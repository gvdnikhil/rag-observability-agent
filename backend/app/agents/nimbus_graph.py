import json
import time
from typing import TypedDict

from langgraph.graph import END, StateGraph

from ..llm.factory import get_provider
from ..services import guardrails
from ..services.rag.store import VectorStore

MAX_STEPS = 4

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "Search the knowledge base for chunks relevant to a query. Always call this before answering a factual question.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers ONLY using information returned by the "
    "search_docs tool. Always call search_docs at least once before answering a factual "
    "question. If the retrieved chunks don't contain the answer, say you don't know instead "
    "of guessing. Write a natural, conversational answer — never mention similarity scores, "
    "source filenames, or the search_docs tool itself; the UI already displays that separately."
)


class AgentState(TypedDict):
    messages: list[dict]
    trace: dict
    steps: int


def build_graph(store: VectorStore):
    provider = get_provider()

    def run_search(query: str) -> list[dict]:
        return store.search(query, k=4)

    def agent_node(state: AgentState) -> AgentState:
        start = time.time()
        response = provider.chat(state["messages"], tools=[SEARCH_TOOL])
        latency_ms = round((time.time() - start) * 1000, 1)
        state["steps"] += 1
        state["trace"]["steps"].append(
            {
                "type": "llm_call",
                "latency_ms": latency_ms,
                "tokens": response.usage,
                "made_tool_call": bool(response.tool_calls),
            }
        )

        if response.tool_calls:
            state["messages"].append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                        }
                        for tc in response.tool_calls
                    ],
                }
            )
            for tc in response.tool_calls:
                query = tc.arguments.get("query", "")
                results = run_search(query) if tc.name == "search_docs" else []
                state["trace"]["retrieved"].extend(results)
                state["trace"]["tool_calls"].append({"name": tc.name, "arguments": tc.arguments})
                state["messages"].append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": json.dumps([{"text": r["text"]} for r in results]),
                    }
                )
        else:
            state["messages"].append({"role": "assistant", "content": response.content})

        return state

    def guardrail_node(state: AgentState) -> AgentState:
        answer = state["messages"][-1]["content"] or ""
        verdict = guardrails.check(state["trace"], answer, domain="nimbus")
        state["trace"]["guardrail"] = verdict
        if verdict["blocked"]:
            state["messages"].append({"role": "assistant", "content": verdict["message"]})
        return state

    def route(state: AgentState) -> str:
        if state["steps"] >= MAX_STEPS:
            return "guardrail"
        if state["messages"][-1]["role"] == "tool":
            return "agent"
        return "guardrail"

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("guardrail", guardrail_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route, {"agent": "agent", "guardrail": "guardrail"})
    graph.add_edge("guardrail", END)
    return graph.compile()

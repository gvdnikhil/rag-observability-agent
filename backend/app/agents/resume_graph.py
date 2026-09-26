import json
import operator
import time
from typing import Annotated, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ..llm.factory import get_provider
from ..services import guardrails, sessions

MAX_STEPS = 4

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_resume",
        "description": "Search the uploaded resume for chunks relevant to a query. Always call this before answering a factual question about the person.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}

SYSTEM_PROMPT = (
    "You are speaking on behalf of the person whose resume was uploaded. Answer ONLY using "
    "information returned by the search_resume tool. Always call search_resume at least once "
    "before answering a factual question about them. Refuse anything not about this person "
    "(general knowledge, other people, small talk unrelated to their background) instead of "
    "guessing. Write a natural, conversational answer — never mention similarity scores, source "
    "filenames, or the search_resume tool itself; the UI already displays that separately."
)


class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    trace: dict
    steps: int


def build_graph():
    provider = get_provider()

    def agent_node(state: AgentState, config: RunnableConfig) -> AgentState:
        session_id = config["configurable"]["thread_id"]
        start = time.time()
        response = provider.chat(
            [{"role": "system", "content": SYSTEM_PROMPT}, *state["messages"]], tools=[SEARCH_TOOL]
        )
        latency_ms = round((time.time() - start) * 1000, 1)

        trace = state["trace"]
        steps = state["steps"] + 1
        trace["steps"].append(
            {
                "type": "llm_call",
                "latency_ms": latency_ms,
                "tokens": response.usage,
                "made_tool_call": bool(response.tool_calls),
            }
        )

        new_messages = []
        if response.tool_calls:
            new_messages.append(
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
                session = sessions.get(session_id)
                results = session.store.search(query, k=4) if (session and session.store and tc.name == "search_resume") else []
                trace["retrieved"].extend(results)
                trace["tool_calls"].append({"name": tc.name, "arguments": tc.arguments})
                new_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": json.dumps([{"text": r["text"]} for r in results]),
                    }
                )
        else:
            new_messages.append({"role": "assistant", "content": response.content})

        return {"messages": new_messages, "trace": trace, "steps": steps}

    def guardrail_node(state: AgentState) -> AgentState:
        answer = state["messages"][-1]["content"] or ""
        verdict = guardrails.check(state["trace"], answer, domain="resume")
        state["trace"]["guardrail"] = verdict
        new_messages = []
        if verdict["blocked"]:
            new_messages.append({"role": "assistant", "content": verdict["message"]})
        return {"messages": new_messages, "trace": state["trace"], "steps": state["steps"]}

    def route(state: AgentState) -> str:
        if state["steps"] >= MAX_STEPS:
            return "guardrail"
        last = state["messages"][-1]
        if last["role"] == "tool":
            return "agent"
        return "guardrail"

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("guardrail", guardrail_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route, {"agent": "agent", "guardrail": "guardrail"})
    graph.add_edge("guardrail", END)
    return graph.compile(checkpointer=MemorySaver())

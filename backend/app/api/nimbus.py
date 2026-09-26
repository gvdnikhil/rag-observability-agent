from fastapi import APIRouter, Request

from ..agents.nimbus_graph import SYSTEM_PROMPT
from ..schemas import ChatRequest
from ..services import observability

router = APIRouter(prefix="/api", tags=["nimbus"])


@router.post("/chat")
def nimbus_chat(req: ChatRequest, request: Request):
    graph = request.app.state.nimbus_graph
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *req.history, {"role": "user", "content": req.message}]
    state = {"messages": messages, "trace": observability.new_trace(), "steps": 0}

    result = graph.invoke(state)

    return {
        "reply": result["messages"][-1]["content"],
        "trace": result["trace"],
        "summary": observability.summarize(result["trace"]),
    }

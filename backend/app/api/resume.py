import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, UploadFile

from ..schemas import PasteTextRequest, ResumeChatRequest
from ..services import observability, sessions
from ..services.rag.ingest import chunk_text
from ..services.rag.store import VectorStore
from ..services.resume_parse import ResumeParseError, extract_text_from_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["resume"])


def _require_session_id(x_session_id: str | None) -> str:
    if not x_session_id:
        raise HTTPException(400, "Missing X-Session-Id header")
    return x_session_id


def reset_resume_thread_memory(resume_graph: Any, session_id: str) -> None:
    """Clears a session's LangGraph conversation memory. Takes the compiled graph
    directly (not a Request) so it's callable from both HTTP handlers and the
    background TTL sweeper in main.py.
    """
    try:
        resume_graph.checkpointer.delete_thread(session_id)
        logger.info("Cleared resume-agent LangGraph memory for session=%s", session_id)
    except AttributeError:
        logger.warning(
            "Checkpointer has no delete_thread(); conversation memory for session=%s left in place until process restart",
            session_id,
        )


def _ingest_resume_text(resume_graph: Any, session_id: str, text: str) -> dict:
    chunks_raw = chunk_text(text)
    chunks = [{"id": f"resume-{i}", "text": c, "source": "resume"} for i, c in enumerate(chunks_raw)]

    store = VectorStore()
    store.build(chunks)

    session = sessions.get_or_create(session_id)
    if session.has_resume:
        logger.info("Replacing existing resume for session=%s", session_id)
        reset_resume_thread_memory(resume_graph, session_id)
    session.store = store

    logger.info("Resume ingested: session=%s chunks=%d chars=%d", session_id, len(chunks), len(text))
    return {"status": "ok", "chunks": len(chunks)}


@router.get("/session")
def resume_session_status(x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    session = sessions.get(session_id)
    if session is None or not session.has_resume:
        return {"has_resume": False, "chunks": 0}
    return {"has_resume": True, "chunks": len(session.store.chunks)}


@router.delete("/session")
def resume_clear_session(request: Request, x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    logger.info("Clearing resume session by user request: %s", session_id)
    resume_graph = request.app.state.resume_graph
    sessions.delete(session_id, on_delete=lambda sid: reset_resume_thread_memory(resume_graph, sid))
    return {"status": "cleared"}


@router.post("/resume/pdf")
async def upload_resume_pdf(request: Request, file: UploadFile, x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    logger.info("Resume PDF upload: session=%s filename=%r content_type=%s", session_id, file.filename, file.content_type)

    data = await file.read()
    try:
        text = extract_text_from_pdf(data)
    except ResumeParseError as e:
        logger.warning("Resume PDF parse failed: session=%s error=%s", session_id, e)
        raise HTTPException(400, str(e)) from None

    return _ingest_resume_text(request.app.state.resume_graph, session_id, text)


@router.post("/resume/text")
async def upload_resume_text(request: Request, body: PasteTextRequest, x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    logger.info("Resume pasted as text: session=%s chars=%d", session_id, len(body.text))

    if not body.text.strip():
        raise HTTPException(400, "Pasted resume text is empty.")

    return _ingest_resume_text(request.app.state.resume_graph, session_id, body.text)


@router.post("/resume/chat")
def resume_chat(req: ResumeChatRequest, request: Request, x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    session = sessions.get(session_id)

    if session is None or not session.has_resume:
        logger.info("Resume chat attempted with no resume uploaded: session=%s", session_id)
        return {
            "reply": "Upload your resume first (PDF or pasted text) — I can only answer questions once I have it.",
            "trace": None,
            "summary": None,
        }

    logger.info("Resume chat message: session=%s chars=%d", session_id, len(req.message))
    state = {
        "messages": [{"role": "user", "content": req.message}],
        "trace": observability.new_trace(),
        "steps": 0,
    }
    graph_config = {"configurable": {"thread_id": session_id}}
    result = request.app.state.resume_graph.invoke(state, config=graph_config)

    reply = result["messages"][-1]["content"]
    trace = result["trace"]
    summary = observability.summarize(trace)
    logger.info(
        "Resume chat reply: session=%s llm_calls=%d latency_ms=%s guardrail_blocked=%s",
        session_id,
        summary["llm_calls"],
        summary["total_latency_ms"],
        trace["guardrail"]["blocked"] if trace["guardrail"] else None,
    )
    return {"reply": reply, "trace": trace, "summary": summary}

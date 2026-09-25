import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from . import observability, sessions  # noqa: E402
from .agent.graph import SYSTEM_PROMPT as NIMBUS_SYSTEM_PROMPT  # noqa: E402
from .agent.graph import build_graph as build_nimbus_graph  # noqa: E402
from .agent.resume_graph import build_graph as build_resume_graph  # noqa: E402
from .rag.ingest import chunk_text, load_docs  # noqa: E402
from .rag.store import VectorStore  # noqa: E402
from .resume_parse import ResumeParseError, extract_text_from_pdf  # noqa: E402

DOCS_DIR = Path(__file__).parent / "data" / "docs"

app = FastAPI(title="Observability-First RAG Assistant")

origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# One shared embedding-model instance underlies both stores (see rag/store.py's
# _MODEL_CACHE) — this boot-time build and every per-session resume upload below
# reuse it instead of each loading their own copy.
nimbus_store = VectorStore()
nimbus_store.build(load_docs(DOCS_DIR))
NIMBUS_GRAPH = build_nimbus_graph(nimbus_store)
RESUME_GRAPH = build_resume_graph()


@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(sessions.sweep_expired_sessions_forever(on_delete=_reset_resume_thread_memory))
    logger.info("Service started (log level=%s)", os.environ.get("LOG_LEVEL", "INFO"))


def _reset_resume_thread_memory(session_id: str) -> None:
    try:
        RESUME_GRAPH.checkpointer.delete_thread(session_id)
        logger.info("Cleared resume-agent LangGraph memory for session=%s", session_id)
    except AttributeError:
        logger.warning(
            "Checkpointer has no delete_thread(); conversation memory for session=%s left in place until process restart",
            session_id,
        )


def _require_session_id(x_session_id: str | None) -> str:
    if not x_session_id:
        raise HTTPException(400, "Missing X-Session-Id header")
    return x_session_id


def _ingest_resume_text(session_id: str, text: str) -> dict:
    chunks_raw = chunk_text(text)
    chunks = [{"id": f"resume-{i}", "text": c, "source": "resume"} for i, c in enumerate(chunks_raw)]

    store = VectorStore()
    store.build(chunks)

    session = sessions.get_or_create(session_id)
    if session.has_resume:
        logger.info("Replacing existing resume for session=%s", session_id)
        _reset_resume_thread_memory(session_id)
    session.store = store

    logger.info("Resume ingested: session=%s chunks=%d chars=%d", session_id, len(chunks), len(text))
    return {"status": "ok", "chunks": len(chunks)}


class PasteTextRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ResumeChatRequest(BaseModel):
    message: str


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "nimbus_chunks_indexed": len(nimbus_store.chunks),
        "resume_active_sessions": len(sessions.SESSIONS),
    }


# ---- Nimbus (fixed sample knowledge base) ----


@app.post("/api/chat")
def nimbus_chat(req: ChatRequest):
    messages = [{"role": "system", "content": NIMBUS_SYSTEM_PROMPT}, *req.history, {"role": "user", "content": req.message}]
    state = {"messages": messages, "trace": observability.new_trace(), "steps": 0}

    result = NIMBUS_GRAPH.invoke(state)

    return {
        "reply": result["messages"][-1]["content"],
        "trace": result["trace"],
        "summary": observability.summarize(result["trace"]),
    }


# ---- Resume Agent (per-session upload, ephemeral) ----


@app.get("/api/session")
def resume_session_status(x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    session = sessions.get(session_id)
    if session is None or not session.has_resume:
        return {"has_resume": False, "chunks": 0}
    return {"has_resume": True, "chunks": len(session.store.chunks)}


@app.delete("/api/session")
def resume_clear_session(x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    logger.info("Clearing resume session by user request: %s", session_id)
    sessions.delete(session_id, on_delete=_reset_resume_thread_memory)
    return {"status": "cleared"}


@app.post("/api/resume/pdf")
async def upload_resume_pdf(file: UploadFile, x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    logger.info("Resume PDF upload: session=%s filename=%r content_type=%s", session_id, file.filename, file.content_type)

    data = await file.read()
    try:
        text = extract_text_from_pdf(data)
    except ResumeParseError as e:
        logger.warning("Resume PDF parse failed: session=%s error=%s", session_id, e)
        raise HTTPException(400, str(e)) from None

    return _ingest_resume_text(session_id, text)


@app.post("/api/resume/text")
async def upload_resume_text(body: PasteTextRequest, x_session_id: str | None = Header(default=None)):
    session_id = _require_session_id(x_session_id)
    logger.info("Resume pasted as text: session=%s chars=%d", session_id, len(body.text))

    if not body.text.strip():
        raise HTTPException(400, "Pasted resume text is empty.")

    return _ingest_resume_text(session_id, body.text)


@app.post("/api/resume/chat")
def resume_chat(req: ResumeChatRequest, x_session_id: str | None = Header(default=None)):
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
    config = {"configurable": {"thread_id": session_id}}
    result = RESUME_GRAPH.invoke(state, config=config)

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

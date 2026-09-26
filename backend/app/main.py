import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .config import app as app_config  # noqa: E402  (after load_dotenv: env vars must be loaded first)

logging.basicConfig(
    level=app_config.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from .agents.nimbus_graph import build_graph as build_nimbus_graph  # noqa: E402
from .agents.resume_graph import build_graph as build_resume_graph  # noqa: E402
from .api import health, nimbus, resume  # noqa: E402
from .services import sessions  # noqa: E402
from .services.rag.ingest import load_docs  # noqa: E402
from .services.rag.store import VectorStore  # noqa: E402

DOCS_DIR = Path(__file__).parent / "data" / "docs"

app = FastAPI(title="Observability-First RAG Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(nimbus.router)
app.include_router(resume.router)

# One shared embedding-model instance underlies both stores (see services/rag/store.py's
# _MODEL_CACHE) — this boot-time build and every per-session resume upload reuse it
# instead of each loading their own copy. Both graphs live on app.state so routers can
# reach them via `request.app.state` without module-level globals.
app.state.nimbus_store = VectorStore()
app.state.nimbus_store.build(load_docs(DOCS_DIR))
app.state.nimbus_graph = build_nimbus_graph(app.state.nimbus_store)
app.state.resume_graph = build_resume_graph()


@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(
        sessions.sweep_expired_sessions_forever(
            on_delete=lambda sid: resume.reset_resume_thread_memory(app.state.resume_graph, sid)
        )
    )
    logger.info("Service started (log level=%s)", app_config.LOG_LEVEL)

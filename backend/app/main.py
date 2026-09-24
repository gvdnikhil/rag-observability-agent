import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import observability
from .agent.graph import SYSTEM_PROMPT, build_graph
from .rag.ingest import load_docs
from .rag.store import VectorStore

load_dotenv()

DOCS_DIR = Path(__file__).parent / "data" / "docs"

app = FastAPI(title="Observability-First RAG Assistant")

origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = VectorStore()
store.build(load_docs(DOCS_DIR))
graph = build_graph(store)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.get("/api/health")
def health():
    return {"status": "ok", "chunks_indexed": len(store.chunks)}


@app.post("/api/chat")
def chat(req: ChatRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *req.history, {"role": "user", "content": req.message}]
    state = {"messages": messages, "trace": observability.new_trace(), "steps": 0}

    result = graph.invoke(state)

    return {
        "reply": result["messages"][-1]["content"],
        "trace": result["trace"],
        "summary": observability.summarize(result["trace"]),
    }

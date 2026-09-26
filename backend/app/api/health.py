from fastapi import APIRouter, Request

from ..services import sessions

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health(request: Request):
    return {
        "status": "ok",
        "nimbus_chunks_indexed": len(request.app.state.nimbus_store.chunks),
        "resume_active_sessions": len(sessions.SESSIONS),
    }

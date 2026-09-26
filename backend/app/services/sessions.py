import asyncio
import logging
import time
from typing import Callable

from ..config import session as session_config
from .rag.store import VectorStore

logger = logging.getLogger(__name__)

TTL_SECONDS = session_config.TTL_SECONDS
SWEEP_INTERVAL_SECONDS = session_config.SWEEP_INTERVAL_SECONDS


class Session:
    def __init__(self):
        self.store: VectorStore | None = None
        self.last_active = time.time()

    @property
    def has_resume(self) -> bool:
        return self.store is not None and len(self.store.chunks) > 0

    def touch(self) -> None:
        self.last_active = time.time()


SESSIONS: dict[str, Session] = {}


def get_or_create(session_id: str) -> Session:
    session = SESSIONS.get(session_id)
    if session is None:
        session = Session()
        SESSIONS[session_id] = session
        logger.info("Session created: %s (active sessions: %d)", session_id, len(SESSIONS))
    session.touch()
    return session


def get(session_id: str) -> Session | None:
    session = SESSIONS.get(session_id)
    if session is not None:
        session.touch()
    return session


def delete(session_id: str, on_delete: Callable[[str], None] | None = None) -> None:
    if SESSIONS.pop(session_id, None) is not None:
        logger.info("Session deleted: %s (active sessions: %d)", session_id, len(SESSIONS))
        if on_delete:
            on_delete(session_id)


async def sweep_expired_sessions_forever(on_delete: Callable[[str], None] | None = None) -> None:
    logger.info("Session sweeper started (ttl=%ds, interval=%ds)", TTL_SECONDS, SWEEP_INTERVAL_SECONDS)
    while True:
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
        now = time.time()
        expired = [sid for sid, s in SESSIONS.items() if now - s.last_active > TTL_SECONDS]
        for sid in expired:
            SESSIONS.pop(sid, None)
            if on_delete:
                on_delete(sid)
        if expired:
            logger.info("Swept %d expired session(s): %s (active sessions: %d)", len(expired), expired, len(SESSIONS))

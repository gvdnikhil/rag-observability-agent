"""Pydantic request/response models, shared across API routers."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ResumeChatRequest(BaseModel):
    message: str


class PasteTextRequest(BaseModel):
    text: str

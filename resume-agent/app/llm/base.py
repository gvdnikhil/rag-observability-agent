from abc import ABC, abstractmethod
from typing import Any


class ToolCall:
    def __init__(self, id: str, name: str, arguments: dict[str, Any]):
        self.id = id
        self.name = name
        self.arguments = arguments


class LLMResponse:
    def __init__(
        self,
        content: str | None,
        tool_calls: list[ToolCall],
        usage: dict[str, int] | None = None,
    ):
        self.content = content
        self.tool_calls = tool_calls
        self.usage = usage or {"prompt_tokens": 0, "completion_tokens": 0}


class LLMProvider(ABC):
    """Common interface every provider (Groq, Gemini, OpenAI, Anthropic, ...) implements.

    Swapping providers is just: implement this interface + register in factory.py.
    """

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        ...

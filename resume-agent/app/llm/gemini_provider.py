import google.generativeai as genai

from .base import LLMProvider, LLMResponse, ToolCall

_ROLE_MAP = {"assistant": "model", "tool": "user", "user": "user"}


def _to_gemini_tools(tools: list[dict]) -> list[dict]:
    return [
        {
            "name": t["function"]["name"],
            "description": t["function"].get("description", ""),
            "parameters": t["function"].get("parameters", {}),
        }
        for t in tools
    ]


def _to_gemini_history(messages: list[dict]) -> tuple[str | None, list[dict]]:
    system_prompt = None
    history = []
    for m in messages:
        if m["role"] == "system":
            system_prompt = m["content"]
            continue
        if m["role"] == "tool":
            history.append(
                {"role": "user", "parts": [f"Tool `{m.get('name')}` result: {m['content']}"]}
            )
            continue
        history.append({"role": _ROLE_MAP[m["role"]], "parts": [m["content"] or ""]})
    return system_prompt, history


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model_name = model

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        system_prompt, history = _to_gemini_history(messages)
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            tools=_to_gemini_tools(tools) if tools else None,
        )
        *past, last = history
        chat = model.start_chat(history=past)
        result = chat.send_message(last["parts"][0])

        content_parts = []
        tool_calls = []
        for part in result.candidates[0].content.parts:
            if getattr(part, "function_call", None):
                fc = part.function_call
                tool_calls.append(
                    ToolCall(id=fc.name, name=fc.name, arguments=dict(fc.args))
                )
            elif getattr(part, "text", None):
                content_parts.append(part.text)

        usage = None
        if getattr(result, "usage_metadata", None):
            usage = {
                "prompt_tokens": result.usage_metadata.prompt_token_count,
                "completion_tokens": result.usage_metadata.candidates_token_count,
            }

        return LLMResponse(
            content="".join(content_parts) or None, tool_calls=tool_calls, usage=usage
        )

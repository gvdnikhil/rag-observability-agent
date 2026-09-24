import os

from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .openai_compatible import OpenAICompatibleProvider

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"

_DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-120b",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}


def get_provider() -> LLMProvider:
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    api_key = os.environ["LLM_API_KEY"]
    model = os.environ.get("LLM_MODEL", _DEFAULT_MODELS.get(provider))

    if provider == "groq":
        return OpenAICompatibleProvider(api_key=api_key, model=model, base_url=_GROQ_BASE_URL)
    if provider == "openai":
        return OpenAICompatibleProvider(api_key=api_key, model=model)
    if provider == "gemini":
        return GeminiProvider(api_key=api_key, model=model)

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected groq, openai, or gemini)")

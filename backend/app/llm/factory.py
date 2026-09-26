from ..config import llm as llm_config
from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .openai_compatible import OpenAICompatibleProvider


def get_provider() -> LLMProvider:
    provider = llm_config.PROVIDER
    if not llm_config.API_KEY:
        raise ValueError("LLM_API_KEY is not set — see backend/.env.example")
    model = llm_config.MODEL or llm_config.DEFAULT_MODELS.get(provider)

    if provider == "groq":
        return OpenAICompatibleProvider(api_key=llm_config.API_KEY, model=model, base_url=llm_config.GROQ_BASE_URL)
    if provider == "openai":
        return OpenAICompatibleProvider(api_key=llm_config.API_KEY, model=model)
    if provider == "gemini":
        return GeminiProvider(api_key=llm_config.API_KEY, model=model)

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected groq, openai, or gemini)")

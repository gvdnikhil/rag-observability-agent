"""LLM provider settings. Swap providers with one env var, no code change."""

import os

# groq (free tier, default) | openai | gemini
PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower()
API_KEY = os.environ.get("LLM_API_KEY", "")
MODEL = os.environ.get("LLM_MODEL")  # falls back to DEFAULT_MODELS[PROVIDER] below if unset

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-120b",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}

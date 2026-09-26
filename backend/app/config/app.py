"""Server-level settings: logging and CORS."""

import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Comma-separated list of allowed frontend origins.
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

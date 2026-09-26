"""Resume agent session lifecycle settings."""

import os

TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(30 * 60)))
SWEEP_INTERVAL_SECONDS = int(os.environ.get("SESSION_SWEEP_INTERVAL_SECONDS", str(5 * 60)))

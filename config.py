import os
from dotenv import load_dotenv

load_dotenv()


def _require(var: str) -> str:
    """Read an env var and raise at startup if it is missing or empty."""
    value = os.getenv(var, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {var}. "
            f"Check your .env file (see .env.example)."
        )
    return value


# --- Required ---
COUNTRIESNOW_BASE_URL: str = _require("COUNTRIESNOW_BASE_URL").rstrip("/")
FRANKFURTER_BASE_URL: str  = _require("FRANKFURTER_BASE_URL").rstrip("/")

# --- Optional (has a sensible default) ---
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "8.0"))

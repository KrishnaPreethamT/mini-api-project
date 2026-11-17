import os
from dataclasses import dataclass
from math import isfinite

from dotenv import load_dotenv

load_dotenv()


def _required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value or not value.strip():
        raise RuntimeError(f"Missing required setting: {name}")
    return value.strip().rstrip("/")


def _request_timeout() -> float:
    value = os.getenv("REQUEST_TIMEOUT", "8")
    try:
        timeout = float(value)
    except ValueError as exc:
        raise RuntimeError("REQUEST_TIMEOUT must be a positive number") from exc
    if not isfinite(timeout) or timeout <= 0:
        raise RuntimeError("REQUEST_TIMEOUT must be a positive number")
    return timeout


@dataclass(frozen=True)
class Settings:
    countriesnow_base_url: str
    frankfurter_base_url: str
    request_timeout: float
    database_url: str
    log_level: str


settings = Settings(
    countriesnow_base_url=_required_setting("COUNTRIESNOW_BASE_URL"),
    frankfurter_base_url=_required_setting("FRANKFURTER_BASE_URL"),
    request_timeout=_request_timeout(),
    database_url=_required_setting("DATABASE_URL"),
    log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
)

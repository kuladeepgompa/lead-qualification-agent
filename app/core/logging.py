"""Structured logging with request-scoped correlation identifiers."""

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from app.core.config import Settings

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Get the current request correlation ID, if a request is active."""

    return _request_id.get()


def set_request_id(request_id: str):  # type: ignore[no-untyped-def]
    """Set the request correlation ID and return its context token."""

    return _request_id.set(request_id)


def reset_request_id(token: Any) -> None:
    """Restore the previous request correlation context."""

    _request_id.reset(token)


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line with safe standard fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for field in ("method", "path", "status_code", "duration_ms", "environment", "app_name"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    """Configure process logging once during application creation."""

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdLogFilter())
    handler.setFormatter(JsonFormatter() if settings.log_format == "json" else logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s"
    ))
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())


class RequestIdLogFilter(logging.Filter):
    """Make request_id available to the optional text formatter."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def get_logger(name: str) -> logging.Logger:
    """Return a named standard-library logger."""

    return logging.getLogger(name)

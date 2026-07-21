"""HTTP middleware for request correlation and access logging."""

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger, reset_request_id, set_request_id

REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign a request ID, measure latency, and emit a single access log event."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = get_logger(__name__)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        supplied_request_id = request.headers.get(REQUEST_ID_HEADER, "").strip()
        request_id = (
            supplied_request_id
            if 0 < len(supplied_request_id) <= MAX_REQUEST_ID_LENGTH
            else str(uuid.uuid4())
        )
        token = set_request_id(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            self.logger.info(
                "http_request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code if "response" in locals() else 500,
                    "duration_ms": duration_ms,
                },
            )
            reset_request_id(token)

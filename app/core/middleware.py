"""HTTP middleware for request correlation, body size protection, and access logging."""

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.errors import error_payload
from app.core.logging import get_logger, get_request_id, reset_request_id, set_request_id

REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128
MAX_BODY_SIZE_BYTES = 1_048_576  # 1 MB


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


class RequestBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject requests with payloads exceeding 1 MB prior to JSON parsing."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        content_length_header = request.headers.get("content-length")
        if content_length_header:
            try:
                if int(content_length_header) > MAX_BODY_SIZE_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content=error_payload(
                            code="REQUEST_TOO_LARGE",
                            message="Request payload exceeds maximum allowed size of 1 MB.",
                            request_id=get_request_id(),
                        ),
                    )
            except ValueError:
                pass

        if request.method in ("POST", "PUT", "PATCH"):
            body_bytes = await request.body()
            if len(body_bytes) > MAX_BODY_SIZE_BYTES:
                return JSONResponse(
                    status_code=413,
                    content=error_payload(
                        code="REQUEST_TOO_LARGE",
                        message="Request payload exceeds maximum allowed size of 1 MB.",
                        request_id=get_request_id(),
                    ),
                )

        return await call_next(request)

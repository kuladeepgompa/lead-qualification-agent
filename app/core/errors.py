"""Safe application errors and FastAPI exception handlers."""

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger, get_request_id


class AppError(Exception):
    """An expected application failure that can be returned safely to clients."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def error_payload(
    *, code: str, message: str, request_id: str, details: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Build the standard public error envelope."""

    error: dict[str, Any] = {"code": code, "message": message, "request_id": request_id}
    if details:
        error["details"] = details
    return {"error": error}


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Serialize known application errors."""

    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            code=exc.code,
            message=exc.message,
            request_id=get_request_id(),
            details=exc.details,
        ),
    )


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return validation failures in the public error envelope."""

    details = [
        {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            request_id=get_request_id(),
            details=details,
        ),
    )


async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Normalize framework-generated HTTP errors to the public error contract."""

    message = exc.detail if isinstance(exc.detail, str) else "Request could not be completed."
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            code="HTTP_ERROR",
            message=message,
            request_id=get_request_id(),
        ),
        headers=exc.headers,
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """Avoid exposing internal errors while retaining an actionable request ID."""

    get_logger(__name__).exception("unhandled_application_error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            request_id=get_request_id(),
        ),
    )

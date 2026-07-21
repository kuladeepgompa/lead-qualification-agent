"""FastAPI application factory and process entry point."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import router as v1_router
from app.core.config import Settings, get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the configured API application."""

    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="AI Lead Qualification Agent",
        version="0.1.0",
        description="REST API foundation for AI-assisted lead qualification.",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(v1_router, prefix="/api/v1")

    get_logger(__name__).info(
        "application_configured",
        extra={"environment": settings.environment, "app_name": settings.app_name},
    )
    return app


app = create_app()

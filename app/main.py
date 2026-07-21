"""FastAPI application factory and process entry point."""

from contextlib import asynccontextmanager

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
from app.core.middleware import RequestBodySizeMiddleware, RequestContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle resources (e.g. closing Redis and LLM provider clients)."""

    yield
    from app.llm.openai import close_openai_clients
    from app.repositories.cache import close_redis_client

    await close_redis_client()
    await close_openai_clients()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the configured API application."""

    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="AI Lead Qualification Agent",
        version="0.1.0",
        description="REST API foundation for AI-assisted lead qualification.",
        lifespan=lifespan,
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.add_middleware(RequestBodySizeMiddleware)
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

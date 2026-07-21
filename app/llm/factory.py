"""Construct configured LLM providers without coupling routes to a vendor SDK."""

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.llm.base import ProviderConfigurationError, StructuredLLMProvider
from app.llm.openai import OpenAIProvider


def get_llm_provider(settings: Settings = Depends(get_settings)) -> StructuredLLMProvider:
    """Return the configured provider or a safe configuration error."""

    try:
        if settings.llm_provider == "openai":
            return OpenAIProvider(settings)
    except ProviderConfigurationError as exc:
        raise AppError(
            status_code=503,
            code="SERVICE_UNAVAILABLE",
            message="The qualification provider is not configured.",
        ) from exc
    raise AppError(
        status_code=503,
        code="SERVICE_UNAVAILABLE",
        message="The configured qualification provider is unavailable.",
    )

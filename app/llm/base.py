"""Provider-neutral contracts and exceptions for structured LLM generation."""

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


class LLMProviderError(Exception):
    """Base exception for expected provider failures."""

    retryable = False


class ProviderTimeoutError(LLMProviderError):
    """The provider did not return within the configured time budget."""

    retryable = True


class ProviderUnavailableError(LLMProviderError):
    """The provider is temporarily unavailable or rejected a transient request."""

    retryable = True


class ProviderConfigurationError(LLMProviderError):
    """The configured provider cannot be initialized safely."""


class InvalidProviderResponseError(LLMProviderError):
    """The provider did not return a usable structured payload."""


@runtime_checkable
class StructuredLLMProvider(Protocol):
    """Interface that future OpenAI, Anthropic, or Gemini adapters must implement."""

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: Mapping[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        """Generate one JSON object that conforms to the supplied schema."""

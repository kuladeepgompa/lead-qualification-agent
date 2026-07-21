"""Orchestration for structured, validated lead qualification."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends
from pydantic import ValidationError

import time

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.llm.base import (
    InvalidProviderResponseError,
    LLMProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StructuredLLMProvider,
)
from app.llm.factory import get_llm_provider
from app.prompts.registry import PromptDefinition, get_lead_qualification_prompt
from app.repositories.usage import UsageRepository
from app.schemas.lead import LeadQualificationRequest
from app.schemas.qualification import (
    LLMQualificationResult,
    LeadPriority,
    LeadQualificationResponse,
    QualificationMetadata,
)
from app.schemas.usage import UsageRecord
from app.utils.privacy import redact_lead_data


class LeadQualificationService:
    """Coordinates prompt rendering, provider calls, validation, and response assembly."""

    def __init__(
        self,
        *,
        provider: StructuredLLMProvider,
        settings: Settings,
        prompt: PromptDefinition | None = None,
        usage_repository: UsageRepository | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._provider = provider
        self._settings = settings
        self._prompt = prompt or get_lead_qualification_prompt()
        self._usage_repository = usage_repository
        self._sleep = sleep
        self._logger = get_logger(__name__)

    async def qualify(
        self, lead: LeadQualificationRequest, *, request_id: str
    ) -> LeadQualificationResponse:
        """Return a strict public qualification response for one validated lead."""

        start_time = time.perf_counter()
        raw_result = await self._generate_with_retries(lead)
        usage_data = raw_result.pop("_usage", None) if isinstance(raw_result, dict) else None
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        try:
            result = LLMQualificationResult.model_validate(raw_result)
        except ValidationError as exc:
            self._logger.warning(
                "llm_response_schema_invalid", extra={"error_count": exc.error_count()}
            )
            raise AppError(
                status_code=502,
                code="INVALID_LLM_RESPONSE",
                message="The qualification provider returned an invalid response.",
            ) from exc

        expected_priority = self._priority_for_score(result.lead_score)
        if result.priority != expected_priority:
            self._logger.info(
                "llm_priority_reconciled",
                extra={"lead_score": result.lead_score, "provider_priority": result.priority.value},
            )
            result = result.model_copy(update={"priority": expected_priority})

        if usage_data and self._usage_repository:
            usage_record = UsageRecord(
                provider=usage_data.get("provider", self._settings.llm_provider),
                model=usage_data.get("model", self._settings.openai_model),
                prompt_tokens=usage_data.get("prompt_tokens"),
                completion_tokens=usage_data.get("completion_tokens"),
                total_tokens=usage_data.get("total_tokens"),
                estimated_cost_usd=usage_data.get("estimated_cost_usd"),
                latency_ms=duration_ms,
                cached=False,
            )
            await self._usage_repository.record_usage(usage_record)

        self._logger.info(
            "lead_qualification_completed",
            extra={
                "request_id": request_id,
                "duration_ms": duration_ms,
                "lead_score": result.lead_score,
                "priority": result.priority.value,
                "prompt_version": self._prompt.version,
                "lead": redact_lead_data(lead.model_dump(mode="json")),
            },
        )

        return LeadQualificationResponse(
            **result.model_dump(),
            metadata=QualificationMetadata(
                request_id=request_id,
                prompt_version=self._prompt.version,
                cached=False,
            ),
        )

    async def _generate_with_retries(self, lead: LeadQualificationRequest) -> dict[str, Any]:
        """Bound transient provider failures with exponential backoff and a total attempt count."""

        schema = LLMQualificationResult.model_json_schema()
        user_prompt = self._prompt.render_user_prompt(lead)
        attempts = self._settings.llm_max_retries + 1
        for attempt in range(attempts):
            try:
                return await asyncio.wait_for(
                    self._provider.generate_structured(
                        system_prompt=self._prompt.system_prompt,
                        user_prompt=user_prompt,
                        json_schema=schema,
                        schema_name="lead_qualification_result",
                    ),
                    timeout=self._settings.llm_timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                provider_error: LLMProviderError = ProviderTimeoutError(
                    "Qualification provider timed out."
                )
                provider_error.__cause__ = exc
            except LLMProviderError as exc:
                provider_error = exc

            is_last_attempt = attempt == attempts - 1
            if not provider_error.retryable or is_last_attempt:
                raise self._translate_provider_error(provider_error) from provider_error

            delay = self._settings.llm_retry_base_delay_seconds * (2**attempt)
            self._logger.warning(
                "llm_request_retrying",
                extra={"attempt": attempt + 1, "max_attempts": attempts, "delay_seconds": delay},
            )
            await self._sleep(delay)

        raise AssertionError("The retry loop must return or raise.")

    def _priority_for_score(self, score: int) -> LeadPriority:
        """Derive the configured priority band from a validated numeric score."""

        if score >= self._settings.hot_lead_min_score:
            return LeadPriority.HOT
        if score >= self._settings.warm_lead_min_score:
            return LeadPriority.WARM
        return LeadPriority.COLD

    @staticmethod
    def _translate_provider_error(error: LLMProviderError) -> AppError:
        """Map provider failures to stable, provider-agnostic public API errors."""

        if isinstance(error, ProviderTimeoutError):
            return AppError(
                status_code=504,
                code="LLM_TIMEOUT",
                message="The qualification provider timed out.",
            )
        if isinstance(error, InvalidProviderResponseError):
            return AppError(
                status_code=502,
                code="INVALID_LLM_RESPONSE",
                message="The qualification provider returned an invalid response.",
            )
        if isinstance(error, ProviderUnavailableError):
            return AppError(
                status_code=502,
                code="LLM_UNAVAILABLE",
                message="The qualification provider is temporarily unavailable.",
            )
        return AppError(
            status_code=502,
            code="LLM_UNAVAILABLE",
            message="The qualification provider is unavailable.",
        )


def get_qualification_service(
    settings: Settings = Depends(get_settings),
    provider: StructuredLLMProvider = Depends(get_llm_provider),
) -> LeadQualificationService:
    """Build the request-scoped qualification service from configured dependencies."""

    return LeadQualificationService(provider=provider, settings=settings)

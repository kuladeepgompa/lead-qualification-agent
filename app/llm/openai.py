"""OpenAI implementation of the structured LLM provider interface."""

import json
from collections.abc import Mapping
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)

from app.core.config import Settings
from app.llm.base import (
    InvalidProviderResponseError,
    ProviderConfigurationError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class OpenAIProvider:
    """Generate strict JSON-schema output through OpenAI Chat Completions."""

    def __init__(self, settings: Settings, client: AsyncOpenAI | None = None) -> None:
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
        if not api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is not configured.")
        self._model = settings.openai_model
        self._client = client or AsyncOpenAI(
            api_key=api_key,
            timeout=settings.llm_timeout_seconds,
            max_retries=0,
        )

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: Mapping[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        """Call OpenAI with native strict JSON Schema output enabled."""

        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": dict(json_schema),
                    },
                },
                temperature=0,
            )
        except (APITimeoutError, TimeoutError) as exc:
            raise ProviderTimeoutError("OpenAI request timed out.") from exc
        except (RateLimitError, InternalServerError, APIConnectionError) as exc:
            raise ProviderUnavailableError("OpenAI is temporarily unavailable.") from exc
        except APIStatusError as exc:
            raise ProviderUnavailableError("OpenAI request failed.") from exc

        if not completion.choices or not completion.choices[0].message.content:
            raise InvalidProviderResponseError("OpenAI returned an empty completion.")
        try:
            payload = json.loads(completion.choices[0].message.content)
        except json.JSONDecodeError as exc:
            raise InvalidProviderResponseError("OpenAI did not return valid JSON.") from exc
        if not isinstance(payload, dict):
            raise InvalidProviderResponseError("OpenAI returned a non-object JSON response.")
        return payload

"""Cache interface, in-memory, and Redis implementations for normalized lead responses."""

import json
from typing import Any, Protocol

from app.core.logging import get_logger
from app.schemas.qualification import LeadQualificationResponse


class QualificationCache(Protocol):
    """Interface for lead qualification caching."""

    async def get(self, cache_key: str) -> LeadQualificationResponse | None:
        """Retrieve a cached qualification response by key."""

        ...

    async def set(
        self, cache_key: str, response: LeadQualificationResponse, ttl_seconds: int = 3600
    ) -> None:
        """Store a qualification response by key."""

        ...


class InMemoryCache:
    """In-memory implementation of the qualification cache."""

    def __init__(self) -> None:
        self._store: dict[str, LeadQualificationResponse] = {}

    async def get(self, cache_key: str) -> LeadQualificationResponse | None:
        """Retrieve a cached response if present."""

        return self._store.get(cache_key)

    async def set(
        self, cache_key: str, response: LeadQualificationResponse, ttl_seconds: int = 3600
    ) -> None:
        """Store a response in memory."""

        self._store[cache_key] = response

    def clear(self) -> None:
        """Clear all stored cache entries."""

        self._store.clear()


class RedisCache:
    """Redis-backed implementation of the qualification cache protocol."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self._logger = get_logger(__name__)

    async def get(self, cache_key: str) -> LeadQualificationResponse | None:
        """Retrieve and deserialize a cached LeadQualificationResponse."""

        try:
            raw_data = await self._client.get(f"lead_qual:{cache_key}")
            if not raw_data:
                return None
            data = raw_data.decode("utf-8") if isinstance(raw_data, bytes) else raw_data
            payload = json.loads(data)
            return LeadQualificationResponse.model_validate(payload)
        except Exception as exc:
            self._logger.warning("redis_cache_get_failed", extra={"error": str(exc)})
            return None

    async def set(
        self, cache_key: str, response: LeadQualificationResponse, ttl_seconds: int = 3600
    ) -> None:
        """Serialize and store a LeadQualificationResponse with TTL."""

        try:
            payload = json.dumps(response.model_dump(mode="json"))
            await self._client.set(f"lead_qual:{cache_key}", payload, ex=ttl_seconds)
        except Exception as exc:
            self._logger.warning("redis_cache_set_failed", extra={"error": str(exc)})


def create_redis_client(redis_url: str) -> Any:
    """Factory helper to construct an async Redis client instance."""

    import redis.asyncio as redis

    return redis.from_url(redis_url, socket_timeout=2.0)

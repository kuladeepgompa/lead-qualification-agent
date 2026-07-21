"""Cache interface and in-memory implementation for normalized lead responses."""

from typing import Protocol

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

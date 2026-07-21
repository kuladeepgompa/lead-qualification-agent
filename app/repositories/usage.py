"""Usage telemetry repository interface and in-memory implementation."""

from typing import Protocol

from app.schemas.usage import UsageRecord


class UsageRepository(Protocol):
    """Interface for persisting or emitting usage and cost telemetry records."""

    async def record_usage(self, record: UsageRecord) -> None:
        """Record one validated usage telemetry entry."""

        ...


class InMemoryUsageRepository:
    """Thread-safe in-memory repository for recording LLM usage and cost metrics."""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    async def record_usage(self, record: UsageRecord) -> None:
        """Store a usage record in memory."""

        self._records.append(record)

    def get_records(self) -> list[UsageRecord]:
        """Return all recorded usage records."""

        return list(self._records)

    def clear(self) -> None:
        """Clear all stored records."""

        self._records.clear()

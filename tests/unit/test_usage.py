"""Unit tests for token cost estimation and usage repository telemetry."""

import pytest

from app.llm.usage import calculate_estimated_cost
from app.repositories.usage import InMemoryUsageRepository
from app.schemas.usage import UsageRecord


def test_calculate_estimated_cost_known_models() -> None:
    # gpt-4o-mini: $0.15/1M input, $0.60/1M output
    # 1000 prompt tokens = $0.00015, 1000 completion tokens = $0.00060 -> $0.00075
    cost = calculate_estimated_cost("gpt-4o-mini", 1000, 1000)
    assert cost == 0.00075

    # None tokens return None
    assert calculate_estimated_cost("gpt-4o-mini", None, None) is None


def test_calculate_estimated_cost_fallback_model() -> None:
    cost = calculate_estimated_cost("unknown-model", 1000, 1000)
    assert cost is not None
    assert cost > 0


@pytest.mark.asyncio
async def test_in_memory_usage_repository_stores_records() -> None:
    repo = InMemoryUsageRepository()
    record = UsageRecord(
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=500,
        completion_tokens=200,
        total_tokens=700,
        estimated_cost_usd=0.000195,
        latency_ms=150.5,
        cached=False,
    )

    await repo.record_usage(record)
    stored = repo.get_records()

    assert len(stored) == 1
    assert stored[0].model == "gpt-4o-mini"
    assert stored[0].total_tokens == 700
    assert stored[0].estimated_cost_usd == 0.000195

    repo.clear()
    assert len(repo.get_records()) == 0

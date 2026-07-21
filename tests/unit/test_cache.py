"""Unit tests for InMemoryCache and RedisCache implementations."""

from unittest.mock import AsyncMock

import pytest

from app.repositories.cache import InMemoryCache, RedisCache
from app.schemas.qualification import (
    BuyingIntent,
    CompanySize,
    LeadPriority,
    LeadQualificationResponse,
    QualificationMetadata,
)


def sample_response() -> LeadQualificationResponse:
    return LeadQualificationResponse(
        lead_score=85,
        priority=LeadPriority.HOT,
        buying_intent=BuyingIntent.HIGH,
        intent="CRM Integration",
        company_size=CompanySize.ENTERPRISE,
        estimated_deal_size={"currency": "USD", "min": 20000, "max": 50000, "basis": "Enterprise"},
        pain_points=["Manual routing"],
        recommended_next_action="Schedule call",
        sales_summary="Qualified lead",
        confidence_score=0.9,
        metadata=QualificationMetadata(request_id="req-1", prompt_version="v1"),
    )


@pytest.mark.asyncio
async def test_in_memory_cache_get_set_clear() -> None:
    cache = InMemoryCache()
    res = sample_response()

    assert await cache.get("key1") is None

    await cache.set("key1", res)
    cached = await cache.get("key1")

    assert cached is not None
    assert cached.lead_score == 85

    cache.clear()
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_redis_cache_get_set_success() -> None:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = sample_response().model_dump_json()

    cache = RedisCache(mock_redis)
    res = sample_response()

    await cache.set("key1", res, ttl_seconds=3600)
    mock_redis.set.assert_called_once()

    cached = await cache.get("key1")
    assert cached is not None
    assert cached.lead_score == 85


@pytest.mark.asyncio
async def test_redis_cache_gracefully_handles_connection_failures() -> None:
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = Exception("Connection refused")
    mock_redis.set.side_effect = Exception("Connection refused")

    cache = RedisCache(mock_redis)
    res = sample_response()

    # Neither set nor get should raise an exception
    await cache.set("key1", res)
    cached = await cache.get("key1")

    assert cached is None

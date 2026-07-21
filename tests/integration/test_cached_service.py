"""Integration test for LeadQualificationService caching behavior."""

import pytest

from app.core.config import Settings
from app.repositories.cache import InMemoryCache
from app.schemas.lead import LeadQualificationRequest
from app.services.qualification_service import LeadQualificationService
from tests.test_qualification_service import FakeProvider, valid_provider_result


@pytest.mark.asyncio
async def test_qualification_service_uses_cache_on_subsequent_requests() -> None:
    provider = FakeProvider([valid_provider_result(lead_score=80)])
    cache = InMemoryCache()
    settings = Settings(environment="test", cache_enabled=True)

    service = LeadQualificationService(provider=provider, settings=settings, cache=cache)

    lead = LeadQualificationRequest(company="Acme Corp", email="aisha@example.com")

    # First request: cache miss, provider invoked
    res1 = await service.qualify(lead, request_id="req-1")
    assert res1.lead_score == 80
    assert res1.metadata.cached is False
    assert len(provider.calls) == 1

    # Second request: cache hit, provider not invoked again
    res2 = await service.qualify(lead, request_id="req-2")
    assert res2.lead_score == 80
    assert res2.metadata.cached is True
    assert res2.metadata.request_id == "req-2"
    assert len(provider.calls) == 1

"""Integration tests for the /api/v1/lead/qualify endpoint and usage telemetry."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories.usage import InMemoryUsageRepository
from app.services.qualification_service import LeadQualificationService, get_qualification_service
from tests.test_qualification_service import FakeProvider, valid_provider_result


def create_test_client(
    provider_outcomes: list[dict[str, Any] | Exception] | None = None,
    usage_repo: InMemoryUsageRepository | None = None,
) -> TestClient:
    settings = Settings(environment="test")
    app = create_app(settings)

    outcomes = provider_outcomes or [valid_provider_result()]
    provider = FakeProvider(outcomes)
    service = LeadQualificationService(
        provider=provider, settings=settings, usage_repository=usage_repo
    )

    app.dependency_overrides[get_qualification_service] = lambda: service
    return TestClient(app)


def test_qualify_lead_full_payload_success() -> None:
    client = create_test_client()
    payload = {
        "name": "Aisha Sharma",
        "email": "aisha@example.com",
        "phone": "+919876543210",
        "company": "Acme Solutions",
        "designation": "VP of Engineering",
        "industry": "Software",
        "employees": 250,
        "country": "India",
        "source": "Inbound Demo",
        "message": "We need an automated lead qualification tool for our CRM.",
    }

    response = client.post("/api/v1/lead/qualify", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["lead_score"] == 82
    assert body["priority"] == "HOT"
    assert body["buying_intent"] == "HIGH"
    assert body["company_size"] == "MID_MARKET"
    assert body["estimated_deal_size"]["currency"] == "USD"
    assert body["estimated_deal_size"]["min"] == 15000
    assert body["estimated_deal_size"]["max"] == 40000
    assert len(body["pain_points"]) == 2
    assert body["metadata"]["prompt_version"] == "lead_qualification_v1"
    assert response.headers["X-Request-ID"] == body["metadata"]["request_id"]


@pytest.mark.parametrize(
    "minimal_payload",
    [
        {"company": "Acme Corp"},
        {"email": "contact@acme.com"},
        {"phone": "+14155552671"},
        {"message": "I want to schedule a product demo."},
    ],
)
def test_qualify_lead_minimal_context_success(minimal_payload: dict[str, str]) -> None:
    client = create_test_client()

    response = client.post("/api/v1/lead/qualify", json=minimal_payload)

    assert response.status_code == 200
    assert response.json()["lead_score"] == 82


def test_qualify_lead_validation_error_returns_standard_envelope() -> None:
    client = create_test_client()

    # Empty payload violates minimum lead context rule
    response = client.post("/api/v1/lead/qualify", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed."
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]
    assert len(body["error"]["details"]) > 0


def test_qualify_lead_invalid_email_returns_field_details() -> None:
    client = create_test_client()

    response = client.post(
        "/api/v1/lead/qualify", json={"company": "Acme", "email": "not-an-email"}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert any("email" in str(d["location"]) for d in body["error"]["details"])


def test_qualify_lead_preserves_custom_request_id() -> None:
    client = create_test_client()
    custom_id = "test-correlation-id-999"

    response = client.post(
        "/api/v1/lead/qualify", json={"company": "Acme"}, headers={"X-Request-ID": custom_id}
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
    assert response.json()["metadata"]["request_id"] == custom_id


@pytest.mark.asyncio
async def test_qualify_lead_records_usage_telemetry_when_usage_present() -> None:
    usage_repo = InMemoryUsageRepository()
    payload_with_usage = valid_provider_result()
    payload_with_usage["_usage"] = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "prompt_tokens": 350,
        "completion_tokens": 150,
        "total_tokens": 500,
        "estimated_cost_usd": 0.0001425,
    }

    client = create_test_client(provider_outcomes=[payload_with_usage], usage_repo=usage_repo)

    response = client.post("/api/v1/lead/qualify", json={"company": "Acme"})

    assert response.status_code == 200
    records = usage_repo.get_records()
    assert len(records) == 1
    assert records[0].provider == "openai"
    assert records[0].model == "gpt-4o-mini"
    assert records[0].total_tokens == 500
    assert records[0].estimated_cost_usd == 0.0001425
    assert records[0].latency_ms > 0

"""Phase 2 contract and validation tests."""

import pytest
from pydantic import ValidationError

from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.lead import LeadQualificationRequest
from app.schemas.qualification import (
    BuyingIntent,
    CompanySize,
    EstimatedDealSize,
    LeadPriority,
    LeadQualificationResponse,
    QualificationMetadata,
)
from app.schemas.usage import UsageRecord


def test_lead_request_normalizes_text_email_and_phone() -> None:
    lead = LeadQualificationRequest(
        name="  Aisha Sharma  ",
        email="AISHA@EXAMPLE.COM",
        phone=" +91 (987) 654-3210 ",
        company="  Acme Retail  ",
        message="   ",
    )

    assert lead.name == "Aisha Sharma"
    assert str(lead.email) == "aisha@example.com"
    assert lead.phone == "+919876543210"
    assert lead.company == "Acme Retail"
    assert lead.message is None


@pytest.mark.parametrize("payload", [{}, {"name": "Only a name"}, {"message": "   "}])
def test_lead_request_requires_meaningful_context(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="At least one of email, phone, company, or message"):
        LeadQualificationRequest(**payload)


def test_lead_request_rejects_unknown_fields_and_invalid_phone() -> None:
    with pytest.raises(ValidationError):
        LeadQualificationRequest(company="Acme", unsupported="value")
    with pytest.raises(ValidationError, match="Phone must contain"):
        LeadQualificationRequest(company="Acme", phone="123")


def test_estimated_deal_size_requires_complete_ordered_currency_qualified_range() -> None:
    estimate = EstimatedDealSize(currency="usd", min=10_000, max=20_000, basis="Company size.")
    assert estimate.currency == "USD"

    with pytest.raises(ValidationError, match="Currency is required"):
        EstimatedDealSize(min=10_000, max=20_000, basis="Company size.")
    with pytest.raises(ValidationError, match="must not exceed"):
        EstimatedDealSize(currency="USD", min=20_000, max=10_000, basis="Company size.")


def test_success_response_is_strict_and_bounded() -> None:
    response = LeadQualificationResponse(
        lead_score=82,
        priority=LeadPriority.HOT,
        buying_intent=BuyingIntent.HIGH,
        intent="Improve inbound lead routing.",
        company_size=CompanySize.MID_MARKET,
        estimated_deal_size={
            "currency": "USD",
            "min": 15_000,
            "max": 40_000,
            "basis": "Company size.",
        },
        pain_points=["Slow response time", "Manual routing"],
        recommended_next_action="Schedule a discovery call within one business day.",
        sales_summary="VP-level buyer with a clear operational need.",
        confidence_score=0.84,
        metadata=QualificationMetadata(request_id="request-123", prompt_version="v1"),
    )

    assert response.priority is LeadPriority.HOT
    assert response.metadata.cached is False
    with pytest.raises(ValidationError):
        LeadQualificationResponse(**response.model_dump(), unsupported="value")


def test_error_response_has_typed_details() -> None:
    response = ErrorResponse(
        error={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "request_id": "request-123",
            "details": [
                ErrorDetail(location=["body", "email"], message="Invalid email", type="value_error")
            ],
        }
    )

    assert response.error.details is not None
    assert response.error.details[0].location == ["body", "email"]


def test_usage_record_validates_non_negative_telemetry() -> None:
    usage = UsageRecord(provider="provider", model="model", prompt_tokens=10, latency_ms=25.5)

    assert usage.cached is False
    with pytest.raises(ValidationError):
        UsageRecord(provider="provider", model="model", total_tokens=-1)

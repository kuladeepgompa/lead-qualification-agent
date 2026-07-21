"""Unit tests for lead normalization and cache key generation."""

from app.schemas.lead import LeadInput
from app.utils.normalization import (
    compute_lead_cache_key,
    normalize_email,
    normalize_phone,
    normalize_text,
)


def test_normalize_helpers() -> None:
    assert normalize_text("   Acme Corp  ") == "Acme Corp"
    assert normalize_text("   ") is None
    assert normalize_text(123) is None

    assert normalize_email("  USER@EXAMPLE.COM ") == "user@example.com"
    assert normalize_email(None) is None

    assert normalize_phone(" +1 (555) 123-4567 ") == "+15551234567"
    assert normalize_phone(None) is None


def test_compute_lead_cache_key_is_deterministic() -> None:
    lead1 = LeadInput(company="Acme Corp", email="aisha@example.com")
    lead2 = LeadInput(email="aisha@example.com", company="Acme Corp")

    key1 = compute_lead_cache_key(lead1)
    key2 = compute_lead_cache_key(lead2)

    assert key1 == key2
    assert len(key1) == 64

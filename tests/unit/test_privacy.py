"""Unit tests for PII redaction and masking utilities."""

from app.utils.privacy import (
    hash_identifier,
    mask_email,
    mask_phone,
    redact_lead_data,
    redact_text,
)


def test_mask_email_conceals_local_part_and_preserves_domain() -> None:
    assert mask_email("aisha.sharma@example.com") == "a**********a@example.com"
    assert mask_email("ab@acme.org") == "a*@acme.org"
    assert mask_email("a@acme.org") == "*@acme.org"
    assert mask_email(None) == ""
    assert mask_email("invalid-email") == "***"


def test_mask_phone_conceals_middle_digits() -> None:
    assert mask_phone("+919876543210") == "+9*********10"
    assert mask_phone("1234567890") == "1*******90"
    assert mask_phone("123") == "***"
    assert mask_phone(None) == ""


def test_redact_text_truncates_long_free_text() -> None:
    short_msg = "Hello World"
    long_msg = (
        "This is a very long message containing sensitive lead details and project instructions."
    )

    assert redact_text(short_msg, max_length=20) == "Hello World"
    assert redact_text(long_msg, max_length=20) == "This is a very long ...[87 chars]"
    assert redact_text(None) == ""


def test_hash_identifier_produces_deterministic_snippet() -> None:
    hash1 = hash_identifier("aisha.sharma@example.com")
    hash2 = hash_identifier("aisha.sharma@example.com")
    hash3 = hash_identifier("other@example.com")

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 16


def test_redact_lead_data_masks_sensitive_dict_fields() -> None:
    raw_lead = {
        "name": "Aisha Sharma",
        "email": "aisha@example.com",
        "phone": "+919876543210",
        "company": "Acme Corp",
        "message": "We need help improving our lead qualification pipeline immediately.",
    }

    redacted = redact_lead_data(raw_lead)

    assert redacted["company"] == "Acme Corp"
    assert redacted["email"] == "a***a@example.com"
    assert redacted["phone"] == "+9*********10"
    assert "Aisha" in redacted["name"]
    assert "...[" in redacted["message"]

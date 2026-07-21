"""Privacy and PII redaction utilities for safe logging and telemetry."""

import hashlib
from typing import Any


def mask_email(email: str | None) -> str:
    """Mask email address to conceal identity in logs while preserving domain structure."""

    if not email:
        return ""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) == 1:
        masked_local = "*"
    elif len(local) == 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str | None) -> str:
    """Mask phone number keeping only leading prefix and last 2 digits."""

    if not phone:
        return ""
    if len(phone) <= 4:
        return "*" * len(phone)
    prefix = phone[:2] if phone.startswith("+") else phone[:1]
    suffix = phone[-2:]
    masked_middle = "*" * (len(phone) - len(prefix) - len(suffix))
    return f"{prefix}{masked_middle}{suffix}"


def redact_text(text: str | None, max_length: int = 30) -> str:
    """Return a safe summary indicator of free-text fields without logging full PII."""

    if not text:
        return ""
    length = len(text)
    snippet = text[:max_length].replace("\n", " ")
    return f"{snippet}...[{length} chars]" if length > max_length else snippet


def hash_identifier(value: str) -> str:
    """Return a deterministic SHA-256 hash snippet of a sensitive string for correlation."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def redact_lead_data(lead_data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a lead data dictionary with sensitive PII fields masked/redacted."""

    redacted = dict(lead_data)
    if "email" in redacted and redacted["email"]:
        redacted["email"] = mask_email(str(redacted["email"]))
    if "phone" in redacted and redacted["phone"]:
        redacted["phone"] = mask_phone(str(redacted["phone"]))
    if "name" in redacted and redacted["name"]:
        redacted["name"] = redact_text(str(redacted["name"]), max_length=15)
    if "message" in redacted and redacted["message"]:
        redacted["message"] = redact_text(str(redacted["message"]), max_length=20)
    return redacted

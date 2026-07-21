"""Lead normalization and cache-key generation utilities."""

import hashlib
import json
from typing import Any

from app.schemas.lead import LeadInput


def normalize_text(value: Any) -> str | None:
    """Trim leading/trailing whitespace and return None for whitespace-only or non-string values."""

    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def normalize_email(email: str | None) -> str | None:
    """Normalize email to lowercase string."""

    if email:
        return email.strip().lower()
    return None


def normalize_phone(phone: str | None) -> str | None:
    """Remove formatting characters from phone number while retaining leading plus."""

    if not phone:
        return None
    cleaned = "".join(
        character for character in phone.strip() if character.isdigit() or character == "+"
    )
    return cleaned or None


def compute_lead_cache_key(lead: LeadInput) -> str:
    """Calculate a stable SHA-256 hash key from normalized lead fields for caching."""

    data = lead.model_dump(mode="json")
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

"""Validated, normalized input models for incoming leads."""

import re
from typing import Any

from pydantic import ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.shared import StrictSchema

_PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,30}$")


class LeadInput(StrictSchema):
    """Normalized lead data that is safe to pass to later application layers."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = Field(default=None, min_length=1, max_length=160)
    designation: str | None = Field(default=None, min_length=1, max_length=120)
    industry: str | None = Field(default=None, min_length=1, max_length=100)
    employees: int | None = Field(default=None, ge=0, le=10_000_000)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    source: str | None = Field(default=None, min_length=1, max_length=100)
    message: str | None = Field(default=None, min_length=1, max_length=4_000)

    @field_validator(
        "name", "company", "designation", "industry", "country", "source", "message", mode="before"
    )
    @classmethod
    def normalize_optional_text(cls, value: Any) -> Any:
        """Trim text and represent whitespace-only optional values as missing."""

        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        """Normalize an email for consistent comparison without changing its identity."""

        return str(value).lower() if value is not None else None

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: Any) -> Any:
        """Remove common display separators while preserving an optional leading plus."""

        if not isinstance(value, str):
            return value
        normalized = "".join(
            character for character in value.strip() if character.isdigit() or character == "+"
        )
        return normalized or None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Require a compact international or local phone representation."""

        if value is not None and not _PHONE_PATTERN.fullmatch(value):
            raise ValueError("Phone must contain 7 to 30 digits with an optional leading '+'.")
        return value


class LeadQualificationRequest(LeadInput):
    """Public request contract for a lead qualification submission."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_meaningful_lead_context(self) -> "LeadQualificationRequest":
        """Reject requests that contain no usable lead identifier or context."""

        if not any((self.email, self.phone, self.company, self.message)):
            raise ValueError("At least one of email, phone, company, or message must be provided.")
        return self

"""Strict schemas for LLM qualification output and public API responses."""

from enum import Enum

from pydantic import Field, field_validator, model_validator

from app.schemas.shared import StrictSchema


class LeadPriority(str, Enum):
    """Sales urgency classification."""

    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"


class BuyingIntent(str, Enum):
    """Estimated strength of active buying interest."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class CompanySize(str, Enum):
    """Normalized company-size bands."""

    SOLO = "SOLO"
    SMB = "SMB"
    MID_MARKET = "MID_MARKET"
    ENTERPRISE = "ENTERPRISE"
    UNKNOWN = "UNKNOWN"


class EstimatedDealSize(StrictSchema):
    """Bounded deal-size estimate with explicit uncertainty support."""

    currency: str | None = Field(default=None, min_length=3, max_length=3)
    min: float | None = Field(default=None, ge=0)
    max: float | None = Field(default=None, ge=0)
    basis: str = Field(min_length=1, max_length=500)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        """Normalize currency codes before enforcing their ISO-like format."""

        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        """Accept only three uppercase alphabetic characters as a currency code."""

        if value is not None and (not value.isalpha() or value != value.upper()):
            raise ValueError("Currency must be a three-letter uppercase alphabetic code.")
        return value

    @model_validator(mode="after")
    def validate_estimate_consistency(self) -> "EstimatedDealSize":
        """Ensure numerical estimates are complete, ordered, and currency-qualified."""

        has_minimum = self.min is not None
        has_maximum = self.max is not None
        if has_minimum != has_maximum:
            raise ValueError(
                "Estimated deal size min and max must both be provided or both be null."
            )
        if has_minimum:
            if self.currency is None:
                raise ValueError(
                    "Currency is required when estimated deal size values are provided."
                )
            if self.min is not None and self.max is not None and self.min > self.max:
                raise ValueError("Estimated deal size min must not exceed max.")
        elif self.currency is not None:
            raise ValueError("Currency must be null when estimated deal size is unknown.")
        return self


class QualificationAnalysis(StrictSchema):
    """The validated substance of a lead qualification result."""

    lead_score: int = Field(ge=0, le=100)
    priority: LeadPriority
    buying_intent: BuyingIntent
    intent: str = Field(min_length=1, max_length=1_000)
    company_size: CompanySize
    estimated_deal_size: EstimatedDealSize
    pain_points: list[str] = Field(default_factory=list, max_length=5)
    recommended_next_action: str = Field(min_length=1, max_length=500)
    sales_summary: str = Field(min_length=1, max_length=1_500)
    confidence_score: float = Field(ge=0, le=1)

    @field_validator("intent", "recommended_next_action", "sales_summary", mode="before")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        """Trim generated text so whitespace-only output cannot satisfy the contract."""

        return value.strip() if isinstance(value, str) else value

    @field_validator("pain_points")
    @classmethod
    def validate_pain_points(cls, values: list[str]) -> list[str]:
        """Keep each pain point concise, non-empty, and safely bounded."""

        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Pain points must not contain empty values.")
        if any(len(value) > 300 for value in normalized):
            raise ValueError("Each pain point must be 300 characters or fewer.")
        return normalized


class LLMQualificationResult(QualificationAnalysis):
    """Strict provider result before public response metadata is attached."""


class QualificationMetadata(StrictSchema):
    """Safe execution metadata exposed alongside a successful qualification."""

    request_id: str = Field(min_length=1, max_length=128)
    prompt_version: str = Field(min_length=1, max_length=100)
    cached: bool = False
    model: str | None = Field(default=None, min_length=1, max_length=120)


class LeadQualificationResponse(QualificationAnalysis):
    """Public success response for the qualification endpoint."""

    metadata: QualificationMetadata

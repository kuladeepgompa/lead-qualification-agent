"""Internal schema for future LLM usage and cost telemetry."""

from pydantic import Field

from app.schemas.shared import StrictSchema


class UsageRecord(StrictSchema):
    """Validated, provider-neutral usage data; persistence is intentionally deferred."""

    provider: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=120)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)
    cached: bool = False

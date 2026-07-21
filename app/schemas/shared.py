"""Common Pydantic model configuration for strict public schemas."""

from pydantic import BaseModel, ConfigDict


class StrictSchema(BaseModel):
    """Base schema that rejects undeclared fields and validates assigned values."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

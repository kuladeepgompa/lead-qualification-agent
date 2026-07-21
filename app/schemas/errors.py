"""Pydantic schemas for the API's stable public error envelope."""

from typing import Any

from pydantic import Field

from app.schemas.shared import StrictSchema


class ErrorDetail(StrictSchema):
    """Safe, field-level explanation for a request validation failure."""

    location: list[str | int] = Field(min_length=1)
    message: str = Field(min_length=1, max_length=500)
    type: str = Field(min_length=1, max_length=120)


class ErrorBody(StrictSchema):
    """The error object returned within every public error response."""

    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=500)
    request_id: str = Field(min_length=1, max_length=128)
    details: list[ErrorDetail] | None = None


class ErrorResponse(StrictSchema):
    """Top-level public error response."""

    error: ErrorBody

"""Validation and rule schemas."""

from __future__ import annotations

from pydantic import Field

from modelops_core.schemas.common import BaseObject


class ValidationRule(BaseObject):
    """Checks expected correctness."""

    rule_type: str | None = Field(default=None)
    attribute: str | None = Field(default=None)


class BusinessRule(BaseObject):
    """Business rule."""

    attribute: str | None = Field(default=None)


class DataQualityCheck(BaseObject):
    """Data quality check."""

    attribute: str | None = Field(default=None)

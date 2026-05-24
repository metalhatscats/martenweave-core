"""Issue and Risk schemas."""

from __future__ import annotations

from pydantic import Field

from modelops_core.schemas.common import BaseObject


class Issue(BaseObject):
    """Captures a gap or problem."""

    issue_type: str | None = Field(default=None)
    severity: str | None = Field(default=None)
    source_dataset_id: str | None = Field(default=None)
    source_column: str | None = Field(default=None)
    source_gap_code: str | None = Field(default=None)
    affected_objects: list[str] | None = Field(default=None)
    recommended_action: str | None = Field(default=None)
    related_objects: list[str] | None = Field(default=None)


class Risk(BaseObject):
    """Captures a risk."""

    risk_category: str | None = Field(default=None)
    severity: str | None = Field(default=None)
    attribute: str | None = Field(default=None)

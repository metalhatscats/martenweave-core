"""ChangeRequest schema."""

from __future__ import annotations

from pydantic import Field

from modelops_core.schemas.common import BaseObject


class ChangeRequest(BaseObject):
    """Captures an approved model change."""

    source_patch_proposals: list[str] | None = Field(default=None)
    affected_objects: list[str] | None = Field(default=None)
    related_issues: list[str] | None = Field(default=None)
    related_decisions: list[str] | None = Field(default=None)
    requested_by: str | None = Field(default=None)
    approval_status: str | None = Field(default=None)
    implementation_status: str | None = Field(default=None)
    summary: str | None = Field(default=None)

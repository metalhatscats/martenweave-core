"""PatchProposal and PatchOperation schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from modelops_core.schemas.common import BaseObject


class CreatedBy(StrEnum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class PatchValidationStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class PatchOperation(BaseModel):
    """A single operation within a PatchProposal."""

    op: str = Field(..., description="Operation type.")
    object_id: str | None = Field(default=None)
    object_type: str | None = Field(default=None)
    target_path: str | None = Field(default=None)
    before: Any = Field(default=None)
    after: Any = Field(default=None)
    reason: str | None = Field(default=None)


class PatchProposal(BaseObject):
    """Proposed model change before approval."""

    created_by: str | None = Field(default=None)
    created_at: str | None = Field(default=None)
    source_evidence: str | None = Field(default=None)
    affected_objects: list[str] | None = Field(default=None)
    operations: list[PatchOperation] | None = Field(default=None)
    validation_status: str | None = Field(default=None)
    validation_results: list[dict[str, Any]] | None = Field(default=None)
    application_status: str | None = Field(default=None)
    applied_at: str | None = Field(default=None)
    applied_by: str | None = Field(default=None)
    applied_changed_files: list[str] | None = Field(default=None)
    applied_audit_event_id: str | None = Field(default=None)
    expires_at: str | None = Field(
        default=None, description="ISO 8601 timestamp when the proposal expires."
    )

"""Patch operation dataclasses and enums."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


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

    op: str = Field(...)
    object_id: str | None = Field(default=None)
    object_type: str | None = Field(default=None)
    target_path: str | None = Field(default=None)
    before: Any = Field(default=None)
    after: Any = Field(default=None)
    reason: str | None = Field(default=None)


_ALLOWED_OPERATIONS: frozenset[str] = frozenset(
    {
        "add_object",
        "update_object",
        "create_object",
        "add_relationship",
        "add_evidence_link",
        "create_issue",
    }
)

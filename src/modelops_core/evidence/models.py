from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceFindingKind(StrEnum):
    MISSING_OWNER = "missing_owner"
    MISSING_MAPPING = "missing_mapping"
    VALIDATION_ISSUE = "validation_issue"
    DECISION_NOTE = "decision_note"
    FIELD_QUESTION = "field_question"
    RENAME_SUGGESTION = "rename_suggestion"


class EvidenceFinding(BaseModel):
    kind: EvidenceFindingKind
    object_id: str | None = Field(default=None)
    field: str | None = Field(default=None)
    message: str
    severity: str | None = Field(default=None)
    source_line: int | None = Field(default=None)

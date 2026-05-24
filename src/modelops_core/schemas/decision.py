"""Decision schema."""

from __future__ import annotations

from pydantic import Field

from modelops_core.schemas.common import BaseObject


class Decision(BaseObject):
    """Captures rationale for a model choice."""

    decision_category: str | None = Field(default=None)
    attribute: str | None = Field(default=None)
    evidence: str | None = Field(default=None)
    related_decisions: list[str] | None = Field(default=None)

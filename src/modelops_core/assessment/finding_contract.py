"""Stable, typed contract for assessment findings and their provenance."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FindingProvenance(BaseModel):
    """Evidence location and deterministic assessment context for a finding."""

    model_config = ConfigDict(extra="forbid")

    assessment_run_id: str
    source_kind: Literal["mapping_profile", "dataset_readiness", "model_validation"]
    location: dict[str, Any] = Field(default_factory=dict)


class AssessmentFinding(BaseModel):
    """A reviewable readiness finding; evidence does not mutate canonical truth."""

    model_config = ConfigDict(extra="forbid")

    id: str
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    message: str
    lifecycle_state: Literal[
        "open", "confirmed", "false_positive", "accepted_risk", "deferred", "resolved"
    ] = "open"
    provenance: FindingProvenance

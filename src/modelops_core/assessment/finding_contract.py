"""Stable, typed contract for assessment findings and their provenance."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DetectionMode = Literal["deterministic", "inferred", "heuristic", "ai_generated"]
ReadinessImpact = Literal["blocking", "ready_with_warnings", "informational"]
SourceKind = Literal[
    "mapping_profile",
    "dataset_readiness",
    "model_validation",
    "risk_analysis",
    "ai_suggestion",
]
FindingStatus = Literal[
    "open", "confirmed", "false_positive", "accepted_risk", "deferred", "resolved"
]
Severity = Literal["low", "medium", "high", "critical"]


class FindingProvenance(BaseModel):
    """Evidence location and deterministic assessment context for a finding."""

    model_config = ConfigDict(extra="forbid")

    assessment_run_id: str
    source_kind: SourceKind
    detection_mode: DetectionMode
    location: dict[str, Any] = Field(default_factory=dict)
    rule_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    affected_objects: list[str] = Field(default_factory=list)
    input_fingerprint: str | None = None


class AssessmentFinding(BaseModel):
    """A reviewable readiness finding; evidence does not mutate canonical truth."""

    model_config = ConfigDict(extra="forbid")

    id: str
    category: str
    severity: Severity
    message: str
    status: FindingStatus = "open"
    lifecycle_state: FindingStatus = "open"
    provenance: FindingProvenance
    rule_id: str | None = None
    affected_objects: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    recommended_action: str | None = None
    readiness_impact: ReadinessImpact | None = None
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence is meaningful only for inferred, heuristic, or ai_generated findings."
        ),
    )

    @model_validator(mode="after")
    def _confidence_only_for_non_deterministic(self) -> AssessmentFinding:
        if self.confidence is not None and self.provenance.detection_mode == "deterministic":
            raise ValueError("Deterministic findings must not carry a confidence score.")
        return self

    @field_validator("status", "lifecycle_state", mode="before")
    @classmethod
    def _coerce_status(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value

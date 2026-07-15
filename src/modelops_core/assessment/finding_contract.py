"""Typed finding provenance and readiness contract.

Defines a stable schema shared by assessment, gaps, API, reports, and UI so that
every finding can explain what it is, how it was detected, what evidence supports
it, and whether it blocks readiness.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FindingDetectionMode(StrEnum):
    """How a finding was produced.

    ``deterministic`` findings come from explicit validation rules and are
    reproducible for the same inputs. ``inferred`` findings are derived by
    combining deterministic signals. ``heuristic`` findings use pattern-based
    classification. ``ai_generated`` findings may be produced by an AI adapter
    but are never presented as deterministic facts.
    """

    DETERMINISTIC = "deterministic"
    INFERRED = "inferred"
    HEURISTIC = "heuristic"
    AI_GENERATED = "ai_generated"


class FindingStatus(StrEnum):
    """Lifecycle status of a finding."""

    OPEN = "open"
    REVIEWED = "reviewed"
    PROMOTED = "promoted"
    RESOLVED = "resolved"


class FindingSeverity(StrEnum):
    """Severity levels for findings."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReadinessImpact(StrEnum):
    """Effect of a finding on migration readiness."""

    BLOCKING = "blocking"
    AT_RISK = "at_risk"
    INFORMATIONAL = "informational"


class FindingEvidence(BaseModel):
    """Reference to evidence that supports a finding."""

    source_type: str = Field(
        default="",
        description="Kind of evidence source, e.g. mapping_workbook, dataset, canonical_object.",
    )
    source_id: str = Field(
        default="",
        description="Stable identity of the evidence source, e.g. a file hash or object ID.",
    )
    location: dict[str, Any] = Field(
        default_factory=dict,
        description="Human- and machine-readable location within the source (sheet, row, field).",
    )
    fingerprint: str = Field(
        default="",
        description="Content fingerprint of the evidence at detection time.",
    )


class FindingProvenance(BaseModel):
    """Provenance describing how a finding was detected."""

    detection_mode: FindingDetectionMode = Field(
        default=FindingDetectionMode.DETERMINISTIC,
        description="How the finding was produced.",
    )
    rule_id: str = Field(
        default="",
        description="Identifier of the rule, check, or code path that produced the finding.",
    )
    rule_version: str = Field(
        default="",
        description="Version of the rule or rule set, when available.",
    )
    source_module: str = Field(
        default="",
        description="Python module or service that produced the finding.",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence only when meaningful; never used for deterministic rules.",
    )


class AffectedObject(BaseModel):
    """Canonical object or source artifact affected by a finding."""

    object_id: str = Field(default="", description="ID of the affected object or artifact.")
    object_type: str = Field(default="", description="Type of the affected object, if known.")
    role: str = Field(
        default="",
        description="Role in the finding, e.g. source, target, owner, related.",
    )


class ReadinessFinding(BaseModel):
    """A single finding in the assessment readiness contract.

    This model is shared by assessment, gaps, API, reports, and UI. It separates
    detection provenance from human disposition so that reviewers can see what
    produced a finding before deciding what to do with it.
    """

    id: str = Field(..., description="Stable finding identifier.")
    type: str = Field(default="readiness_finding", description="Finding type discriminator.")
    category: str = Field(default="", description="Finding category, e.g. missing_owner.")
    severity: FindingSeverity = Field(default=FindingSeverity.MEDIUM)
    status: FindingStatus = Field(default=FindingStatus.OPEN)
    source: str = Field(
        default="",
        description=(
            "High-level source family, e.g. mapping_profile, dataset_gap, model_validation."
        ),
    )
    message: str = Field(default="", description="Human-readable description.")
    recommended_action: str = Field(
        default="",
        description="Suggested next step for the reviewer.",
    )
    readiness_impact: ReadinessImpact = Field(
        default=ReadinessImpact.INFORMATIONAL,
        description="Whether the finding blocks readiness, introduces risk, or is informational.",
    )
    location: dict[str, Any] = Field(
        default_factory=dict,
        description="Machine-readable location of the finding in its source.",
    )
    affected_objects: list[AffectedObject] = Field(default_factory=list)
    evidence_refs: list[FindingEvidence] = Field(default_factory=list)
    provenance: FindingProvenance = Field(default_factory=FindingProvenance)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict using Pydantic serialization."""
        return self.model_dump(mode="json", exclude_none=True)


# Human disposition is separate from detection provenance and is recorded in
# ``finding-reviews.json`` by ``modelops_core.pilot.review``.

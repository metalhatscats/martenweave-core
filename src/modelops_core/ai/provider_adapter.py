"""Provider-agnostic AI adapter protocol and no-provider scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_validator import validate_patch_proposal


@dataclass
class AIContextBundle:
    """Privacy-scrubbed context passed to AI providers."""

    note: str
    dataset_columns: list[str] = field(default_factory=list)
    dataset_row_count: int | None = None
    affected_object_ids: list[str] = field(default_factory=list)
    domain: str | None = None
    include_raw_samples: bool = False
    max_context_length: int = 4000
    repository_context: dict[str, Any] | None = None

    def scrub(self) -> AIContextBundle:
        """Return a copy with raw samples removed."""
        return AIContextBundle(
            note=self.note,
            dataset_columns=self.dataset_columns,
            dataset_row_count=self.dataset_row_count,
            affected_object_ids=self.affected_object_ids,
            domain=self.domain,
            include_raw_samples=False,
            max_context_length=self.max_context_length,
            repository_context=self.repository_context,
        )


@dataclass
class AICandidateOutput:
    """Structured output from an AI provider before PatchProposal creation."""

    proposal_id: str
    title: str
    operations: list[dict[str, Any]] = field(default_factory=list)
    affected_objects: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    human_checks: list[str] = field(default_factory=list)
    source_evidence: str | None = None


class AIProviderError(Exception):
    """Base AI provider error."""


class AIOutputValidationError(AIProviderError):
    """AI output failed structured validation."""


class AITimeoutError(AIProviderError):
    """AI provider timed out."""


class AIRateLimitError(AIProviderError):
    """AI provider rate limited."""


class AIProviderAdapter(Protocol):
    """Protocol for AI provider adapters."""

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        """Generate candidate patch proposals from context."""
        ...


class NoProviderAdapter:
    """Deterministic scaffold adapter used when no AI provider is configured."""

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        note = context.note.upper()
        operations: list[dict[str, Any]] = []
        affected_objects: list[str] = []
        assumptions: list[str] = [
            "No AI provider is configured. This is a deterministic scaffold proposal."
        ]
        human_checks: list[str] = ["Verify the proposed objects and fields match your intent."]

        if "CUSTOMER GROUP" in note or "KNVV-KDGRP" in note:
            affected_objects = ["ATTR-CUST-SALES-CUSTOMER-GROUP", "FEP-S4-KNVV-KDGRP"]
            operations.append(
                {
                    "op": "update_object",
                    "object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
                    "object_type": "Attribute",
                    "target_path": "description",
                    "after": "Updated description from note.",
                    "reason": "Note indicates a change to Customer Group semantics.",
                }
            )

        proposal_id = "PP-SCAFFOLD-001"
        return [
            AICandidateOutput(
                proposal_id=proposal_id,
                title="Scaffold Patch Proposal from Note",
                operations=operations,
                affected_objects=affected_objects,
                assumptions=assumptions,
                human_checks=human_checks,
                source_evidence=context.note[:500],
            )
        ]


class ProviderOutputValidator:
    """Validates candidate outputs from AI providers."""

    def __init__(self) -> None:
        pass

    def validate(self, candidate: AICandidateOutput) -> dict[str, Any]:
        """Validate a candidate and return a structured result."""
        if not candidate.proposal_id:
            raise AIOutputValidationError("Candidate is missing proposal_id.")
        if not candidate.title:
            raise AIOutputValidationError("Candidate is missing title.")
        if not candidate.operations:
            raise AIOutputValidationError("Candidate has no operations.")

        for op in candidate.operations:
            if op.get("op") not in {
                "add_object",
                "update_object",
                "create_object",
                "add_relationship",
                "add_evidence_link",
                "create_issue",
            }:
                raise AIOutputValidationError(f"Disallowed operation: {op.get('op')}")

        return {"valid": True, "candidate": candidate}

    def to_patch_proposal(self, candidate: AICandidateOutput) -> dict[str, Any]:
        """Convert a validated candidate into a PatchProposal dict."""
        from modelops_core.patching.patch_proposal_service import build_patch_proposal

        operations = [PatchOperation(**op) for op in candidate.operations]
        proposal = build_patch_proposal(
            proposal_id=candidate.proposal_id,
            operations=operations,
            affected_objects=candidate.affected_objects,
            source_evidence=candidate.source_evidence,
            created_by="ai",
        )

        validation_results = validate_patch_proposal(proposal)
        proposal["validation_status"] = (
            "valid" if not any(v.severity == "ERROR" for v in validation_results) else "invalid"
        )
        proposal["validation_results"] = [v.model_dump() for v in validation_results]

        return {
            "is_safe": proposal["validation_status"] == "valid",
            "proposal": proposal,
            "validation": validation_results,
            "markdown": "",
            "assumptions": candidate.assumptions,
            "human_checks": candidate.human_checks,
        }

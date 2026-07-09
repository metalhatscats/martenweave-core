"""Reviewer summary for PatchProposals.

Builds a compact, deterministic summary that tells a human reviewer what to
check before approving or applying a proposal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.approval.risk_service import compute_proposal_risk
from modelops_core.impact.proposal_impact_service import generate_proposal_impact_report
from modelops_core.patching.patch_validator import validate_patch_proposal
from modelops_core.repository import parse_file, scan_repository


@dataclass
class ReviewerSummary:
    """Deterministic reviewer summary for a single PatchProposal."""

    proposal_id: str
    status: str
    validation_status: str | None
    operations_count: int
    operations_by_type: dict[str, int]
    affected_object_ids: list[str]
    files_touched: list[str]
    risk_level: str
    requires_approval: bool
    risk_reasons: list[str]
    validation_errors: list[str]
    validation_warnings: list[str]
    recommended_action: str
    review_notes: list[str] = field(default_factory=list)


def _build_object_registry(model_path: Path) -> dict[str, dict[str, Any]]:
    """Build object_id -> frontmatter registry."""
    registry: dict[str, dict[str, Any]] = {}
    if not model_path.exists():
        return registry
    for file_path in scan_repository(model_path):
        parsed = parse_file(file_path)
        if parsed.frontmatter and parsed.frontmatter.get("id"):
            registry[parsed.frontmatter["id"]] = parsed.frontmatter
    return registry


def _predict_files_touched(
    operations: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    model_path: Path,
) -> list[str]:
    """Predict canonical files that would be created, updated, or deleted."""
    files: set[str] = set()
    for op in operations:
        obj_id = op.get("object_id")
        obj_type = op.get("object_type")
        op_name = op.get("op", "")
        if not obj_id:
            continue

        existing = registry.get(obj_id)
        if existing and existing.get("source_file"):
            files.add(str(existing["source_file"]))
        elif obj_type:
            # Predict canonical path for new objects.
            predicted = model_path / f"{obj_type.lower()}s" / f"{obj_id}.md"
            files.add(str(predicted))
        if op_name == "create_issue":
            predicted = model_path / "issues" / f"{obj_id}.md"
            files.add(str(predicted))
    return sorted(files)


def _count_operations_by_type(operations: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for op in operations:
        name = op.get("op", "unknown")
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def generate_reviewer_summary(
    proposal: dict[str, Any],
    repo_model_path: Path,
    db_path: Path | None = None,
) -> ReviewerSummary:
    """Generate a reviewer summary for a PatchProposal dict.

    Args:
        proposal: PatchProposal frontmatter dict.
        repo_model_path: Path to the repository ``model/`` directory.
        db_path: Optional path to the SQLite index for impact analysis.

    Returns:
        A ``ReviewerSummary`` dataclass.
    """
    proposal_id = str(proposal.get("id", "unknown"))
    status = str(proposal.get("status", "pending_review"))
    validation_status = proposal.get("validation_status")
    operations = proposal.get("operations") or []

    registry = _build_object_registry(repo_model_path)
    files_touched = _predict_files_touched(operations, registry, repo_model_path)
    operations_by_type = _count_operations_by_type(operations)

    affected_ids: set[str] = set()
    for op in operations:
        obj_id = op.get("object_id")
        affected = op.get("affected_objects") or []
        if obj_id:
            affected_ids.add(obj_id)
        if isinstance(affected, list):
            affected_ids.update(str(a) for a in affected)

    # Impact-aware risk assessment
    impact_report = None
    if db_path and db_path.exists():
        try:
            impact_report = generate_proposal_impact_report(
                db_path, proposal_id, operations, max_depth=2
            )
        except Exception:
            impact_report = None

    risk = compute_proposal_risk(operations, repo_model_path, impact_report=impact_report)

    # Validation
    validation_results = validate_patch_proposal(proposal, repo_model_path=repo_model_path)
    errors = [f"{v.code}: {v.message}" for v in validation_results if v.severity == "ERROR"]
    warnings = [f"{v.code}: {v.message}" for v in validation_results if v.severity == "WARNING"]

    # Recommended action
    if errors:
        recommended_action = "reject"
    elif risk.risk_level == "high":
        recommended_action = "inspect"
    elif risk.requires_approval:
        recommended_action = "approve_with_review"
    else:
        recommended_action = "approve"

    review_notes: list[str] = []
    if errors:
        review_notes.append("Proposal has validation errors and should not be approved.")
    if warnings:
        review_notes.append(f"Proposal has {len(warnings)} validation warning(s).")
    if risk.risk_level == "high":
        review_notes.append(
            "High-risk proposal: verify each affected object and rationale before approval."
        )
    elif risk.risk_level == "medium":
        review_notes.append("Medium-risk proposal: review risk reasons before approval.")
    if "active_object_modified" in risk.triggering_rules:
        review_notes.append("Active objects are modified; confirm no production impact.")
    if "governance_field_changed" in risk.triggering_rules:
        review_notes.append("Governance/owner fields change; ensure stewards are notified.")

    return ReviewerSummary(
        proposal_id=proposal_id,
        status=status,
        validation_status=validation_status,
        operations_count=len(operations),
        operations_by_type=operations_by_type,
        affected_object_ids=sorted(affected_ids),
        files_touched=files_touched,
        risk_level=risk.risk_level,
        requires_approval=risk.requires_approval,
        risk_reasons=risk.risk_reasons,
        validation_errors=errors,
        validation_warnings=warnings,
        recommended_action=recommended_action,
        review_notes=review_notes,
    )


def reviewer_summary_to_dict(summary: ReviewerSummary) -> dict[str, Any]:
    """Convert a ReviewerSummary to a JSON-serializable dict."""
    return {
        "proposal_id": summary.proposal_id,
        "status": summary.status,
        "validation_status": summary.validation_status,
        "operations_count": summary.operations_count,
        "operations_by_type": summary.operations_by_type,
        "affected_object_ids": summary.affected_object_ids,
        "files_touched": summary.files_touched,
        "risk_level": summary.risk_level,
        "requires_approval": summary.requires_approval,
        "risk_reasons": summary.risk_reasons,
        "validation_errors": summary.validation_errors,
        "validation_warnings": summary.validation_warnings,
        "recommended_action": summary.recommended_action,
        "review_notes": summary.review_notes,
    }

"""Human disposition workflow for migration-assessment findings.

Assessment findings are produced by ``migration_assessment.generate_migration_assessment``
as ``findings.json`` next to the run manifest. This module lets a human reviewer
record dispositions, summarize the review state, and promote confirmed findings to
PatchProposal objects for approval.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.config import resolve_model_path
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    write_patch_proposal,
)

_ALLOWED_DISPOSITIONS: frozenset[str] = frozenset(
    {"confirmed", "false_positive", "accepted_risk", "deferred", "resolved"}
)

_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$")


def _assessment_dir_from_manifest(manifest_path: Path) -> Path:
    """Return the directory containing the manifest."""
    return manifest_path.resolve().parent


def load_findings(assessment_dir: Path) -> dict[str, Any]:
    """Load ``findings.json`` from an assessment output directory."""
    findings_path = assessment_dir / "findings.json"
    if not findings_path.exists():
        raise FileNotFoundError(f"Findings file not found: {findings_path}")
    return json.loads(findings_path.read_text(encoding="utf-8"))


def load_reviews(assessment_dir: Path) -> dict[str, Any]:
    """Load or initialize ``finding-reviews.json``.

    Returns a dict with ``reviews`` and ``history`` keys.
    """
    reviews_path = assessment_dir / "finding-reviews.json"
    if reviews_path.exists():
        return json.loads(reviews_path.read_text(encoding="utf-8"))
    return {"reviews": {}, "history": []}


def _write_reviews(assessment_dir: Path, reviews: dict[str, Any]) -> Path:
    """Persist ``finding-reviews.json``."""
    reviews_path = assessment_dir / "finding-reviews.json"
    reviews_path.write_text(
        json.dumps(reviews, indent=2, default=str, sort_keys=True),
        encoding="utf-8",
    )
    return reviews_path


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finding_by_id(findings: dict[str, Any], finding_id: str) -> dict[str, Any] | None:
    for finding in findings.get("findings", []):
        if finding.get("id") == finding_id:
            return finding
    return None


def set_review(
    assessment_dir: Path,
    finding_id: str,
    disposition: str,
    reviewer: str,
    note: str | None = None,
    reviewed_at: str | None = None,
) -> dict[str, Any]:
    """Record a human disposition for a single finding.

    Args:
        assessment_dir: Directory containing ``findings.json``.
        finding_id: Stable finding ID from ``findings.json``.
        disposition: One of ``confirmed``, ``false_positive``, ``accepted_risk``,
            ``deferred``, ``resolved``.
        reviewer: Identity of the reviewer.
        note: Optional free-form note.
        reviewed_at: Optional ISO timestamp for the review. Defaults to now.

    Returns:
        The updated review record for the finding.

    Raises:
        ValueError: If the disposition is not allowed or the finding is unknown.
    """
    if disposition not in _ALLOWED_DISPOSITIONS:
        allowed = ", ".join(sorted(_ALLOWED_DISPOSITIONS))
        raise ValueError(f"Invalid disposition '{disposition}'. Allowed: {allowed}")

    findings = load_findings(assessment_dir)
    finding = _finding_by_id(findings, finding_id)
    if finding is None:
        raise ValueError(f"Finding '{finding_id}' not found in findings.json")

    reviews = load_reviews(assessment_dir)
    record: dict[str, Any] = {
        "finding_id": finding_id,
        "disposition": disposition,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at or _now_iso(),
        "note": note or "",
        "severity": finding.get("severity", "medium"),
        "category": finding.get("category", "unknown"),
    }
    reviews["reviews"][finding_id] = record
    reviews["history"].append(record)
    _write_reviews(assessment_dir, reviews)
    return record


def summarize_reviews(assessment_dir: Path) -> dict[str, Any]:
    """Return a summary of current review state.

    Includes counts by disposition, severity, and category, plus a list of
    unreviewed finding IDs.
    """
    findings = load_findings(assessment_dir)
    reviews = load_reviews(assessment_dir)

    by_disposition: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    reviewed_ids: set[str] = set()

    for finding_id, record in reviews.get("reviews", {}).items():
        reviewed_ids.add(finding_id)
        disposition = record.get("disposition", "unknown")
        severity = record.get("severity", "medium")
        category = record.get("category", "unknown")
        by_disposition[disposition] = by_disposition.get(disposition, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1

    all_ids = {f.get("id") for f in findings.get("findings", []) if f.get("id")}
    unreviewed = sorted(all_ids - reviewed_ids)

    return {
        "total_findings": len(findings.get("findings", [])),
        "reviewed_count": len(reviewed_ids),
        "unreviewed_count": len(unreviewed),
        "unreviewed": unreviewed,
        "by_disposition": by_disposition,
        "by_severity": by_severity,
        "by_category": by_category,
    }


def _finding_to_proposal_id(finding_id: str) -> str:
    """Convert a finding ID into a valid canonical object ID.

    Finding IDs use ``:`` as a separator and may start with a lowercase category.
    Proposal IDs must match ``^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$``.
    """
    parts = finding_id.split(":")
    cleaned = [re.sub(r"[^A-Z0-9]+", "-", part.upper()).strip("-") for part in parts]
    cleaned = [p for p in cleaned if p]
    proposal_id = "AR-" + "-".join(cleaned)
    # Remove repeated separators and trailing/leading separators.
    proposal_id = re.sub(r"-+", "-", proposal_id).strip("-")
    if not _ID_PATTERN.match(proposal_id):
        raise ValueError(f"Cannot derive valid proposal ID from finding '{finding_id}'")
    return proposal_id


def promote_finding(
    assessment_dir: Path,
    repo_root: Path,
    finding_id: str,
    created_by: str = "assessment-review",
) -> Path:
    """Promote a confirmed finding to a PatchProposal in the model repository.

    Args:
        assessment_dir: Directory containing ``findings.json`` and reviews.
        repo_root: Path to the model repository.
        finding_id: Stable finding ID to promote.
        created_by: Actor recorded on the proposal.

    Returns:
        Path to the written PatchProposal file.

    Raises:
        ValueError: If the finding has not been reviewed as ``confirmed``.
    """
    findings = load_findings(assessment_dir)
    finding = _finding_by_id(findings, finding_id)
    if finding is None:
        raise ValueError(f"Finding '{finding_id}' not found in findings.json")

    reviews = load_reviews(assessment_dir)
    review = reviews.get("reviews", {}).get(finding_id)
    if review is None or review.get("disposition") != "confirmed":
        raise ValueError(
            f"Finding '{finding_id}' must be reviewed as 'confirmed' before promotion."
        )

    proposal_id = _finding_to_proposal_id(finding_id)
    op = PatchOperation(
        op="create_issue",
        object_id=proposal_id,
        object_type="Issue",
        reason=finding.get("message", ""),
        after={
            "id": proposal_id,
            "type": "Issue",
            "status": "open",
            "name": finding.get("message", proposal_id),
            "issue_type": "assessment_finding",
            "severity": finding.get("severity", "medium"),
            "category": finding.get("category", "unknown"),
            "source_finding_id": finding_id,
            "source": finding.get("source", "mapping_profile"),
            "location": finding.get("location", {}),
            "disposition": "confirmed",
            "reviewer": review.get("reviewer", ""),
            "reviewed_at": review.get("reviewed_at", ""),
            "note": review.get("note", ""),
        },
    )

    proposal = build_patch_proposal(
        proposal_id=proposal_id,
        operations=[op],
        affected_objects=[proposal_id],
        source_evidence=finding.get("message", ""),
        created_by=created_by,
        generated_by="assessment-review",
    )

    model_path = resolve_model_path(repo_root)
    return write_patch_proposal(proposal, model_path)

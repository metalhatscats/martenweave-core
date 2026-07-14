"""PatchProposal build, render, write, and transition services."""

from __future__ import annotations

import re
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from modelops_core.patching.patch_model import PatchOperation
from modelops_core.schemas.common import SourceState

_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$")


def build_patch_proposal(
    proposal_id: str,
    operations: list[PatchOperation],
    affected_objects: list[str] | None = None,
    source_evidence: str | None = None,
    created_by: str = "system",
    generated_by: str | None = None,
) -> dict[str, Any]:
    """Build an in-memory PatchProposal dict."""
    proposal: dict[str, Any] = {
        "id": proposal_id,
        "type": "PatchProposal",
        "status": "pending_review",
        "name": proposal_id,
        "title": f"Patch Proposal: {proposal_id}",
        "created_by": created_by,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_evidence": source_evidence,
        "source_state": SourceState.PROPOSAL.value,
        "affected_objects": affected_objects or [],
        "operations": [op.model_dump() for op in operations],
        "validation_status": "pending",
        "validation_results": [],
    }
    if generated_by:
        proposal["generated_by"] = generated_by
    return proposal


def render_patch_proposal_markdown(proposal: dict[str, Any]) -> str:
    """Render a PatchProposal dict as canonical Markdown with YAML frontmatter."""
    frontmatter = dict(proposal)
    # Remove body-like fields from frontmatter if they exist
    yaml_text = yaml.safe_dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    lines = ["---", yaml_text.rstrip(), "---", ""]
    lines.append(f"# Patch Proposal: {proposal.get('id', '')}")
    lines.append("")
    if proposal.get("source_evidence"):
        lines.append("## Source Evidence")
        lines.append(proposal["source_evidence"])
        lines.append("")
    return "\n".join(lines) + "\n"


def write_patch_proposal(proposal: dict[str, Any], repo_model_path: Path) -> Path:
    """Write a PatchProposal to ``model/patch-proposals/{id}.md``."""
    proposals_dir = repo_model_path / "patch-proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    path = proposals_dir / f"{proposal['id']}.md"
    path.write_text(render_patch_proposal_markdown(proposal), encoding="utf-8")
    return path


def transition_patch_proposal_status(
    proposal_path: Path,
    new_status: str,
    reviewer: str | None = None,
    reviewer_notes: str | None = None,
    rejection_reason: str | None = None,
) -> str | None:
    """Transition a PatchProposal's status in its canonical file.

    Args:
        proposal_path: Path to the PatchProposal canonical file.
        new_status: Target status (e.g. 'accepted', 'rejected').
        reviewer: Identity of the reviewer.
        reviewer_notes: Free-form notes from the reviewer.
        rejection_reason: Reason for rejection (when new_status is 'rejected').

    Returns:
        A warning message if audit emission failed, otherwise None.
    """
    from modelops_core.repository import parse_file

    parsed = parse_file(proposal_path)
    if parsed.frontmatter is None:
        raise ValueError("PatchProposal file has no frontmatter")

    if not reviewer:
        raise ValueError("reviewer is required to transition proposal status")

    frontmatter = dict(parsed.frontmatter)
    old_status = frontmatter.get("status", "unknown")
    frontmatter["status"] = new_status
    frontmatter["reviewer"] = reviewer
    frontmatter["reviewed_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if reviewer_notes:
        frontmatter["reviewer_notes"] = reviewer_notes
    if rejection_reason:
        frontmatter["rejection_reason"] = rejection_reason

    yaml_text = yaml.safe_dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    lines = ["---", yaml_text.rstrip(), "---"]
    if parsed.body:
        lines.append("")
        lines.append(parsed.body.strip())
    proposal_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Emit audit event for the transition
    warning: str | None = None
    try:
        repo_root = proposal_path.parent.parent.parent
        from modelops_core.reports.audit_service import (
            AuditEventService,
            create_audit_event,
        )

        service = AuditEventService(repo_root)
        event = create_audit_event(
            event_type="proposal_status_changed",
            actor=reviewer or "system",
            status="success",
            proposal_id=frontmatter.get("id"),
            metadata={
                "old_status": old_status,
                "new_status": new_status,
                "reason": rejection_reason or reviewer_notes or "",
            },
        )
        service.emit(event)
    except Exception as exc:
        warning = (
            f"PatchProposal status changed to {new_status}, but audit event emission failed: {exc}"
        )
        warnings.warn(warning, stacklevel=2)

    return warning

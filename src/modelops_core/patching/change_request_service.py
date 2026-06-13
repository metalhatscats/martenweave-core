"""ChangeRequest build, write, approve, and reject services.

.. deprecated::
    This module is deprecated. Use ``modelops_core.change_request.service`` instead.
"""

from __future__ import annotations

import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from modelops_core.patching.apply_service import apply_patch_proposal
from modelops_core.patching.change_request_validator import validate_change_request
from modelops_core.repository import parse_file

warnings.warn(
    "modelops_core.patching.change_request_service is deprecated and will be removed. "
    "Use modelops_core.change_request.service instead.",
    DeprecationWarning,
    stacklevel=2,
)


def build_change_request_from_patch_proposal(
    proposal: dict[str, Any], requested_by: str = "system"
) -> dict[str, Any]:
    """Build a ChangeRequest from an accepted PatchProposal."""
    if proposal.get("status") != "accepted":
        raise ValueError("PatchProposal must be accepted before creating a ChangeRequest.")

    proposal_id = proposal.get("id")
    cr_id = f"CR-{proposal_id}"

    return {
        "id": cr_id,
        "type": "ChangeRequest",
        "status": "pending",
        "name": cr_id,
        "title": f"Change Request: {cr_id}",
        "source_patch_proposals": [proposal_id],
        "affected_objects": proposal.get("affected_objects", []),
        "related_issues": [],
        "related_decisions": [],
        "requested_by": requested_by,
        "approval_status": "pending",
        "implementation_status": "pending",
        "summary": f"Implements patch proposal {proposal_id}.",
    }


def render_change_request_markdown(change_request: dict[str, Any]) -> str:
    yaml_text = yaml.safe_dump(
        change_request, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    lines = ["---", yaml_text.rstrip(), "---", ""]
    lines.append(f"# Change Request: {change_request.get('id', '')}")
    lines.append("")
    if change_request.get("summary"):
        lines.append(change_request["summary"])
        lines.append("")
    return "\n".join(lines) + "\n"


def write_change_request(change_request: dict[str, Any], repo_model_path: Path) -> Path:
    changes_dir = repo_model_path / "change-requests"
    changes_dir.mkdir(parents=True, exist_ok=True)
    path = changes_dir / f"{change_request['id']}.md"
    path.write_text(render_change_request_markdown(change_request), encoding="utf-8")
    return path


def approve_change_request(repo_model_path: Path, change_request_id: str) -> dict[str, Any]:
    cr_path = repo_model_path / "change-requests" / f"{change_request_id}.md"
    if not cr_path.exists():
        raise FileNotFoundError(f"ChangeRequest not found: {cr_path}")

    parsed = parse_file(cr_path)
    fm = parsed.frontmatter or {}

    validation = validate_change_request(fm)
    errors = [v for v in validation if v.severity == "ERROR"]
    if errors:
        raise ValueError(f"ChangeRequest validation failed: {[e.code for e in errors]}")

    if fm.get("approval_status") == "approved":
        raise ValueError(f"ChangeRequest '{change_request_id}' is already approved.")

    # Apply linked patch proposals
    proposal_ids = fm.get("source_patch_proposals", [])
    changed_files: list[str] = []
    audit_events: list[str] = []
    index_rebuilt = False
    db_path: str | None = None

    for pid in proposal_ids:
        if isinstance(pid, str):
            result = apply_patch_proposal(repo_model_path, pid)
            changed_files.extend(result.changed_files)
            if result.audit_event_written:
                audit_events.append(pid)
            if result.index_rebuilt:
                index_rebuilt = True
                db_path = result.db_path

    # Update CR metadata
    frontmatter = dict(fm)
    frontmatter["approval_status"] = "approved"
    frontmatter["approved_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter["approved_by"] = "system"
    frontmatter["implementation_status"] = "completed"
    frontmatter["changed_files"] = changed_files

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
    cr_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "change_request_id": change_request_id,
        "changed_files": changed_files,
        "audit_events": audit_events,
        "index_rebuilt": index_rebuilt,
        "db_path": db_path,
    }


def reject_change_request(
    repo_model_path: Path,
    change_request_id: str,
    reason: str | None = None,
) -> None:
    cr_path = repo_model_path / "change-requests" / f"{change_request_id}.md"
    if not cr_path.exists():
        raise FileNotFoundError(f"ChangeRequest not found: {cr_path}")

    parsed = parse_file(cr_path)
    fm = parsed.frontmatter or {}

    frontmatter = dict(fm)
    frontmatter["approval_status"] = "rejected"
    frontmatter["rejected_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter["rejected_by"] = "system"
    if reason:
        frontmatter["rejection_reason"] = reason

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
    cr_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

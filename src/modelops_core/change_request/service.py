"""ChangeRequest CRUD and lifecycle services."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from modelops_core.approval.risk_service import assess_change_request
from modelops_core.repository import parse_file

_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$")

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected", "implemented"},
    "approved": {"implemented", "rejected"},
    "rejected": set(),
    "implemented": set(),
}


def _record_approval(frontmatter: dict[str, Any], approver: str, decision: str) -> None:
    """Append an approval record to the ChangeRequest frontmatter."""
    if "approvals" not in frontmatter:
        frontmatter["approvals"] = []
    if not isinstance(frontmatter["approvals"], list):
        frontmatter["approvals"] = []
    frontmatter["approvals"].append(
        {
            "approver": approver,
            "decision": decision,
            "approved_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )


def _render_change_request_markdown(data: dict[str, Any]) -> str:
    """Render a ChangeRequest dict as canonical Markdown with YAML frontmatter."""
    frontmatter = dict(data)
    yaml_text = yaml.safe_dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    lines = ["---", yaml_text.rstrip(), "---", ""]
    lines.append(f"# Change Request: {data.get('id', '')}")
    lines.append("")
    if data.get("reason"):
        lines.append("## Reason")
        lines.append(data["reason"])
        lines.append("")
    if data.get("requested_change"):
        lines.append("## Requested Change")
        lines.append(data["requested_change"])
        lines.append("")
    if data.get("expected_impact"):
        lines.append("## Expected Impact")
        lines.append(data["expected_impact"])
        lines.append("")
    return "\n".join(lines) + "\n"


def _change_requests_dir(model_path: Path) -> Path:
    path = model_path / "change-requests"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_change_request(
    model_path: Path,
    cr_id: str,
    title: str,
    status: str = "pending",
    requester: str | None = None,
    reason: str | None = None,
    requested_change: str | None = None,
    expected_impact: str | None = None,
    affected_objects: list[str] | None = None,
    linked_proposals: list[str] | None = None,
    related_issues: list[str] | None = None,
    related_decisions: list[str] | None = None,
    approvers: list[str] | None = None,
    priority: str | None = None,
    source_evidence: str | None = None,
    dry_run: bool = False,
) -> Path:
    """Create a new ChangeRequest canonical file."""
    if not _ID_PATTERN.match(cr_id):
        raise ValueError(f"Invalid ChangeRequest ID: '{cr_id}'. Must match {_ID_PATTERN.pattern}")
    if status not in _VALID_TRANSITIONS:
        raise ValueError(
            f"Invalid status: '{status}'. Must be one of: {', '.join(_VALID_TRANSITIONS)}"
        )

    data: dict[str, Any] = {
        "id": cr_id,
        "type": "ChangeRequest",
        "status": status,
        "name": title,
        "title": title,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if requester:
        data["requester"] = requester
    if reason:
        data["reason"] = reason
    if requested_change:
        data["requested_change"] = requested_change
    if expected_impact:
        data["expected_impact"] = expected_impact
    if affected_objects:
        data["affected_objects"] = affected_objects
    if linked_proposals:
        data["linked_proposals"] = linked_proposals
    if related_issues:
        data["related_issues"] = related_issues
    if related_decisions:
        data["related_decisions"] = related_decisions
    if approvers:
        data["approvers"] = approvers
    if priority:
        data["priority"] = priority
    if source_evidence:
        data["source_evidence"] = source_evidence

    cr_dir = _change_requests_dir(model_path)
    path = cr_dir / f"{cr_id}.md"
    if not dry_run:
        path.write_text(_render_change_request_markdown(data), encoding="utf-8")
    return path


def list_change_requests(model_path: Path) -> list[dict[str, Any]]:
    """List all ChangeRequests in the repository."""
    cr_dir = model_path / "change-requests"
    if not cr_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for f in sorted(cr_dir.glob("CR-*.md")):
        parsed = parse_file(f)
        fm = parsed.frontmatter or {}
        results.append(
            {
                "id": fm.get("id", f.stem),
                "status": fm.get("status", "—"),
                "title": fm.get("title") or fm.get("name") or "—",
                "requester": fm.get("requester", "—"),
                "affected_objects": fm.get("affected_objects") or [],
                "source_path": str(f),
            }
        )
    return results


def load_change_request(model_path: Path, cr_id: str) -> dict[str, Any] | None:
    """Load a single ChangeRequest by ID."""
    cr_dir = model_path / "change-requests"
    path = cr_dir / f"{cr_id}.md"
    if not path.exists():
        return None
    parsed = parse_file(path)
    return parsed.frontmatter or {}


def update_change_request_status(model_path: Path, cr_id: str, new_status: str) -> dict[str, Any]:
    """Transition a ChangeRequest to a new status."""
    if new_status not in _VALID_TRANSITIONS:
        raise ValueError(
            f"Invalid status: '{new_status}'. Must be one of: {', '.join(_VALID_TRANSITIONS)}"
        )

    cr_dir = model_path / "change-requests"
    path = cr_dir / f"{cr_id}.md"
    if not path.exists():
        raise ValueError(f"ChangeRequest not found: {cr_id}")

    parsed = parse_file(path)
    if parsed.frontmatter is None:
        raise ValueError("ChangeRequest file has no frontmatter")

    frontmatter = dict(parsed.frontmatter)
    current_status = str(frontmatter.get("status", ""))

    if new_status == current_status:
        raise ValueError(f"ChangeRequest is already '{current_status}'")

    allowed = _VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition: '{current_status}' -> '{new_status}'. "
            f"Allowed: {', '.join(allowed) or 'none'}"
        )

    frontmatter["status"] = new_status
    if new_status == "implemented":
        frontmatter["implemented_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    path.write_text(_render_change_request_markdown(frontmatter), encoding="utf-8")
    return frontmatter


def approve_change_request(
    model_path: Path, cr_id: str, approver: str, skip_risk_check: bool = False
) -> dict[str, Any]:
    """Approve a ChangeRequest and record the approver."""
    cr_dir = model_path / "change-requests"
    path = cr_dir / f"{cr_id}.md"
    if not path.exists():
        raise ValueError(f"ChangeRequest not found: {cr_id}")

    parsed = parse_file(path)
    if parsed.frontmatter is None:
        raise ValueError("ChangeRequest file has no frontmatter")

    frontmatter = dict(parsed.frontmatter)
    current_status = str(frontmatter.get("status", ""))

    allowed = _VALID_TRANSITIONS.get(current_status, set())
    if "approved" not in allowed:
        raise ValueError(
            f"Invalid transition: '{current_status}' -> 'approved'. "
            f"Allowed: {', '.join(allowed) or 'none'}"
        )

    # Risk assessment
    risk = assess_change_request(frontmatter, model_path)
    if risk.risk_level == "high" and not skip_risk_check:
        raise ValueError(
            f"High-risk ChangeRequest blocked (level: {risk.risk_level}). "
            f"Reasons: {'; '.join(risk.risk_reasons)}. "
            "Use --skip-risk-check to override."
        )

    frontmatter["status"] = "approved"
    _record_approval(frontmatter, approver, "approved")
    frontmatter["risk_level"] = risk.risk_level
    frontmatter["risk_reasons"] = risk.risk_reasons
    frontmatter["risk_triggering_rules"] = risk.triggering_rules
    path.write_text(_render_change_request_markdown(frontmatter), encoding="utf-8")
    return frontmatter


def find_approved_cr_for_proposal(model_path: Path, proposal_id: str) -> dict[str, Any] | None:
    """Find an approved ChangeRequest that links to a given PatchProposal."""
    cr_dir = model_path / "change-requests"
    if not cr_dir.exists():
        return None
    for f in sorted(cr_dir.glob("CR-*.md")):
        parsed = parse_file(f)
        fm = parsed.frontmatter or {}
        if fm.get("status") != "approved":
            continue
        linked = fm.get("linked_proposals") or []
        if proposal_id in linked:
            return fm
    return None


def reject_change_request(
    model_path: Path, cr_id: str, approver: str, reason: str | None = None
) -> dict[str, Any]:
    """Reject a ChangeRequest and record the approver."""
    cr_dir = model_path / "change-requests"
    path = cr_dir / f"{cr_id}.md"
    if not path.exists():
        raise ValueError(f"ChangeRequest not found: {cr_id}")

    parsed = parse_file(path)
    if parsed.frontmatter is None:
        raise ValueError("ChangeRequest file has no frontmatter")

    frontmatter = dict(parsed.frontmatter)
    current_status = str(frontmatter.get("status", ""))

    allowed = _VALID_TRANSITIONS.get(current_status, set())
    if "rejected" not in allowed:
        raise ValueError(
            f"Invalid transition: '{current_status}' -> 'rejected'. "
            f"Allowed: {', '.join(allowed) or 'none'}"
        )

    frontmatter["status"] = "rejected"
    _record_approval(frontmatter, approver, "rejected")
    if reason:
        frontmatter["rejection_reason"] = reason
    path.write_text(_render_change_request_markdown(frontmatter), encoding="utf-8")
    return frontmatter

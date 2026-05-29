"""Generate GitHub-ready change bundles from PatchProposals or ChangeRequests."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.approval import compute_proposal_risk
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.impact.proposal_impact_service import generate_proposal_impact_report
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation import validate_objects


@dataclass
class BundleResult:
    """Result of generating a git bundle."""

    bundle_dir: Path
    proposal_id: str
    affected_objects: list[str] = field(default_factory=list)
    commit_message: str = ""
    pr_body_path: Path | None = None
    readme_path: Path | None = None
    bundle_json_path: Path | None = None
    changed_files_dir: Path | None = None


def _load_proposal(model_path: Path, proposal_id: str) -> dict[str, Any]:
    """Load a PatchProposal by ID from the model directory."""
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        raise ValueError(f"PatchProposal not found: {proposal_id}")
    parsed = parse_file(proposal_path)
    return parsed.frontmatter or {}


def _now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _suggest_commit_message(proposal: dict[str, Any], risk_level: str) -> str:
    """Generate a suggested commit message from a proposal."""
    proposal_id = proposal.get("id", "unknown")
    ops = proposal.get("operations", [])
    op_types: set[str] = set()
    obj_types: set[str] = set()
    for op in ops:
        op_types.add(op.get("op", "change"))
        ot = op.get("object_type")
        if ot:
            obj_types.add(ot)

    op_summary = ", ".join(sorted(op_types)) if op_types else "update"
    type_summary = "/".join(sorted(obj_types)) if obj_types else "model"

    lines = [
        f"feat({proposal_id}): {op_summary} {type_summary} objects",
        "",
        f"Risk level: {risk_level}",
        f"Operations: {len(ops)}",
    ]
    affected = proposal.get("affected_objects") or []
    if affected:
        lines.append(f"Affected: {', '.join(affected[:10])}")
        if len(affected) > 10:
            lines.append(f"... and {len(affected) - 10} more")
    return "\n".join(lines)


def _build_pr_body(
    proposal: dict[str, Any],
    risk: Any,
    impact: Any | None,
    validation_summary: dict[str, Any],
) -> str:
    """Build a Markdown PR body for the bundle."""
    proposal_id = proposal.get("id", "unknown")
    ops = proposal.get("operations", [])
    lines: list[str] = []

    lines.append(f"## Proposal {proposal_id}")
    lines.append("")

    lines.append("### Summary")
    lines.append(f"- **Operations:** {len(ops)}")
    lines.append(f"- **Risk level:** {risk.risk_level}")
    lines.append(f"- **Approval required:** {'yes' if risk.requires_approval else 'no'}")
    lines.append("")

    affected = proposal.get("affected_objects") or []
    if affected:
        lines.append("### Affected Objects")
        for obj_id in affected[:30]:
            lines.append(f"- `{obj_id}`")
        if len(affected) > 30:
            lines.append(f"- ... and {len(affected) - 30} more")
        lines.append("")

    if ops:
        lines.append("### Operations")
        for op in ops[:20]:
            obj_id = op.get("object_id", "—")
            op_type = op.get("op", "—")
            target = op.get("target_path", "—")
            lines.append(f"- `{op_type}` → `{obj_id}` ({target})")
        if len(ops) > 20:
            lines.append(f"- ... and {len(ops) - 20} more operations")
        lines.append("")

    if impact is not None:
        lines.append("### Impact Report")
        lines.append(f"- **High risk:** {'yes' if impact.high_risk else 'no'}")
        lines.append(f"- **Total affected objects:** {len(impact.all_affected_objects)}")
        for obj in impact.all_affected_objects[:15]:
            lines.append(
                f"- `{obj.object_id}` ({obj.object_type or 'Unknown'}) "
                f"— {obj.direction} depth {obj.depth}"
            )
        if len(impact.all_affected_objects) > 15:
            lines.append(f"- ... and {len(impact.all_affected_objects) - 15} more")
        lines.append("")

    lines.append("### Validation")
    lines.append(f"- **Errors:** {validation_summary.get('error_count', 0)}")
    lines.append(f"- **Warnings:** {validation_summary.get('warning_count', 0)}")
    lines.append("")

    lines.append("### Suggested Next Steps")
    lines.append("1. Review the changed files in this bundle.")
    lines.append("2. Confirm validation and impact are acceptable.")
    if risk.requires_approval:
        lines.append("3. Obtain approval before merging.")
    else:
        lines.append("3. Merge if validation passes.")
    lines.append("")

    lines.append("---")
    lines.append(f"*Generated by martenweave at {_now_iso()}*")

    return "\n".join(lines)


def _build_bundle_json(
    proposal: dict[str, Any],
    risk: Any,
    impact: Any | None,
    validation_summary: dict[str, Any],
    copied_files: list[str],
) -> dict[str, Any]:
    """Build the structured bundle.json metadata."""
    return {
        "proposal_id": proposal.get("id"),
        "proposal_type": proposal.get("type"),
        "proposal_status": proposal.get("status"),
        "generated_at": _now_iso(),
        "risk": {
            "level": risk.risk_level,
            "requires_approval": risk.requires_approval,
            "reasons": risk.risk_reasons,
        },
        "impact": {
            "high_risk": impact.high_risk if impact else False,
            "affected_object_ids": impact.affected_object_ids if impact else [],
        },
        "validation": validation_summary,
        "operations_count": len(proposal.get("operations", [])),
        "affected_objects": proposal.get("affected_objects") or [],
        "copied_files": copied_files,
    }


def create_git_bundle(
    repo_root: Path,
    proposal_id: str,
    output_dir: Path | None = None,
) -> BundleResult:
    """Generate a GitHub-ready change bundle from a PatchProposal.

    Args:
        repo_root: Path to the model repository root.
        proposal_id: ID of the PatchProposal to bundle.
        output_dir: Directory to write the bundle. Defaults to
            ``<repo_root>/generated/git_bundles/<proposal_id>``.

    Returns:
        BundleResult with paths to generated artifacts.

    Raises:
        ValueError: If the proposal is not found.
    """
    model_path = resolve_model_path(repo_root)
    generated_path = resolve_generated_path(repo_root)

    if output_dir is None:
        output_dir = generated_path / "git_bundles" / proposal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load proposal
    proposal = _load_proposal(model_path, proposal_id)
    ops = proposal.get("operations", [])

    # Risk assessment
    risk = compute_proposal_risk(ops, model_path)

    # Validation on current model state
    files = scan_repository(model_path)
    parsed_objects = [parse_file(f) for f in files]
    validation = validate_objects(parsed_objects)
    validation_summary = {
        "error_count": validation.error_count,
        "warning_count": validation.warning_count,
        "info_count": validation.info_count,
        "is_valid": validation.is_valid,
    }

    # Impact analysis
    db_path = generated_path / "modelops.db"
    impact = None
    if db_path.exists():
        try:
            impact = generate_proposal_impact_report(db_path, proposal_id, ops, max_depth=2)
        except Exception:
            pass

    # Copy changed canonical files
    changed_dir = output_dir / "changed_files"
    changed_dir.mkdir(parents=True, exist_ok=True)
    copied_files: list[str] = []

    # Build a lookup from object_id → source file path
    object_id_to_path: dict[str, Path] = {}
    for f in files:
        fpath = Path(f)
        parsed = parse_file(fpath)
        if parsed.frontmatter:
            obj_id = str(parsed.frontmatter.get("id", ""))
            if obj_id:
                object_id_to_path[obj_id] = fpath

    affected = proposal.get("affected_objects") or []
    for obj_id in affected:
        src = object_id_to_path.get(obj_id)
        if src and src.exists():
            dst = changed_dir / src.name
            shutil.copy2(src, dst)
            copied_files.append(str(dst.relative_to(output_dir)))

    # Write bundle.json
    bundle_json = _build_bundle_json(proposal, risk, impact, validation_summary, copied_files)
    bundle_json_path = output_dir / "bundle.json"
    bundle_json_path.write_text(json.dumps(bundle_json, indent=2, default=str), encoding="utf-8")

    # Write README.md (human-readable review doc)
    readme_path = output_dir / "README.md"
    readme_path.write_text(
        _build_pr_body(proposal, risk, impact, validation_summary), encoding="utf-8"
    )

    # Write PR_BODY.md (same content, explicit filename)
    pr_body_path = output_dir / "PR_BODY.md"
    pr_body_path.write_text(
        _build_pr_body(proposal, risk, impact, validation_summary), encoding="utf-8"
    )

    # Write COMMIT_MESSAGE.txt
    commit_message = _suggest_commit_message(proposal, risk.risk_level)
    commit_path = output_dir / "COMMIT_MESSAGE.txt"
    commit_path.write_text(commit_message, encoding="utf-8")

    return BundleResult(
        bundle_dir=output_dir,
        proposal_id=proposal_id,
        affected_objects=affected,
        commit_message=commit_message,
        pr_body_path=pr_body_path,
        readme_path=readme_path,
        bundle_json_path=bundle_json_path,
        changed_files_dir=changed_dir,
    )

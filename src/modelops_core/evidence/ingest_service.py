from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from modelops_core.evidence.models import EvidenceFinding, EvidenceFindingKind
from modelops_core.evidence.parsers import parse_csv_report, parse_markdown_note, parse_xlsx_report
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import build_patch_proposal
from modelops_core.repository import parse_file, scan_repository

_RENAME_TARGET_RE = re.compile(r"\bto\s+['\"]([^'\"]+)['\"]", re.IGNORECASE)
_PROPOSAL_ID_SANITIZE_RE = re.compile(r"[^A-Z0-9]+")


def _sanitize_proposal_id(stem: str) -> str:
    """Turn a file stem into a valid uppercase PatchProposal ID suffix."""
    sanitized = _PROPOSAL_ID_SANITIZE_RE.sub("-", stem.upper()).strip("-")
    return sanitized[:30]


def _load_existing_objects(repo_model_path: Path) -> dict[str, dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    for file_path in scan_repository(repo_model_path):
        parsed = parse_file(file_path)
        if parsed.parser_error or not parsed.frontmatter:
            continue
        obj_id = str(parsed.frontmatter.get("id", ""))
        if obj_id:
            existing[obj_id] = dict(parsed.frontmatter)
    return existing


def _issue_op(
    title: str,
    description: str,
    related_objects: list[str] | None = None,
    affected_objects: list[str] | None = None,
    issue_type: str | None = None,
) -> PatchOperation:
    issue_id = f"ISSUE-EVIDENCE-{uuid.uuid4().hex[:8].upper()}"
    after: dict[str, Any] = {
        "id": issue_id,
        "type": "Issue",
        "status": "open",
        "title": title[:80],
        "description": description,
    }
    if related_objects:
        after["related_objects"] = related_objects
    if affected_objects:
        after["affected_objects"] = affected_objects
    if issue_type:
        after["issue_type"] = issue_type
    return PatchOperation(
        op="create_object",
        object_id=issue_id,
        object_type="Issue",
        after=after,
        reason=f"Evidence: {description}",
    )


def _extract_rename_target(message: str) -> str | None:
    match = _RENAME_TARGET_RE.search(message)
    if match:
        return match.group(1).strip()
    return None


def _findings_to_operations(
    findings: list[EvidenceFinding], existing: dict[str, dict[str, Any]]
) -> tuple[list[PatchOperation], list[str], list[str]]:
    operations: list[PatchOperation] = []
    affected: list[str] = []
    skipped: list[str] = []

    for finding in findings:
        obj_id = finding.object_id
        if not obj_id or obj_id not in existing:
            skipped.append(f"{finding.kind.value}: {finding.message}")
            continue

        obj_type = str(existing[obj_id].get("type", ""))

        if finding.kind == EvidenceFindingKind.MISSING_OWNER:
            operations.append(
                _issue_op(
                    title=f"Missing owner for {obj_id}",
                    description=finding.message,
                    affected_objects=[obj_id],
                    issue_type="missing_owner",
                )
            )
            affected.append(obj_id)
        elif finding.kind == EvidenceFindingKind.RENAME_SUGGESTION:
            suggested_name = _extract_rename_target(finding.message)
            if suggested_name:
                operations.append(
                    PatchOperation(
                        op="update_object",
                        object_id=obj_id,
                        object_type=obj_type,
                        target_path="name",
                        before=str(existing[obj_id].get("name", "")),
                        after=suggested_name,
                        reason=f"Evidence: {finding.message}",
                    )
                )
                affected.append(obj_id)
            else:
                operations.append(
                    _issue_op(
                        title=f"Rename suggestion for {obj_id}",
                        description=finding.message,
                        related_objects=[obj_id],
                        issue_type="rename_suggestion",
                    )
                )
                affected.append(obj_id)
        elif finding.kind == EvidenceFindingKind.MISSING_MAPPING:
            operations.append(
                _issue_op(
                    title=f"Missing mapping for {obj_id}",
                    description=finding.message,
                    affected_objects=[obj_id],
                    issue_type="missing_mapping",
                )
            )
            affected.append(obj_id)
        elif finding.kind == EvidenceFindingKind.DECISION_NOTE:
            decision_id = f"DEC-EVIDENCE-{uuid.uuid4().hex[:8].upper()}"
            operations.append(
                PatchOperation(
                    op="create_object",
                    object_id=decision_id,
                    object_type="Decision",
                    after={
                        "id": decision_id,
                        "type": "Decision",
                        "status": "draft",
                        "name": f"Evidence decision for {obj_id}",
                        "title": finding.message[:80],
                        "evidence": finding.message,
                        "attribute": obj_id,
                        "decision_category": "evidence",
                    },
                    reason=f"Evidence: {finding.message}",
                )
            )
            affected.append(obj_id)
        else:
            operations.append(
                _issue_op(
                    title=finding.message[:80],
                    description=finding.message,
                    related_objects=[obj_id],
                    issue_type=finding.kind.value,
                )
            )
            affected.append(obj_id)

    return operations, affected, skipped


def ingest_evidence(
    repo_model_path: Path,
    source_path: Path,
    output_format: str = "proposal",
) -> dict[str, Any]:
    """Ingest evidence and return a PatchProposal or issue summary dict."""
    suffix = source_path.suffix.lower()
    if suffix == ".md":
        findings = parse_markdown_note(source_path)
    elif suffix == ".csv":
        findings = parse_csv_report(source_path)
    elif suffix == ".xlsx":
        findings = parse_xlsx_report(source_path)
    else:
        raise ValueError(f"Unsupported evidence format: {suffix}")

    existing = _load_existing_objects(repo_model_path)
    operations, affected, skipped = _findings_to_operations(findings, existing)

    if output_format == "proposal":
        proposal_id = f"PP-EVIDENCE-{_sanitize_proposal_id(source_path.stem)}"
        proposal = build_patch_proposal(
            proposal_id=proposal_id,
            operations=operations,
            affected_objects=affected,
            source_evidence=str(source_path),
            created_by="system",
            generated_by="evidence_ingest",
        )
        proposal["skipped_findings"] = skipped
        return proposal

    return {
        "type": "EvidenceSummary",
        "findings_count": len(findings),
        "operations_count": len(operations),
        "affected_objects": affected,
        "skipped_findings": skipped,
        "source": str(source_path),
    }

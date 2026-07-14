from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from modelops_core.evidence.models import EvidenceFinding, EvidenceFindingKind
from modelops_core.evidence.parsers import parse_csv_report, parse_markdown_note, parse_xlsx_report
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import build_patch_proposal
from modelops_core.repository import parse_file, scan_repository


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

        if finding.kind == EvidenceFindingKind.MISSING_OWNER and finding.field:
            operations.append(
                PatchOperation(
                    op="update_object",
                    object_id=obj_id,
                    object_type=str(existing[obj_id].get("type", "")),
                    target_path="owner",
                    before=None,
                    after="TBD_OWNER",
                    reason=f"Evidence: {finding.message}",
                )
            )
            affected.append(obj_id)
        elif finding.kind == EvidenceFindingKind.RENAME_SUGGESTION and finding.field:
            operations.append(
                PatchOperation(
                    op="update_object",
                    object_id=obj_id,
                    object_type=str(existing[obj_id].get("type", "")),
                    target_path="name",
                    before=str(existing[obj_id].get("name", "")),
                    after="TBD_NAME",
                    reason=f"Evidence: {finding.message}",
                )
            )
            affected.append(obj_id)
        elif finding.kind == EvidenceFindingKind.MISSING_MAPPING:
            operations.append(
                PatchOperation(
                    op="create_object",
                    object_id=f"MAP-EVIDENCE-{uuid.uuid4().hex[:8].upper()}",
                    object_type="Mapping",
                    after={
                        "id": f"MAP-EVIDENCE-{uuid.uuid4().hex[:8].upper()}",
                        "type": "Mapping",
                        "status": "draft",
                        "name": f"Evidence mapping for {obj_id}",
                        "target_object": obj_id,
                    },
                    reason=f"Evidence: {finding.message}",
                )
            )
            affected.append(obj_id)
        else:
            operations.append(
                PatchOperation(
                    op="create_object",
                    object_id=f"ISSUE-EVIDENCE-{uuid.uuid4().hex[:8].upper()}",
                    object_type="Issue",
                    after={
                        "id": f"ISSUE-EVIDENCE-{uuid.uuid4().hex[:8].upper()}",
                        "type": "Issue",
                        "status": "draft",
                        "title": finding.message[:80],
                        "description": finding.message,
                        "related_object": obj_id,
                    },
                    reason=f"Evidence: {finding.message}",
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
        proposal_id = f"PP-EVIDENCE-{source_path.stem.upper()[:30]}"
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

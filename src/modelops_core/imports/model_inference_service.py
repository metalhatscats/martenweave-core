"""Deterministic model inference from dataset profiles."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any


def _sanitize_id(text: str) -> str:
    """Convert arbitrary text to a valid canonical ID segment."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip())
    cleaned = cleaned.strip("-")
    return cleaned.upper() if cleaned else "UNKNOWN"


def _is_identifier_column(name: str) -> bool:
    lower = name.lower()
    return any(k in lower for k in ("id", "key", "code", "num", "no"))


def _is_foreign_key_column(name: str) -> bool:
    lower = name.lower()
    return lower.endswith("_id") and not _is_identifier_column(name.replace("_id", ""))


def _semantic_category(inferred_type: str, col_name: str) -> str:
    lower = col_name.lower()
    if _is_identifier_column(lower):
        return "identifier"
    if inferred_type == "boolean":
        return "flag"
    if inferred_type in ("integer", "decimal"):
        return "numeric"
    if "date" in lower or "time" in lower:
        return "temporal"
    if "amount" in lower or "price" in lower or "cost" in lower or "value" in lower:
        return "monetary"
    return "text"


def _infer_objects_from_sheet(
    sheet_profile: dict[str, Any],
    dataset_id: str,
    file_name: str,
    sheet_index: int,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Generate draft objects from a single sheet/profile.

    Returns (operations, assumptions, human_checks).
    """
    operations: list[dict[str, Any]] = []
    assumptions: list[str] = []
    human_checks: list[str] = []

    sheet_name = sheet_profile.get("sheet_name") or dataset_id
    stem = _sanitize_id(dataset_id)
    sheet_stem = _sanitize_id(sheet_name)

    # Domain object
    domain_obj_id = f"DOMAIN-{stem}"
    if sheet_index == 0:
        operations.append(
            {
                "op": "add_object",
                "object_id": domain_obj_id,
                "object_type": "MasterDataDomain",
                "after": {
                    "id": domain_obj_id,
                    "type": "MasterDataDomain",
                    "status": "draft",
                    "name": f"{sheet_name} Domain",
                    "description": f"Inferred domain from profile {dataset_id}.",
                },
                "reason": "Domain inferred from profiled file.",
            }
        )

    # Dataset object
    dataset_obj_id = f"DATASET-{stem}"
    if sheet_index == 0:
        operations.append(
            {
                "op": "add_object",
                "object_id": dataset_obj_id,
                "object_type": "Dataset",
                "after": {
                    "id": dataset_obj_id,
                    "type": "Dataset",
                    "status": "draft",
                    "name": file_name,
                    "domain": domain_obj_id,
                    "description": f"Inferred dataset from profile {dataset_id}.",
                },
                "reason": "Dataset inferred from profiled file.",
            }
        )

    # BusinessEntity object (one per sheet/profile)
    entity_obj_id = f"ENTITY-{stem}-{sheet_stem}"
    operations.append(
        {
            "op": "add_object",
            "object_id": entity_obj_id,
            "object_type": "BusinessEntity",
            "after": {
                "id": entity_obj_id,
                "type": "BusinessEntity",
                "status": "draft",
                "name": sheet_name,
                "domain": domain_obj_id,
                "description": f"Inferred entity for sheet {sheet_name}.",
            },
            "reason": "BusinessEntity inferred from sheet/file name.",
        }
    )

    columns = sheet_profile.get("columns", [])
    if not columns:
        assumptions.append(
            f"No columns found for sheet {sheet_name}; skipping attribute inference."
        )
        return operations, assumptions, human_checks

    fk_candidates: list[dict[str, Any]] = []

    for col in columns:
        col_name = col.get("name", "UNKNOWN")
        col_stem = _sanitize_id(col_name)
        inferred_type = col.get("inferred_type", "string")

        attr_obj_id = f"ATTR-{stem}-{sheet_stem}-{col_stem}"
        fep_obj_id = f"FEP-{stem}-{sheet_stem}-{col_stem}"

        operations.append(
            {
                "op": "add_object",
                "object_id": attr_obj_id,
                "object_type": "Attribute",
                "after": {
                    "id": attr_obj_id,
                    "type": "Attribute",
                    "status": "draft",
                    "name": col_name,
                    "domain": domain_obj_id,
                    "semantic_category": _semantic_category(inferred_type, col_name),
                    "description": f"Inferred attribute for column {col_name}.",
                },
                "reason": f"Attribute inferred from column {col_name}.",
            }
        )

        operations.append(
            {
                "op": "add_object",
                "object_id": fep_obj_id,
                "object_type": "FieldEndpoint",
                "after": {
                    "id": fep_obj_id,
                    "type": "FieldEndpoint",
                    "status": "draft",
                    "name": col_name,
                    "domain": domain_obj_id,
                    "endpoint_type": "file_column",
                    "business_attribute": attr_obj_id,
                    "description": f"Inferred field endpoint for column {col_name}.",
                },
                "reason": f"FieldEndpoint inferred from column {col_name}.",
            }
        )

        if _is_foreign_key_column(col_name):
            fk_candidates.append(col)

    # Mapping candidates for FK-like columns
    for fk_col in fk_candidates:
        fk_name = fk_col.get("name", "UNKNOWN")
        fk_stem = _sanitize_id(fk_name)
        target_name = fk_name.lower().replace("_id", "").replace("id", "")
        target_stem = _sanitize_id(target_name) if target_name else "TARGET"
        map_obj_id = f"MAP-{stem}-{sheet_stem}-{fk_stem}-TO-{target_stem}"

        operations.append(
            {
                "op": "add_object",
                "object_id": map_obj_id,
                "object_type": "Mapping",
                "after": {
                    "id": map_obj_id,
                    "type": "Mapping",
                    "status": "draft",
                    "name": f"Map {fk_name} to {target_name}",
                    "description": f"Inferred mapping for foreign-key-like column {fk_name}.",
                },
                "reason": f"Mapping inferred from foreign-key-like column {fk_name}.",
            }
        )
        assumptions.append(
            f"Column {fk_name} looks like a foreign key. Verify the target entity."
        )

    human_checks.append(f"Review inferred entity {entity_obj_id} and its attributes.")
    human_checks.append("Verify semantic categories and endpoint types match your domain.")

    return operations, assumptions, human_checks


def infer_model_from_profile(
    profile: dict[str, Any],
    dataset_id: str,
) -> dict[str, Any]:
    """Generate a PatchProposal from a dataset profile dict.

    The profile may be a CSV profile (has 'columns') or an XLSX workbook
    profile (has 'sheets'). The output is a PatchProposal dict with draft
    canonical objects as 'add_object' operations.
    """
    file_path = profile.get("file_path", "")
    file_name = file_path.split("/")[-1] if "/" in file_path else file_path

    all_operations: list[dict[str, Any]] = []
    all_assumptions: list[str] = []
    all_human_checks: list[str] = []
    affected_objects: list[str] = []

    sheets = profile.get("sheets")
    if sheets is not None:
        # XLSX workbook profile
        for idx, sheet in enumerate(sheets):
            if not sheet.get("status", {}).get("success", True):
                all_assumptions.append(
                    f"Sheet {sheet.get('sheet_name')} was skipped due to errors."
                )
                continue
            ops, assump, checks = _infer_objects_from_sheet(
                sheet, dataset_id, file_name, idx
            )
            all_operations.extend(ops)
            all_assumptions.extend(assump)
            all_human_checks.extend(checks)
    else:
        # CSV single-profile
        ops, assump, checks = _infer_objects_from_sheet(
            profile, dataset_id, file_name, 0
        )
        all_operations.extend(ops)
        all_assumptions.extend(assump)
        all_human_checks.extend(checks)

    for op in all_operations:
        oid = op.get("object_id")
        if oid and oid not in affected_objects:
            affected_objects.append(oid)

    proposal_id = f"PP-INFER-{_sanitize_id(dataset_id)}"

    return {
        "id": proposal_id,
        "type": "PatchProposal",
        "status": "pending_review",
        "name": proposal_id,
        "title": f"Inferred model from dataset profile {dataset_id}",
        "created_by": "system",
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_evidence": f"Dataset profile: {dataset_id}",
        "affected_objects": affected_objects,
        "operations": all_operations,
        "validation_status": "pending",
        "validation_results": [],
        "assumptions": all_assumptions,
        "human_checks": list(set(all_human_checks)),
    }

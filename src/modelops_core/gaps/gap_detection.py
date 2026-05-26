"""Dataset-to-model gap detection."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.imports.dataset_profiler import DatasetProfile


@dataclass
class ColumnMatch:
    column_name: str
    matched_endpoint_id: str
    match_type: str  # "exact" or "normalized"


@dataclass
class ColumnGap:
    column_name: str
    gap_code: str
    severity: str
    message: str
    evidence_ids: list[str] = field(default_factory=list)
    source_dataset_metadata: dict[str, Any] = field(default_factory=dict)
    recommended_proposal_op: dict[str, Any] | None = None


@dataclass
class DatasetGapReport:
    dataset_id: str
    matches: list[ColumnMatch] = field(default_factory=list)
    gaps: list[ColumnGap] = field(default_factory=list)


def _normalize(name: str) -> str:
    return name.strip().lower().replace("_", "-").replace(" ", "-")


def _build_endpoint_index(db_path: Path) -> dict[str, dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, frontmatter_json FROM objects WHERE type = 'FieldEndpoint'"
        ).fetchall()
    finally:
        conn.close()

    endpoints: dict[str, dict[str, Any]] = {}
    for row in rows:
        fm = __import__("json").loads(row[1])
        endpoints[row[0]] = {
            "id": row[0],
            "column_name": fm.get("column_name"),
            "field_name": fm.get("field_name"),
            "sap_field": fm.get("sap_field"),
            "technical_name": fm.get("technical_name"),
            "name": fm.get("name"),
        }
    return endpoints


def _find_matches(column_name: str, endpoints: dict[str, dict[str, Any]]) -> list[ColumnMatch]:
    matches: list[ColumnMatch] = []
    norm_col = _normalize(column_name)

    for ep_id, ep in endpoints.items():
        for field_name, value in ep.items():
            if field_name == "id" or value is None:
                continue
            if value == column_name:
                matches.append(
                    ColumnMatch(
                        column_name=column_name,
                        matched_endpoint_id=ep_id,
                        match_type="exact",
                    )
                )
                break
            elif _normalize(str(value)) == norm_col:
                matches.append(
                    ColumnMatch(
                        column_name=column_name,
                        matched_endpoint_id=ep_id,
                        match_type="normalized",
                    )
                )
                break

    return matches


_GAP_SEVERITY: dict[str, str] = {
    "UNMODELED_DATASET_COLUMN": "warning",
    "DATASET_COLUMN_MULTIPLE_MATCHES": "warning",
    "MODEL_ATTRIBUTE_MISSING_SOURCE": "critical",
    "MISSING_OWNER": "warning",
    "DUPLICATE_COLUMN_NAME": "warning",
    "EMPTY_DATASET": "info",
    "NO_MATCHING_ENDPOINTS": "warning",
}


def _severity_for_gap(gap_code: str) -> str:
    return _GAP_SEVERITY.get(gap_code, "info")


def _build_recommended_op(gap: ColumnGap) -> dict[str, Any] | None:
    if gap.gap_code == "UNMODELED_DATASET_COLUMN":
        return {
            "op": "create_object",
            "object_type": "FieldEndpoint",
            "target_path": "column_name",
            "after": gap.column_name,
            "reason": gap.message,
        }
    if gap.gap_code == "DATASET_COLUMN_MULTIPLE_MATCHES":
        return {
            "op": "create_issue",
            "object_type": "Issue",
            "target_path": "source_column",
            "after": gap.column_name,
            "reason": gap.message,
        }
    return None


def detect_dataset_gaps(profile: DatasetProfile, db_path: Path) -> DatasetGapReport:
    """Match dataset columns against FieldEndpoint objects in the index."""
    endpoints = _build_endpoint_index(db_path)
    matches: list[ColumnMatch] = []
    gaps: list[ColumnGap] = []

    dataset_meta = {
        "dataset_id": profile.dataset_id,
        "row_count": profile.row_count,
    }

    # Edge case: empty dataset
    if not profile.columns:
        gaps.append(
            ColumnGap(
                column_name="",
                gap_code="EMPTY_DATASET",
                severity=_severity_for_gap("EMPTY_DATASET"),
                message=f"Dataset '{profile.dataset_id}' has no columns.",
                source_dataset_metadata=dataset_meta,
            )
        )
        return DatasetGapReport(
            dataset_id=profile.dataset_id,
            matches=matches,
            gaps=gaps,
        )

    # Detect duplicate column names
    seen: set[str] = set()
    for col in profile.columns:
        if col.name in seen:
            gaps.append(
                ColumnGap(
                    column_name=col.name,
                    gap_code="DUPLICATE_COLUMN_NAME",
                    severity=_severity_for_gap("DUPLICATE_COLUMN_NAME"),
                    message=f"Duplicate column name '{col.name}' in dataset.",
                    source_dataset_metadata=dataset_meta,
                    recommended_proposal_op={
                        "op": "create_issue",
                        "object_type": "Issue",
                        "target_path": "source_column",
                        "after": col.name,
                        "reason": f"Duplicate column name '{col.name}' in dataset.",
                    },
                )
            )
        seen.add(col.name)

    for col in profile.columns:
        col_matches = _find_matches(col.name, endpoints)
        if not col_matches:
            gap = ColumnGap(
                column_name=col.name,
                gap_code="UNMODELED_DATASET_COLUMN",
                severity=_severity_for_gap("UNMODELED_DATASET_COLUMN"),
                message=f"Dataset column '{col.name}' has no matching FieldEndpoint.",
                source_dataset_metadata=dataset_meta,
            )
            gap.recommended_proposal_op = _build_recommended_op(gap)
            gaps.append(gap)
        elif len(col_matches) > 1:
            gap = ColumnGap(
                column_name=col.name,
                gap_code="DATASET_COLUMN_MULTIPLE_MATCHES",
                severity=_severity_for_gap("DATASET_COLUMN_MULTIPLE_MATCHES"),
                message=f"Dataset column '{col.name}' matches multiple endpoints.",
                source_dataset_metadata=dataset_meta,
            )
            gap.recommended_proposal_op = _build_recommended_op(gap)
            gaps.append(gap)
            matches.extend(col_matches)
        else:
            matches.extend(col_matches)

    # Edge case: no matching endpoints at all
    if profile.columns and not matches:
        gaps.append(
            ColumnGap(
                column_name="",
                gap_code="NO_MATCHING_ENDPOINTS",
                severity=_severity_for_gap("NO_MATCHING_ENDPOINTS"),
                message=(
                    f"None of the {len(profile.columns)} columns in "
                    f"'{profile.dataset_id}' matched a FieldEndpoint."
                ),
                source_dataset_metadata=dataset_meta,
            )
        )

    return DatasetGapReport(
        dataset_id=profile.dataset_id,
        matches=matches,
        gaps=gaps,
    )


def detect_model_gaps(db_path: Path) -> list[ColumnGap]:
    """Detect model-side gaps by querying the SQLite index.

    Returns gaps for:
    - Attributes with no linked FieldEndpoint (MODEL_ATTRIBUTE_MISSING_SOURCE)
    - Objects missing an owner (MISSING_OWNER)
    """
    gaps: list[ColumnGap] = []
    conn = sqlite3.connect(str(db_path))
    try:
        # Attributes with no incoming represents_attribute relationship
        attr_rows = conn.execute(
            "SELECT id, frontmatter_json FROM objects WHERE type = 'Attribute'"
        ).fetchall()

        rel_rows = conn.execute(
            "SELECT to_object_id FROM object_relationships "
            "WHERE relationship_type = 'represents_attribute'"
        ).fetchall()
        linked_attrs = {r[0] for r in rel_rows}

        for attr_id, _fm_json in attr_rows:
            if attr_id not in linked_attrs:
                gaps.append(
                    ColumnGap(
                        column_name=attr_id,
                        gap_code="MODEL_ATTRIBUTE_MISSING_SOURCE",
                        severity=_severity_for_gap("MODEL_ATTRIBUTE_MISSING_SOURCE"),
                        message=(
                            f"Attribute '{attr_id}' has no linked FieldEndpoint."
                        ),
                    )
                )

        # Objects missing owner
        owner_types = ("Attribute", "FieldEndpoint")
        obj_rows = conn.execute(
            "SELECT id, type, frontmatter_json FROM objects WHERE type IN (?, ?)",
            owner_types,
        ).fetchall()
        for obj_id, obj_type, fm_json in obj_rows:
            fm = __import__("json").loads(fm_json)
            if not fm.get("business_owner") and not fm.get("technical_owner"):
                gaps.append(
                    ColumnGap(
                        column_name=obj_id,
                        gap_code="MISSING_OWNER",
                        severity=_severity_for_gap("MISSING_OWNER"),
                        message=f"{obj_type} '{obj_id}' is missing an owner.",
                    )
                )
    finally:
        conn.close()

    return gaps


def _sanitize_id_part(value: str) -> str:
    """Sanitize a string for use in an object ID part.

    Replaces underscores with hyphens and removes characters that do not
    match ``^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$``.
    """
    cleaned = value.upper().replace("_", "-").replace(" ", "-")
    # Remove any remaining invalid characters
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
    cleaned = "".join(c for c in cleaned if c in allowed)
    # Collapse multiple hyphens
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")


def promote_gaps_to_proposal(
    report: DatasetGapReport,
    repo_model_path: Path,
) -> Path:
    """Promote dataset gaps to a draft PatchProposal.

    Creates a PatchProposal with operations derived from gap
    ``recommended_proposal_op`` values. The proposal is written to
    ``model/patch-proposals/`` and remains in ``pending_review`` status.
    """
    from modelops_core.patching.patch_model import PatchOperation
    from modelops_core.patching.patch_proposal_service import (
        build_patch_proposal,
        write_patch_proposal,
    )

    safe_dataset_id = _sanitize_id_part(report.dataset_id)
    proposal_id = f"PP-GAP-{safe_dataset_id}-001"
    ops: list[PatchOperation] = []
    for gap in report.gaps:
        if gap.recommended_proposal_op:
            ops.append(PatchOperation(**gap.recommended_proposal_op))

    proposal = build_patch_proposal(
        proposal_id=proposal_id,
        operations=ops,
        affected_objects=[],
        source_evidence=f"Auto-generated from gap detection on {report.dataset_id}",
        created_by="system",
    )
    return write_patch_proposal(proposal, repo_model_path)

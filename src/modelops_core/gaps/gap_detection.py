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


def detect_dataset_gaps(profile: DatasetProfile, db_path: Path) -> DatasetGapReport:
    """Match dataset columns against FieldEndpoint objects in the index."""
    endpoints = _build_endpoint_index(db_path)
    matches: list[ColumnMatch] = []
    gaps: list[ColumnGap] = []

    for col in profile.columns:
        col_matches = _find_matches(col.name, endpoints)
        if not col_matches:
            gaps.append(
                ColumnGap(
                    column_name=col.name,
                    gap_code="UNMODELED_DATASET_COLUMN",
                    severity="warning",
                    message=f"Dataset column '{col.name}' has no matching FieldEndpoint.",
                )
            )
        elif len(col_matches) > 1:
            gaps.append(
                ColumnGap(
                    column_name=col.name,
                    gap_code="DATASET_COLUMN_MULTIPLE_MATCHES",
                    severity="info",
                    message=f"Dataset column '{col.name}' matches multiple endpoints.",
                )
            )
            matches.extend(col_matches)
        else:
            matches.extend(col_matches)

    return DatasetGapReport(
        dataset_id=profile.dataset_id,
        matches=matches,
        gaps=gaps,
    )

"""Repository health report generation."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from modelops_core.index.queries import get_object_counts_by_type
from modelops_core.validation.result import ValidationSummary


@dataclass
class CoverageGaps:
    objects_without_name: int = 0
    objects_without_description: int = 0
    types_with_zero_count: list[str] = field(default_factory=list)


@dataclass
class OwnershipCoverage:
    total_eligible: int = 0
    with_owner: int = 0
    without_owner: int = 0
    percentage: float = 0.0


@dataclass
class RepositoryHealthReport:
    """Aggregated repository health."""

    object_count: int = 0
    type_counts: dict[str, int] = field(default_factory=dict)
    validation_summary: ValidationSummary | None = None
    coverage_gaps: CoverageGaps | None = None
    ownership_coverage: OwnershipCoverage | None = None
    index_fresh: bool = False


def generate_repository_health(
    db_path: Path, validation_summary: ValidationSummary | None = None
) -> RepositoryHealthReport:
    """Generate a health report from the SQLite index."""
    conn = sqlite3.connect(str(db_path))
    try:
        manifest_rows = conn.execute(
            "SELECT key, value FROM index_manifest"
        ).fetchall()
        manifest = {k: v for k, v in manifest_rows}

        type_counts = get_object_counts_by_type(db_path)
        total_objects = sum(type_counts.values())

        # Simple coverage check: count objects missing name or description
        name_missing = conn.execute(
            "SELECT COUNT(*) FROM objects WHERE name IS NULL OR name = ''"
        ).fetchone()[0]
        desc_missing = conn.execute(
            "SELECT COUNT(*) FROM objects WHERE description IS NULL OR description = ''"
        ).fetchone()[0]

        coverage = CoverageGaps(
            objects_without_name=name_missing,
            objects_without_description=desc_missing,
        )

        # Ownership coverage
        import json

        _OWNERSHIP_TYPES = {
            "Attribute",
            "FieldEndpoint",
            "Dataset",
            "Mapping",
            "ValidationRule",
            "Issue",
            "Decision",
            "BusinessEntity",
            "ValueList",
            "ValueMapping",
        }
        _OWNERSHIP_FIELDS = {
            "business_owner",
            "technical_owner",
            "data_steward",
            "accountable_team",
            "approver",
        }
        rows = conn.execute(
            "SELECT type, frontmatter_json FROM objects"
        ).fetchall()
        total_eligible = 0
        with_owner = 0
        for obj_type, fm_json in rows:
            if obj_type not in _OWNERSHIP_TYPES:
                continue
            total_eligible += 1
            try:
                fm = json.loads(fm_json or "{}")
                if any(fm.get(field) for field in _OWNERSHIP_FIELDS):
                    with_owner += 1
            except Exception:
                continue
        ownership = OwnershipCoverage(
            total_eligible=total_eligible,
            with_owner=with_owner,
            without_owner=total_eligible - with_owner,
            percentage=round(with_owner / total_eligible * 100, 1)
            if total_eligible
            else 0.0,
        )

        index_fresh = manifest.get("validation_status") == "valid"

        return RepositoryHealthReport(
            object_count=total_objects,
            type_counts=type_counts,
            validation_summary=validation_summary,
            coverage_gaps=coverage,
            ownership_coverage=ownership,
            index_fresh=index_fresh,
        )
    finally:
        conn.close()

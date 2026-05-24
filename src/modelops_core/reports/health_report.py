"""Repository health report generation."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
class CoverageGap:
    """A single coverage gap with remediation hint."""

    object_id: str
    object_type: str
    object_name: str | None
    gap_type: str
    suggested_action: str


@dataclass
class DataQualityCoverage:
    """Deterministic coverage metrics for data quality and governance."""

    active_attributes: int = 0
    attributes_with_rules: int = 0
    active_field_endpoints: int = 0
    endpoints_with_lov: int = 0
    active_mappings: int = 0
    mappings_with_value_mapping: int = 0
    active_datasets: int = 0
    datasets_with_profile: int = 0
    active_objects: int = 0
    objects_with_owner: int = 0

    @property
    def attribute_rule_coverage_percent(self) -> float:
        return (
            round(self.attributes_with_rules / self.active_attributes * 100, 1)
            if self.active_attributes
            else 0.0
        )

    @property
    def endpoint_lov_coverage_percent(self) -> float:
        return (
            round(self.endpoints_with_lov / self.active_field_endpoints * 100, 1)
            if self.active_field_endpoints
            else 0.0
        )

    @property
    def mapping_logic_coverage_percent(self) -> float:
        return (
            round(self.mappings_with_value_mapping / self.active_mappings * 100, 1)
            if self.active_mappings
            else 0.0
        )

    @property
    def dataset_profile_coverage_percent(self) -> float:
        return (
            round(self.datasets_with_profile / self.active_datasets * 100, 1)
            if self.active_datasets
            else 0.0
        )

    @property
    def ownership_coverage_percent(self) -> float:
        return (
            round(self.objects_with_owner / self.active_objects * 100, 1)
            if self.active_objects
            else 0.0
        )


@dataclass
class RepositoryHealthReport:
    """Aggregated repository health."""

    object_count: int = 0
    type_counts: dict[str, int] = field(default_factory=dict)
    validation_summary: ValidationSummary | None = None
    coverage_gaps: CoverageGaps | None = None
    ownership_coverage: OwnershipCoverage | None = None
    data_quality_coverage: DataQualityCoverage | None = None
    coverage_gaps_list: list[CoverageGap] = field(default_factory=list)
    index_fresh: bool = False


def _has_owner(fm: dict[str, Any]) -> bool:
    return any(fm.get(f) for f in (
        "business_owner", "technical_owner", "data_steward",
        "accountable_team", "approver",
    ))


def _is_active(status: str | None) -> bool:
    return str(status or "").lower() in ("active", "draft")


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

        # Load all objects with frontmatter for coverage analysis
        rows = conn.execute(
            "SELECT id, type, name, status, frontmatter_json FROM objects"
        ).fetchall()

        _OWNERSHIP_TYPES = {
            "Attribute", "FieldEndpoint", "Dataset", "Mapping",
            "ValidationRule", "Issue", "Decision", "BusinessEntity",
            "ValueList", "ValueMapping",
        }

        total_eligible = 0
        with_owner = 0

        dq = DataQualityCoverage()
        gaps: list[CoverageGap] = []

        # Build lookup for validation rules by attribute
        validation_rule_attributes: set[str] = set()
        for r in rows:
            if r[1] == "ValidationRule":
                fm = json.loads(r[4] or "{}")
                attr = fm.get("attribute")
                if attr:
                    validation_rule_attributes.add(attr)

        # Build lookup for value lists referenced by field endpoints
        endpoint_value_lists: set[str] = set()
        for r in rows:
            if r[1] == "FieldEndpoint":
                fm = json.loads(r[4] or "{}")
                vl = fm.get("value_list")
                if vl:
                    endpoint_value_lists.add(vl)

        # Build lookup for value mappings referenced by mappings
        mapping_value_mappings: set[str] = set()
        for r in rows:
            if r[1] == "Mapping":
                fm = json.loads(r[4] or "{}")
                vm = fm.get("value_mapping")
                if vm:
                    mapping_value_mappings.add(vm)

        # Build lookup for dataset profiles (check generated dir)
        dataset_profiles: set[str] = set()
        profile_dir = db_path.parent / "dataset_profiles"
        if profile_dir.exists():
            for f in profile_dir.glob("*.json"):
                dataset_profiles.add(f.stem)

        for obj_id, obj_type, obj_name, status, fm_json in rows:
            fm = json.loads(fm_json or "{}")
            active = _is_active(status)

            # Ownership coverage (legacy + new)
            if obj_type in _OWNERSHIP_TYPES and active:
                total_eligible += 1
                if _has_owner(fm):
                    with_owner += 1
                else:
                    gaps.append(
                        CoverageGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            object_name=obj_name,
                            gap_type="missing_owner",
                            suggested_action=(
                                "Add business_owner, technical_owner, or data_steward."
                            ),
                        )
                    )

            # Data quality coverage
            if obj_type == "Attribute" and active:
                dq.active_attributes += 1
                if obj_id in validation_rule_attributes:
                    dq.attributes_with_rules += 1
                else:
                    gaps.append(
                        CoverageGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            object_name=obj_name,
                            gap_type="missing_validation_rule",
                            suggested_action="Add a ValidationRule referencing this attribute.",
                        )
                    )

            if obj_type == "FieldEndpoint" and active:
                dq.active_field_endpoints += 1
                if fm.get("value_list"):
                    dq.endpoints_with_lov += 1
                else:
                    gaps.append(
                        CoverageGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            object_name=obj_name,
                            gap_type="missing_lov",
                            suggested_action="Link a ValueList to this field endpoint.",
                        )
                    )

            if obj_type == "Mapping" and active:
                dq.active_mappings += 1
                if fm.get("value_mapping"):
                    dq.mappings_with_value_mapping += 1
                else:
                    gaps.append(
                        CoverageGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            object_name=obj_name,
                            gap_type="missing_value_mapping",
                            suggested_action="Link a ValueMapping to this mapping.",
                        )
                    )

            if obj_type == "Dataset" and active:
                dq.active_datasets += 1
                if obj_id in dataset_profiles or fm.get("profile"):
                    dq.datasets_with_profile += 1
                else:
                    gaps.append(
                        CoverageGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            object_name=obj_name,
                            gap_type="missing_profile",
                            suggested_action="Run profile-dataset on this dataset.",
                        )
                    )

            if active and obj_type in _OWNERSHIP_TYPES:
                dq.active_objects += 1
                if _has_owner(fm):
                    dq.objects_with_owner += 1

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
            data_quality_coverage=dq,
            coverage_gaps_list=gaps,
            index_fresh=index_fresh,
        )
    finally:
        conn.close()

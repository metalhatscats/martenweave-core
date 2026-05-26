"""Ownership and steward workload report generation."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_OWNER_FIELDS = (
    ("business_owner", "business_owner"),
    ("technical_owner", "technical_owner"),
    ("data_steward", "data_steward"),
    ("accountable_team", "accountable_team"),
    ("approver", "approver"),
)

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


def _is_active(status: str | None) -> bool:
    return str(status or "").lower() in ("active", "draft")


def _has_owner(fm: dict[str, Any]) -> bool:
    return any(fm.get(field_name) for field_name, _ in _OWNER_FIELDS)


@dataclass
class OwnerEntry:
    """A single owner/steward and the objects they own."""

    owner_id: str
    role: str
    object_count: int = 0
    object_types: dict[str, int] = field(default_factory=dict)


@dataclass
class OrphanedObject:
    """An active ownership-eligible object with no owner assigned."""

    object_id: str
    object_type: str
    object_name: str | None


@dataclass
class OwnershipReport:
    """Ownership coverage and steward workload report."""

    owners: list[OwnerEntry] = field(default_factory=list)
    orphaned_objects: list[OrphanedObject] = field(default_factory=list)
    coverage_percent: float = 0.0
    total_eligible: int = 0
    total_with_owner: int = 0


def generate_ownership_report(db_path: Path, _repo_root: Path) -> OwnershipReport:
    """Generate an ownership report from the SQLite index."""
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, type, name, status, frontmatter_json FROM objects"
        ).fetchall()
    finally:
        conn.close()

    owner_map: dict[tuple[str, str], OwnerEntry] = {}
    orphaned: list[OrphanedObject] = []
    total_eligible = 0
    total_with_owner = 0

    for obj_id, obj_type, obj_name, status, fm_json in rows:
        fm = json.loads(fm_json or "{}")
        if obj_type not in _OWNERSHIP_TYPES or not _is_active(status):
            continue

        total_eligible += 1

        if _has_owner(fm):
            total_with_owner += 1
            for field_name, role in _OWNER_FIELDS:
                value = fm.get(field_name)
                if not value:
                    continue
                # Handle both single string and list of strings
                owner_ids: list[str] = []
                if isinstance(value, list):
                    owner_ids = [str(v) for v in value if v]
                else:
                    owner_ids = [str(value)]

                for oid in owner_ids:
                    key = (oid, role)
                    entry = owner_map.get(key)
                    if entry is None:
                        entry = OwnerEntry(owner_id=oid, role=role)
                        owner_map[key] = entry
                    entry.object_count += 1
                    entry.object_types[obj_type] = entry.object_types.get(obj_type, 0) + 1
        else:
            orphaned.append(
                OrphanedObject(
                    object_id=obj_id,
                    object_type=obj_type,
                    object_name=obj_name or None,
                )
            )

    owners = sorted(owner_map.values(), key=lambda o: o.object_count, reverse=True)

    coverage_percent = (
        round(total_with_owner / total_eligible * 100, 1)
        if total_eligible
        else 0.0
    )

    return OwnershipReport(
        owners=owners,
        orphaned_objects=orphaned,
        coverage_percent=coverage_percent,
        total_eligible=total_eligible,
        total_with_owner=total_with_owner,
    )

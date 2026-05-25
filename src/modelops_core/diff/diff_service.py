"""Deterministic diff between two model repository states."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.repository import parse_file, scan_repository


@dataclass
class FieldChange:
    """A single field-level change between two object versions."""

    field: str
    old_value: Any
    new_value: Any


@dataclass
class ChangedObject:
    """An object that exists in both base and head but has differences."""

    object_id: str
    object_type: str
    object_name: str | None
    field_changes: list[FieldChange] = field(default_factory=list)


@dataclass
class DiffResult:
    """Result of comparing two model repository states."""

    base_count: int = 0
    head_count: int = 0
    added: list[dict[str, Any]] = field(default_factory=list)
    removed: list[dict[str, Any]] = field(default_factory=list)
    changed: list[ChangedObject] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def _load_objects(model_path: Path) -> dict[str, dict[str, Any]]:
    """Load all canonical objects from *model_path* into an id→frontmatter map."""
    objects: dict[str, dict[str, Any]] = {}
    if not model_path.exists():
        return objects
    for file_path in scan_repository(model_path):
        parsed = parse_file(file_path)
        if parsed.parser_error is not None or parsed.frontmatter is None:
            continue
        obj_id = parsed.frontmatter.get("id")
        if isinstance(obj_id, str):
            objects[obj_id] = dict(parsed.frontmatter)
    return objects


# Fields that are ignored when comparing objects (metadata that may differ
# without being a semantic change).
_IGNORED_FIELDS: set[str] = {
    "schema_version",
}


def _compare_values(old: Any, new: Any) -> bool:
    """Return True if *old* and *new* are deeply equal."""
    if type(old) is not type(new):
        return False
    if isinstance(old, dict):
        if set(old.keys()) != set(new.keys()):
            return False
        return all(_compare_values(old[k], new[k]) for k in old)
    if isinstance(old, list):
        if len(old) != len(new):
            return False
        return all(
            _compare_values(a, b) for a, b in zip(old, new, strict=True)
        )
    return old == new


def _diff_object(
    base_fm: dict[str, Any],
    head_fm: dict[str, Any],
) -> list[FieldChange]:
    """Compare two frontmatter dicts and return field-level changes."""
    changes: list[FieldChange] = []
    all_fields = set(base_fm) | set(head_fm)
    for field_name in sorted(all_fields):
        if field_name in _IGNORED_FIELDS:
            continue
        old_val = base_fm.get(field_name)
        new_val = head_fm.get(field_name)
        if field_name not in base_fm:
            changes.append(
                FieldChange(field=field_name, old_value=None, new_value=new_val)
            )
        elif field_name not in head_fm:
            changes.append(
                FieldChange(field=field_name, old_value=old_val, new_value=None)
            )
        elif not _compare_values(old_val, new_val):
            changes.append(
                FieldChange(field=field_name, old_value=old_val, new_value=new_val)
            )
    return changes


def diff_repositories(base_path: Path, head_path: Path) -> DiffResult:
    """Compare two model repositories and return differences.

    Args:
        base_path: Path to the base (original) model directory.
        head_path: Path to the head (changed) model directory.

    Returns:
        DiffResult with added, removed, and changed objects.
    """
    base_objects = _load_objects(base_path)
    head_objects = _load_objects(head_path)

    result = DiffResult(
        base_count=len(base_objects),
        head_count=len(head_objects),
    )

    base_ids = set(base_objects)
    head_ids = set(head_objects)

    for obj_id in sorted(head_ids - base_ids):
        fm = head_objects[obj_id]
        result.added.append(
            {
                "object_id": obj_id,
                "object_type": fm.get("type"),
                "object_name": fm.get("name") or fm.get("title"),
                "source_file": fm.get("source_path"),
            }
        )

    for obj_id in sorted(base_ids - head_ids):
        fm = base_objects[obj_id]
        result.removed.append(
            {
                "object_id": obj_id,
                "object_type": fm.get("type"),
                "object_name": fm.get("name") or fm.get("title"),
                "source_file": fm.get("source_path"),
            }
        )

    for obj_id in sorted(base_ids & head_ids):
        field_changes = _diff_object(base_objects[obj_id], head_objects[obj_id])
        if field_changes:
            fm = head_objects[obj_id]
            result.changed.append(
                ChangedObject(
                    object_id=obj_id,
                    object_type=fm.get("type", "Unknown"),
                    object_name=fm.get("name") or fm.get("title"),
                    field_changes=field_changes,
                )
            )

    return result

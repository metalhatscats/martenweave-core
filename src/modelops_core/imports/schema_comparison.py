"""Deterministic comparison of normalized, local schema evidence."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from modelops_core.imports.schema_inspection import NormalizedSchemaDocument, inspect_schema_file


def _items(document: NormalizedSchemaDocument) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "entities": {item.name: asdict(item) for item in document.entities},
        "fields": {
            f"{item.entity_name}.{item.field_path}": asdict(item) for item in document.fields
        },
        "operations": {item.operation_id: asdict(item) for item in document.operations},
    }


def compare_schema_files(base_path: str, candidate_path: str) -> dict[str, Any]:
    """Compare two local contracts; classifications are deterministic clues only."""
    base = inspect_schema_file(Path(base_path))
    candidate = inspect_schema_file(Path(candidate_path))
    base_items, candidate_items = _items(base), _items(candidate)
    differences: list[dict[str, Any]] = []
    for kind in ("entities", "fields", "operations"):
        for identifier in sorted(set(base_items[kind]) | set(candidate_items[kind])):
            before, after = base_items[kind].get(identifier), candidate_items[kind].get(identifier)
            if before is None:
                differences.append(
                    {
                        "kind": kind,
                        "id": identifier,
                        "change": "added",
                        "breaking": False,
                        "rule_id": None,
                    }
                )
            elif after is None:
                differences.append(
                    {
                        "kind": kind,
                        "id": identifier,
                        "change": "removed",
                        "breaking": True,
                        "rule_id": "SCHEMA_REMOVED",
                    }
                )
            elif before != after:
                rule_id = None
                if (
                    kind == "fields"
                    and before.get("required") is not True
                    and after.get("required") is True
                ):
                    rule_id = "SCHEMA_FIELD_NOW_REQUIRED"
                elif kind == "fields" and any(
                    before.get(key) != after.get(key)
                    for key in ("data_type", "length", "precision", "scale")
                ):
                    rule_id = "SCHEMA_FIELD_CONSTRAINT_CHANGED"
                differences.append(
                    {
                        "kind": kind,
                        "id": identifier,
                        "change": "modified",
                        "breaking": rule_id is not None,
                        "rule_id": rule_id,
                        "before": before,
                        "after": after,
                    }
                )
    return {
        "base": {"format": base.source_format, "checksum": base.checksum},
        "candidate": {"format": candidate.source_format, "checksum": candidate.checksum},
        "differences": differences,
        "compatibility_notice": (
            "Potential-breaking findings are deterministic review signals, "
            "not a compatibility guarantee."
        ),
    }

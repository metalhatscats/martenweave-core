"""JSON Schema export service for canonical object types."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modelops_core.schemas.object_models import OBJECT_TYPE_MODELS
from modelops_core.schemas.registry import get_all_types


def export_schemas(type_filter: str | None = None) -> dict[str, Any]:
    """Export JSON Schema for canonical object types.

    Args:
        type_filter: If provided, export only this object type.
            Use ``"all"`` or ``None`` to export every registered type.

    Returns:
        A dict with ``$schema``, ``title``, ``type_count``, and ``schemas`` keys.
        The ``schemas`` value maps object type name to its JSON Schema.
    """
    types = get_all_types()
    if type_filter and type_filter.lower() != "all":
        if type_filter not in types:
            raise ValueError(
                f"Unknown object type '{type_filter}'. Known types: {', '.join(types)}"
            )
        types = [type_filter]

    schemas: dict[str, Any] = {}
    for t in sorted(types):
        model_cls = OBJECT_TYPE_MODELS.get(t)
        if model_cls is None:
            raise RuntimeError(f"No Pydantic model registered for type '{t}'.")
        schemas[t] = model_cls.model_json_schema()

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ModelOps Canonical Object Schemas",
        "type_count": len(schemas),
        "schemas": schemas,
    }


def write_schema_export(
    output_path: Path,
    type_filter: str | None = None,
) -> Path:
    """Write JSON Schema export to *output_path*.

    Returns the written file path.
    """
    result = export_schemas(type_filter=type_filter)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return output_path

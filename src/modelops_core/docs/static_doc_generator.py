"""Generate static Markdown documentation from a model repository index."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

_ANCHOR_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_-")


def _anchor(text: str) -> str:
    """Convert a string to a Markdown anchor."""
    lowered = text.lower().replace(" ", "-").replace("_", "-")
    return "".join(c for c in lowered if c in _ANCHOR_CHARS)


def _fm_field(frontmatter: dict[str, Any], key: str) -> str | None:
    val = frontmatter.get(key)
    if val is None or val == "":
        return None
    return str(val)


def generate_static_docs(
    repo_root: Path,
    output_dir: Path,
    db_path: Path | None = None,
) -> Path:
    """Generate static Markdown docs from the SQLite index.

    Args:
        repo_root: Path to the model repository root.
        output_dir: Directory where docs will be written.
        db_path: Optional path to the SQLite database. Defaults to
            ``<repo_root>/generated/modelops.db``.

    Returns:
        Path to the generated output directory.
    """
    if db_path is None:
        db_path = repo_root / "generated" / "modelops.db"

    if not db_path.exists():
        raise FileNotFoundError(
            f"No index found at {db_path}. Run `modelops build-index` first."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()

        # Load all objects
        cursor.execute(
            "SELECT id, type, status, name, title, domain, description, "
            "source_file, frontmatter_json, body FROM objects ORDER BY type, id"
        )
        rows = cursor.fetchall()

        objects_by_type: dict[str, list[dict[str, Any]]] = {}
        all_objects: list[dict[str, Any]] = []

        for row in rows:
            obj = {
                "id": row[0],
                "type": row[1],
                "status": row[2],
                "name": row[3],
                "title": row[4],
                "domain": row[5],
                "description": row[6],
                "source_file": row[7],
                "frontmatter": json.loads(row[8] or "{}"),
                "body": row[9] or "",
            }
            all_objects.append(obj)
            objects_by_type.setdefault(obj["type"], []).append(obj)

        # Generate index.md
        _write_index_md(output_dir, all_objects, objects_by_type)

        # Generate objects.md (master list)
        _write_objects_md(output_dir, all_objects)

        # Generate per-type pages
        for obj_type, objs in objects_by_type.items():
            _write_type_md(output_dir, obj_type, objs)

    finally:
        conn.close()

    return output_dir


def _write_index_md(
    output_dir: Path,
    all_objects: list[dict[str, Any]],
    objects_by_type: dict[str, list[dict[str, Any]]],
) -> None:
    lines: list[str] = [
        "# Model Documentation",
        "",
        "> **Generated view** — This documentation is a generated view over the "
        "canonical model files. The canonical Markdown + YAML frontmatter objects "
        "in `model/` are the source of truth. This site can be rebuilt at any time "
        "with `modelops build-index` and `modelops docs-build`.",
        "",
        "## Overview",
        "",
        f"- **Total objects**: {len(all_objects)}",
        "- **Object types**:",
    ]

    for obj_type in sorted(objects_by_type.keys()):
        count = len(objects_by_type[obj_type])
        anchor = _anchor(obj_type)
        lines.append(f"  - [{obj_type}]({anchor}.md): {count}")

    lines.extend([
        "",
        "## Browse",
        "",
        "- [All objects](objects.md)",
    ])

    for obj_type in sorted(objects_by_type.keys()):
        anchor = _anchor(obj_type)
        lines.append(f"- [{obj_type}]({anchor}.md)")

    lines.append("")

    (output_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def _write_objects_md(output_dir: Path, all_objects: list[dict[str, Any]]) -> None:
    lines: list[str] = [
        "# All Objects",
        "",
        "> **Generated view** — See [index.md](index.md) for overview.",
        "",
    ]

    for obj in all_objects:
        obj_id = obj["id"]
        obj_type = obj["type"]
        name = obj["name"] or obj["title"] or obj_id
        status = obj["status"]
        anchor = _anchor(obj_id)
        lines.append(f"### {name} (`{obj_id}`) {{#{anchor}}}")
        lines.append(f"- **Type**: {obj_type}")
        lines.append(f"- **Status**: {status}")
        if obj["domain"]:
            lines.append(f"- **Domain**: {obj['domain']}")
        if obj["description"]:
            lines.append(f"- **Description**: {obj['description']}")
        lines.append("")

    (output_dir / "objects.md").write_text("\n".join(lines), encoding="utf-8")


def _write_type_md(
    output_dir: Path,
    obj_type: str,
    objs: list[dict[str, Any]],
) -> None:
    filename = f"{_anchor(obj_type)}.md"
    lines: list[str] = [
        f"# {obj_type}",
        "",
        f"> **Generated view** — [{len(objs)} object(s)](objects.md)",
        "",
    ]

    for obj in objs:
        obj_id = obj["id"]
        name = obj["name"] or obj["title"] or obj_id
        status = obj["status"]
        anchor = _anchor(obj_id)
        lines.append(f"## {name} (`{obj_id}`) {{#{anchor}}}")
        lines.append(f"- **Status**: {status}")
        if obj["domain"]:
            lines.append(f"- **Domain**: {obj['domain']}")

        # Show a few meaningful frontmatter fields
        fm = obj["frontmatter"]
        for key in ("semantic_category", "data_classification", "endpoint_type",
                    "sap_table", "sap_field", "system_type", "usage_type", "scope",
                    "business_owner", "technical_owner", "data_steward"):
            val = _fm_field(fm, key)
            if val:
                lines.append(f"- **{key.replace('_', ' ').title()}**: {val}")

        if obj["description"]:
            lines.append(f"- **Description**: {obj['description']}")

        lines.append("")

    (output_dir / filename).write_text("\n".join(lines), encoding="utf-8")

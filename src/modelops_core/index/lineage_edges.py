"""Generate lineage_edges.jsonl from the SQLite index."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def export_lineage_jsonl(db_path: Path, output_path: Path) -> None:
    """Export all object relationships as newline-delimited JSON lineage edges."""
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT from_object_id, relationship_type, relationship_class, "
            "to_object_id, source_file, confidence FROM object_relationships"
        ).fetchall()
    finally:
        conn.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            edge: dict[str, Any] = {
                "from_object_id": row[0],
                "relationship_type": row[1],
                "relationship_class": row[2],
                "to_object_id": row[3],
                "source_file": row[4],
                "confidence": row[5],
            }
            fh.write(json.dumps(edge, default=str) + "\n")

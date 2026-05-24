"""Generate search_documents.jsonl from the SQLite index."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def export_search_jsonl(db_path: Path, output_path: Path) -> None:
    """Export all indexed objects as newline-delimited JSON search documents."""
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, type, status, name, title, domain, "
            "source_file, frontmatter_json FROM objects"
        ).fetchall()
    finally:
        conn.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            doc: dict[str, Any] = {
                "id": row[0],
                "type": row[1],
                "status": row[2],
                "name": row[3],
                "title": row[4],
                "domain": row[5],
                "source_file": row[6],
                "frontmatter": json.loads(row[7]),
            }
            fh.write(json.dumps(doc, default=str) + "\n")

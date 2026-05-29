"""SQLite query helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def get_object_counts_by_type(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT type, COUNT(*) FROM objects GROUP BY type").fetchall()
        return {row[0]: row[1] for row in rows}
    finally:
        conn.close()


def get_object_by_id(db_path: Path, object_id: str) -> dict[str, Any] | None:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute("SELECT * FROM objects WHERE id = ?", (object_id,)).fetchone()
        if row is None:
            return None
        columns = [
            desc[0]
            for desc in conn.execute("SELECT * FROM objects WHERE id = ?", (object_id,)).description
        ]
        return dict(zip(columns, row, strict=False))
    finally:
        conn.close()


def list_objects(db_path: Path, object_type: str | None = None) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    try:
        if object_type:
            rows = conn.execute("SELECT * FROM objects WHERE type = ?", (object_type,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM objects").fetchall()
        columns = [desc[0] for desc in conn.execute("SELECT * FROM objects").description]
        return [dict(zip(columns, row, strict=False)) for row in rows]
    finally:
        conn.close()


def get_relationships_for_object(db_path: Path, object_id: str) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            """
            SELECT * FROM object_relationships
            WHERE from_object_id = ? OR to_object_id = ?
            """,
            (object_id, object_id),
        ).fetchall()
        columns = [
            desc[0] for desc in conn.execute("SELECT * FROM object_relationships").description
        ]
        return [dict(zip(columns, row, strict=False)) for row in rows]
    finally:
        conn.close()


def get_objects_with_frontmatter(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT id, type, frontmatter_json FROM objects").fetchall()
        return [{"id": row[0], "type": row[1], "frontmatter": row[2]} for row in rows]
    finally:
        conn.close()

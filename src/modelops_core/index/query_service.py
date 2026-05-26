"""Query and search services over the generated SQLite index."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SearchResult:
    """A single object returned by a search or query."""

    object_id: str
    object_type: str
    status: str
    name: str | None
    title: str | None
    domain: str | None
    description: str | None
    source_file: str
    score: float = 0.0
    matched_fields: list[str] = field(default_factory=list)


def _row_to_result(row: sqlite3.Row) -> SearchResult:
    return SearchResult(
        object_id=row["id"],
        object_type=row["type"],
        status=row["status"],
        name=row["name"],
        title=row["title"],
        domain=row["domain"],
        description=row["description"],
        source_file=row["source_file"],
    )


def _build_search_sql(query: str) -> tuple[str, list[Any]]:
    """Build a LIKE-based search query across name, title, description, body.

    Returns (sql, params).
    """
    terms = [t.strip() for t in query.split() if t.strip()]
    if not terms:
        return "SELECT * FROM objects WHERE 1=1", []

    conditions: list[str] = []
    params: list[Any] = []
    for term in terms:
        pattern = f"%{term}%"
        conditions.append(
            "(name LIKE ? OR title LIKE ? OR description LIKE ? OR body LIKE ?)"
        )
        params.extend([pattern] * 4)

    sql = "SELECT * FROM objects WHERE " + " AND ".join(conditions)
    return sql, params


def search_objects(
    db_path: Path,
    query: str,
    object_type: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    tags: list[str] | None = None,
    limit: int = 50,
) -> list[SearchResult]:
    """Keyword search over indexed objects.

    Searches across ``name``, ``title``, ``description``, and ``body``
    using case-insensitive LIKE patterns. Results are scored by the
    number of matched fields.
    """
    if not db_path.exists():
        return []

    sql, params = _build_search_sql(query)
    if object_type:
        sql += " AND type = ?"
        params.append(object_type)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if domain:
        sql += " AND domain = ?"
        params.append(domain)
    if tags:
        placeholders = ", ".join("?" for _ in tags)
        sql += f" AND id IN (SELECT object_id FROM tags WHERE tag IN ({placeholders}))"
        params.extend(tags)
    sql += " LIMIT ?"
    params.append(limit)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
    finally:
        conn.close()

    results: list[SearchResult] = []
    terms = [t.lower() for t in query.split() if t.strip()]
    for row in rows:
        result = _row_to_result(row)
        score = 0
        matched: list[str] = []
        for col in ("name", "title", "description", "body"):
            value = (row[col] or "").lower()
            if any(term in value for term in terms):
                score += 1
                matched.append(col)
        result.score = score
        result.matched_fields = matched
        results.append(result)

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def query_objects(
    db_path: Path,
    object_type: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    name_like: str | None = None,
    tags: list[str] | None = None,
    limit: int = 50,
) -> list[SearchResult]:
    """Structured query over indexed objects.

    Filters by exact match on ``type``, ``status``, ``domain`` and
    optional substring match on ``name``.
    """
    if not db_path.exists():
        return []

    conditions: list[str] = ["1=1"]
    params: list[Any] = []

    if object_type:
        conditions.append("type = ?")
        params.append(object_type)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if domain:
        conditions.append("domain = ?")
        params.append(domain)
    if name_like:
        conditions.append("name LIKE ?")
        params.append(f"%{name_like}%")
    if tags:
        placeholders = ", ".join("?" for _ in tags)
        conditions.append(
            f"id IN (SELECT object_id FROM tags WHERE tag IN ({placeholders}))"
        )
        params.extend(tags)

    sql = "SELECT * FROM objects WHERE " + " AND ".join(conditions)
    sql += " LIMIT ?"
    params.append(limit)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [_row_to_result(row) for row in rows]


def get_object_by_id(db_path: Path, object_id: str) -> dict[str, Any] | None:
    """Fetch a single object from the index by ID.

    Returns the parsed frontmatter dict, or None if not found.
    """
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            "SELECT frontmatter_json FROM objects WHERE id = ?", (object_id,)
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return json.loads(row["frontmatter_json"])


def list_related_objects(
    db_path: Path,
    object_id: str,
    relationship_type: str | None = None,
) -> list[dict[str, Any]]:
    """List objects related to *object_id* via the relationships table.

    Returns a list of dicts with ``to_object_id``, ``relationship_type``,
    and ``relationship_class``.
    """
    if not db_path.exists():
        return []

    sql = (
        "SELECT to_object_id, relationship_type, relationship_class "
        "FROM object_relationships WHERE from_object_id = ?"
    )
    params: list[Any] = [object_id]
    if relationship_type:
        sql += " AND relationship_type = ?"
        params.append(relationship_type)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "to_object_id": row["to_object_id"],
            "relationship_type": row["relationship_type"],
            "relationship_class": row["relationship_class"],
        }
        for row in rows
    ]

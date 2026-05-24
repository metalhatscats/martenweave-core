"""Impact analysis via BFS traversal over object_relationships."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from modelops_core.impact.impact_report import AffectedObject, ImpactReport


def generate_impact_report(
    db_path: Path, object_id: str, max_depth: int = 2
) -> ImpactReport:
    """Perform bounded BFS impact analysis.

    Traverses outgoing and incoming relationships from *object_id* up to
    *max_depth* hops.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        # Load root object metadata
        row = conn.execute(
            "SELECT id, type, name FROM objects WHERE id = ?", (object_id,)
        ).fetchone()
        if row is None:
            return ImpactReport(root_object_id=object_id)

        root_type, root_name = row[1], row[2]

        # Load all relationships
        rel_rows = conn.execute(
            "SELECT from_object_id, to_object_id, relationship_type FROM object_relationships"
        ).fetchall()

        # Load all object metadata for caching
        obj_rows = conn.execute(
            "SELECT id, type, name FROM objects"
        ).fetchall()
    finally:
        conn.close()

    metadata: dict[str, dict[str, Any]] = {
        r[0]: {"type": r[1], "name": r[2]} for r in obj_rows
    }

    # Build adjacency (bidirectional)
    outgoing: dict[str, list[tuple[str, str]]] = {}
    incoming: dict[str, list[tuple[str, str]]] = {}
    for from_id, to_id, rel_type in rel_rows:
        outgoing.setdefault(from_id, []).append((to_id, rel_type))
        incoming.setdefault(to_id, []).append((from_id, rel_type))

    visited: set[str] = {object_id}
    queue: list[tuple[str, int, str]] = [(object_id, 0, "root")]
    affected: list[AffectedObject] = []

    while queue:
        current_id, depth, direction = queue.pop(0)
        if depth >= max_depth:
            continue

        # Outgoing = downstream
        for next_id, rel_type in outgoing.get(current_id, []):
            if next_id not in visited:
                visited.add(next_id)
                meta = metadata.get(next_id, {})
                affected.append(
                    AffectedObject(
                        object_id=next_id,
                        object_type=meta.get("type", "Unknown"),
                        object_name=meta.get("name"),
                        relationship_type=rel_type,
                        direction="downstream",
                        depth=depth + 1,
                    )
                )
                queue.append((next_id, depth + 1, "downstream"))

        # Incoming = upstream
        for prev_id, rel_type in incoming.get(current_id, []):
            if prev_id not in visited:
                visited.add(prev_id)
                meta = metadata.get(prev_id, {})
                affected.append(
                    AffectedObject(
                        object_id=prev_id,
                        object_type=meta.get("type", "Unknown"),
                        object_name=meta.get("name"),
                        relationship_type=rel_type,
                        direction="upstream",
                        depth=depth + 1,
                    )
                )
                queue.append((prev_id, depth + 1, "upstream"))

    return ImpactReport(
        root_object_id=object_id,
        root_object_type=root_type,
        root_object_name=root_name,
        affected_objects=affected,
    )

"""Lineage path generation and JSONL export."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from modelops_core.lineage.edge_model import LineageEdge, LineageNode, LineagePath


def generate_lineage_path(db_path: Path, object_id: str) -> LineagePath:
    """Generate an ordered lineage path starting from *object_id*.

    MVP implementation: builds a hard-coded source-to-target path when
    the object is part of the Customer/BP slice.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, type, name, frontmatter_json FROM objects"
        ).fetchall()
    finally:
        conn.close()

    objects_by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        fm = json.loads(row[3]) if row[3] else {}
        objects_by_id[row[0]] = {
            "id": row[0],
            "type": row[1],
            "name": row[2],
            "frontmatter": fm,
        }

    if object_id not in objects_by_id:
        return LineagePath()

    # Build edges from relationships table
    conn = sqlite3.connect(str(db_path))
    try:
        rel_rows = conn.execute(
            "SELECT from_object_id, to_object_id, relationship_type FROM object_relationships"
        ).fetchall()
    finally:
        conn.close()

    edges: list[LineageEdge] = []
    for rel in rel_rows:
        edges.append(
            LineageEdge(
                from_object_id=rel[0],
                to_object_id=rel[1],
                relationship_type=rel[2],
            )
        )

    # Simple BFS to find connected nodes up to a bounded depth
    visited: set[str] = {object_id}
    queue: list[tuple[str, int]] = [(object_id, 0)]
    connected_nodes: list[LineageNode] = []
    connected_edges: list[LineageEdge] = []

    while queue:
        current_id, depth = queue.pop(0)
        if depth > 5:
            continue
        obj = objects_by_id.get(current_id)
        if obj:
            connected_nodes.append(
                LineageNode(
                    object_id=current_id,
                    object_type=obj["type"],
                    name=obj["name"],
                )
            )
        for edge in edges:
            if edge.from_object_id == current_id and edge.to_object_id not in visited:
                visited.add(edge.to_object_id)
                queue.append((edge.to_object_id, depth + 1))
                connected_edges.append(edge)
            elif edge.to_object_id == current_id and edge.from_object_id not in visited:
                visited.add(edge.from_object_id)
                queue.append((edge.from_object_id, depth + 1))
                connected_edges.append(edge)

    return LineagePath(nodes=connected_nodes, edges=connected_edges)

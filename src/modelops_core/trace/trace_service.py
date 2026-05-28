"""End-to-end traceability graph traversal."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TraceNode:
    """A node in the traceability graph."""

    object_id: str
    object_type: str
    object_name: str | None = None
    source_file: str | None = None
    depth: int = 0


@dataclass
class TraceEdge:
    """A directed edge in the traceability graph."""

    from_object_id: str
    to_object_id: str
    relationship_type: str
    direction: str  # "upstream" or "downstream"
    relationship_class: str | None = None


@dataclass
class TraceResult:
    """Result of a trace query."""

    root_object_id: str
    root_object_type: str | None = None
    root_object_name: str | None = None
    nodes: list[TraceNode] = field(default_factory=list)
    edges: list[TraceEdge] = field(default_factory=list)

    @property
    def upstream(self) -> list[TraceNode]:
        return [n for n in self.nodes if n.depth > 0 and self._is_upstream(n)]

    @property
    def downstream(self) -> list[TraceNode]:
        return [n for n in self.nodes if n.depth > 0 and not self._is_upstream(n)]

    def _is_upstream(self, node: TraceNode) -> bool:
        # A node is upstream if it is the source of an upstream edge
        # (i.e., it was discovered by traversing backward toward the root)
        return any(
            e.direction == "upstream" and e.from_object_id == node.object_id
            for e in self.edges
        )


def trace_object(
    db_path: Path,
    object_id: str,
    max_depth: int = 5,
    direction: str = "both",
    relationship_class: str | None = None,
) -> TraceResult:
    """Trace upstream and/or downstream relationships for an object.

    Args:
        db_path: Path to the SQLite index database.
        object_id: ID of the object to trace from.
        max_depth: Maximum traversal depth (default 5).
        direction: ``"upstream"``, ``"downstream"``, or ``"both"``.

    Returns:
        TraceResult with nodes and edges.
    """
    if not db_path.exists():
        return TraceResult(root_object_id=object_id)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Load all objects for name/type lookup
    obj_rows = conn.execute(
        "SELECT id, type, name, source_file FROM objects"
    ).fetchall()
    obj_info: dict[str, dict[str, str | None]] = {
        row["id"]: {
            "type": row["type"],
            "name": row["name"],
            "source_file": row["source_file"],
        }
        for row in obj_rows
    }

    # Load all relationships
    rel_rows = conn.execute(
        "SELECT from_object_id, to_object_id, relationship_type, "
        "relationship_class FROM object_relationships"
    ).fetchall()

    outgoing: dict[str, list[tuple[str, str, str | None]]] = {}
    incoming: dict[str, list[tuple[str, str, str | None]]] = {}
    for from_id, to_id, rel_type, rel_class in rel_rows:
        outgoing.setdefault(from_id, []).append((to_id, rel_type, rel_class))
        incoming.setdefault(to_id, []).append((from_id, rel_type, rel_class))

    conn.close()

    root_info = obj_info.get(object_id, {})
    result = TraceResult(
        root_object_id=object_id,
        root_object_type=root_info.get("type"),
        root_object_name=root_info.get("name"),
    )

    visited: set[str] = {object_id}
    queue: list[tuple[str, int, str]] = [(object_id, 0, "root")]
    edge_set: set[tuple[str, str, str, str]] = set()

    while queue:
        current_id, depth, _ = queue.pop(0)
        if depth >= max_depth:
            continue

        if direction in ("downstream", "both"):
            for next_id, rel_type, rel_class in outgoing.get(current_id, []):
                if relationship_class and rel_class != relationship_class:
                    continue
                if next_id not in visited:
                    visited.add(next_id)
                    info = obj_info.get(next_id, {})
                    result.nodes.append(
                        TraceNode(
                            object_id=next_id,
                            object_type=info.get("type") or "Unknown",
                            object_name=info.get("name"),
                            source_file=info.get("source_file"),
                            depth=depth + 1,
                        )
                    )
                    queue.append((next_id, depth + 1, "downstream"))
                edge_key = (current_id, next_id, rel_type, "downstream")
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    result.edges.append(
                        TraceEdge(
                            from_object_id=current_id,
                            to_object_id=next_id,
                            relationship_type=rel_type,
                            direction="downstream",
                            relationship_class=rel_class,
                        )
                    )

        if direction in ("upstream", "both"):
            for prev_id, rel_type, rel_class in incoming.get(current_id, []):
                if relationship_class and rel_class != relationship_class:
                    continue
                if prev_id not in visited:
                    visited.add(prev_id)
                    info = obj_info.get(prev_id, {})
                    result.nodes.append(
                        TraceNode(
                            object_id=prev_id,
                            object_type=info.get("type") or "Unknown",
                            object_name=info.get("name"),
                            source_file=info.get("source_file"),
                            depth=depth + 1,
                        )
                    )
                    queue.append((prev_id, depth + 1, "upstream"))
                edge_key = (prev_id, current_id, rel_type, "upstream")
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    result.edges.append(
                        TraceEdge(
                            from_object_id=prev_id,
                            to_object_id=current_id,
                            relationship_type=rel_type,
                            direction="upstream",
                            relationship_class=rel_class,
                        )
                    )

    return result

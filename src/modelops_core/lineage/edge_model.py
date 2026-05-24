"""Lineage dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LineageNode:
    """A node in a lineage path."""

    object_id: str
    object_type: str
    name: str | None = None


@dataclass
class LineageEdge:
    """A directed edge in a lineage graph."""

    from_object_id: str
    to_object_id: str
    relationship_type: str


@dataclass
class LineagePath:
    """An ordered lineage path from source to target."""

    nodes: list[LineageNode] = field(default_factory=list)
    edges: list[LineageEdge] = field(default_factory=list)

"""Tests for lineage edge dataclass models."""

from __future__ import annotations

from modelops_core.lineage.edge_model import LineageEdge, LineageNode, LineagePath


class TestLineageNode:
    def test_defaults(self) -> None:
        node = LineageNode(object_id="A", object_type="Attribute")
        assert node.name is None

    def test_equality(self) -> None:
        a = LineageNode(object_id="A", object_type="Attribute", name="N")
        b = LineageNode(object_id="A", object_type="Attribute", name="N")
        assert a == b

    def test_mutability(self) -> None:
        node = LineageNode(object_id="A", object_type="Attribute")
        node.name = "Updated"
        assert node.name == "Updated"


class TestLineageEdge:
    def test_construction(self) -> None:
        edge = LineageEdge(from_object_id="A", to_object_id="B", relationship_type="has_field")
        assert edge.from_object_id == "A"
        assert edge.to_object_id == "B"


class TestLineagePath:
    def test_empty_defaults(self) -> None:
        path = LineagePath()
        assert path.nodes == []
        assert path.edges == []

    def test_append_nodes_and_edges(self) -> None:
        path = LineagePath()
        path.nodes.append(LineageNode(object_id="A", object_type="Attribute"))
        path.edges.append(
            LineageEdge(from_object_id="A", to_object_id="B", relationship_type="ref")
        )
        assert len(path.nodes) == 1
        assert len(path.edges) == 1

    def test_equality(self) -> None:
        a = LineagePath(nodes=[LineageNode(object_id="A", object_type="Attribute")])
        b = LineagePath(nodes=[LineageNode(object_id="A", object_type="Attribute")])
        assert a == b

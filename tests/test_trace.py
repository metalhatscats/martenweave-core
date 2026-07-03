"""Tests for trace service and CLI/API."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index import build_index
from modelops_core.trace import trace_object


def test_trace_object_upstream_and_downstream(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "FEP-S4-KNVV-KDGRP", max_depth=3, direction="both")
    assert result.root_object_id == "FEP-S4-KNVV-KDGRP"
    assert len(result.nodes) > 0

    # Check that we found the related attribute
    node_ids = {n.object_id for n in result.nodes}
    assert "ATTR-CUST-SALES-CUSTOMER-GROUP" in node_ids


def test_trace_object_downstream_only(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "DOMAIN-CUSTOMER-BP", max_depth=3, direction="downstream")
    assert all(e.direction == "downstream" for e in result.edges)


def test_trace_object_upstream_only(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "FEP-S4-KNVV-KDGRP", max_depth=3, direction="upstream")
    assert all(e.direction == "upstream" for e in result.edges)


def test_trace_object_no_index(temp_model_dir: Path) -> None:
    db_path = temp_model_dir.parent / "generated" / "modelops.db"
    result = trace_object(db_path, "DOMAIN-TEST", max_depth=3)
    assert result.root_object_id == "DOMAIN-TEST"
    assert len(result.nodes) == 0
    assert len(result.edges) == 0


def test_trace_nodes_have_metadata(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "ATTR-CUST-SALES-CUSTOMER-GROUP", max_depth=2)
    for n in result.nodes:
        assert n.object_type != "Unknown"
        assert n.depth > 0


def test_trace_object_filters_by_relationship_class(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    # Without filter: should find related objects
    result_all = trace_object(db_path, "DOMAIN-CUSTOMER-BP", max_depth=2, direction="both")
    assert len(result_all.nodes) > 0

    # With core_dependency filter: should still find domain-linked objects
    result_core = trace_object(
        db_path,
        "DOMAIN-CUSTOMER-BP",
        max_depth=2,
        direction="both",
        relationship_class="core_dependency",
    )
    assert len(result_core.nodes) > 0

    # With a non-matching class: should find nothing
    result_none = trace_object(
        db_path,
        "DOMAIN-CUSTOMER-BP",
        max_depth=2,
        direction="both",
        relationship_class="nonexistent",
    )
    assert len(result_none.nodes) == 0
    assert len(result_none.edges) == 0


def test_trace_edges_include_relationship_class(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "DOMAIN-CUSTOMER-BP", max_depth=2, direction="both")
    assert len(result.edges) > 0
    for edge in result.edges:
        assert edge.relationship_class is not None


def test_trace_upstream_property(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "FEP-S4-KNVV-KDGRP", max_depth=3, direction="both")
    assert result.root_object_id == "FEP-S4-KNVV-KDGRP"

    # upstream should not raise and should contain only non-root nodes
    upstream_nodes = result.upstream
    for n in upstream_nodes:
        assert n.depth > 0
        assert n.object_id != result.root_object_id

    # Every upstream node must be the source of at least one upstream edge
    upstream_ids = {n.object_id for n in upstream_nodes}
    for node_id in upstream_ids:
        assert any(e.direction == "upstream" and e.from_object_id == node_id for e in result.edges)


def test_trace_downstream_property(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "DOMAIN-CUSTOMER-BP", max_depth=3, direction="both")
    assert result.root_object_id == "DOMAIN-CUSTOMER-BP"

    downstream_nodes = result.downstream
    for n in downstream_nodes:
        assert n.depth > 0
        assert n.object_id != result.root_object_id

    # Every downstream node must have at least one downstream edge pointing to it
    downstream_ids = {n.object_id for n in downstream_nodes}
    for node_id in downstream_ids:
        assert any(e.direction == "downstream" and e.to_object_id == node_id for e in result.edges)


def test_trace_upstream_downstream_partition(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "FEP-S4-KNVV-KDGRP", max_depth=3, direction="both")
    upstream_ids = {n.object_id for n in result.upstream}
    downstream_ids = {n.object_id for n in result.downstream}

    # No overlap between upstream and downstream sets
    assert not upstream_ids & downstream_ids

    # Together they cover all non-root nodes
    non_root_ids = {n.object_id for n in result.nodes if n.depth > 0}
    assert upstream_ids | downstream_ids == non_root_ids


def test_trace_upstream_downstream_empty_when_no_index(temp_model_dir: Path) -> None:
    db_path = temp_model_dir.parent / "generated" / "modelops.db"
    result = trace_object(db_path, "DOMAIN-TEST", max_depth=3)
    assert result.upstream == []
    assert result.downstream == []


def test_trace_cli_unknown_object_id(sample_repo: Path) -> None:
    """CLI trace on an unknown ID must fail loudly instead of returning empty output."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["trace", "DOES-NOT-EXIST", "--repo", str(sample_repo)],
    )
    assert result.exit_code == 1
    assert "Object not found: DOES-NOT-EXIST" in result.output


def test_trace_cli_unknown_object_id_json(sample_repo: Path) -> None:
    """CLI trace --json on an unknown ID must include a structured error."""
    import json

    from typer.testing import CliRunner

    from modelops_core.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["trace", "DOES-NOT-EXIST", "--repo", str(sample_repo), "--json"],
    )
    assert result.exit_code == 1
    data = json.loads(result.output.strip())
    assert data["error"] == "Object not found: DOES-NOT-EXIST"

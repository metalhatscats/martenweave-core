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
    assert all(
        e.direction == "downstream"
        for e in result.edges
    )


def test_trace_object_upstream_only(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"

    result = trace_object(db_path, "FEP-S4-KNVV-KDGRP", max_depth=3, direction="upstream")
    assert all(
        e.direction == "upstream"
        for e in result.edges
    )


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

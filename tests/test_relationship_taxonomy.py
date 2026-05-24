"""Tests for relationship taxonomy and classification."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from modelops_core.index import build_index
from modelops_core.index.lineage_edges import export_lineage_jsonl
from modelops_core.schemas.registry import (
    get_relationship_classes,
    get_relationship_fields,
)

SIMPLE_REPO = Path(__file__).parent.parent / "examples" / "simple_product_model"


def test_relationship_fields_are_semantic() -> None:
    rels = get_relationship_fields()
    # Key relationships should use semantic names, not raw field names
    assert rels["domain"] == "belongs_to_domain"
    assert rels["attribute"] == "has_attribute"
    assert rels["business_attribute"] == "represents_attribute"
    assert rels["source_endpoint"] == "mapped_from"
    assert rels["target_endpoint"] == "mapped_to"
    assert rels["validation_rules"] == "validated_by"
    assert rels["business_owner"] == "owned_by_business"


def test_relationship_classes_are_set() -> None:
    classes = get_relationship_classes()
    assert classes["domain"] == "core_dependency"
    assert classes["source_endpoint"] == "mapping"
    assert classes["target_endpoint"] == "mapping"
    assert classes["validation_rules"] == "validation"
    assert classes["business_owner"] == "governance"
    assert classes["evidence"] == "evidence"


def test_index_includes_relationship_class() -> None:
    repo_root = SIMPLE_REPO
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root, db_path=db_path, export_jsonl=False)

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT relationship_type, relationship_class FROM object_relationships LIMIT 1"
        )
        row = cursor.fetchone()
        assert row is not None
        rel_type, rel_class = row
        assert rel_type
        assert rel_class in {
            "core_dependency",
            "context",
            "mapping",
            "validation",
            "governance",
            "evidence",
            "reference",
        }
    finally:
        conn.close()


def test_lineage_edges_export_includes_class() -> None:
    import json

    repo_root = SIMPLE_REPO
    db_path = repo_root / "generated" / "modelops.db"
    output_path = repo_root / "generated" / "lineage_edges_test.jsonl"

    build_index(repo_root, db_path=db_path, export_jsonl=False)
    export_lineage_jsonl(db_path, output_path)

    lines = output_path.read_text(encoding="utf-8").strip().split("\n")
    assert lines
    first = json.loads(lines[0])
    assert "relationship_class" in first
    assert first["relationship_class"] in {
        "core_dependency",
        "context",
        "mapping",
        "validation",
        "governance",
        "evidence",
        "reference",
    }


def test_trace_ignores_governance_edges_when_filtered() -> None:
    """Trace should be able to filter by relationship class in the future.

    This test documents the current behavior: all edges are traversed.
    When filtering is implemented, this test should be updated.
    """
    repo_root = SIMPLE_REPO
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root, db_path=db_path, export_jsonl=False)

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT DISTINCT relationship_class FROM object_relationships"
        ).fetchall()
        classes = {r[0] for r in rows}
        # Simple product model should have core_dependency and context edges
        assert "core_dependency" in classes
    finally:
        conn.close()

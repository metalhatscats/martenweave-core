"""Tests for relationship taxonomy and classification."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from modelops_core.index import build_index
from modelops_core.index.lineage_edges import export_lineage_jsonl
from modelops_core.schemas.common import ObjectType
from modelops_core.schemas.registry import (
    get_all_types,
    get_entry,
    get_expected_target_types,
    get_reference_fields,
    get_relationship_classes,
    get_relationship_fields,
    get_search_fields,
    get_ui_label,
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


# Registry coverage tests (issue #331) ----------------------------------------


def test_every_object_type_has_registry_entry() -> None:
    """Every ObjectType enum member must have a corresponding registry entry."""
    registered_types = set(get_all_types())
    for member in ObjectType:
        assert member.value in registered_types, (
            f"ObjectType '{member.value}' lacks a registry entry"
        )


def test_every_registry_entry_has_non_empty_labels() -> None:
    """Each registry entry must have non-empty singular and plural labels."""
    for member in ObjectType:
        entry = get_entry(member.value)
        assert entry is not None, f"Missing registry entry for {member.value}"
        assert entry.ui_label_singular and entry.ui_label_singular.strip(), (
            f"Empty ui_label_singular for {member.value}"
        )
        assert entry.ui_label_plural and entry.ui_label_plural.strip(), (
            f"Empty ui_label_plural for {member.value}"
        )


def test_registry_helpers_return_sane_defaults_for_all_types() -> None:
    """Registry helper APIs must return sensible defaults for every ObjectType."""
    for member in ObjectType:
        type_id = member.value

        # get_ui_label should return a non-empty string for registered types
        singular = get_ui_label(type_id, plural=False)
        plural = get_ui_label(type_id, plural=True)
        assert singular and singular.strip()
        assert plural and plural.strip()

        # get_reference_fields should return a dict (may be empty)
        refs = get_reference_fields(type_id)
        assert isinstance(refs, dict)

        # get_relationship_fields should return a dict (may be empty)
        rels = get_relationship_fields(type_id)
        assert isinstance(rels, dict)
        for field_name, rel_type in rels.items():
            assert rel_type and rel_type.strip(), (
                f"Empty relationship_type for field '{field_name}' in {type_id}"
            )

        # get_relationship_classes should return a dict (may be empty)
        classes = get_relationship_classes(type_id)
        assert isinstance(classes, dict)
        for _field_name, rel_class in classes.items():
            assert rel_class in {
                "core_dependency",
                "context",
                "mapping",
                "validation",
                "governance",
                "evidence",
                "reference",
            }, f"Unexpected relationship_class '{rel_class}' for {type_id}"

        # get_expected_target_types should return a dict (may be empty)
        targets = get_expected_target_types(type_id)
        assert isinstance(targets, dict)

        # get_search_fields should return a non-empty tuple
        search_fields = get_search_fields(type_id)
        assert isinstance(search_fields, tuple)
        assert len(search_fields) > 0, f"Empty search_fields for {type_id}"

"""Tests for system lineage object types and relationships."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.schemas.registry import (
    get_entry,
    get_expected_target_types,
    get_relationship_fields,
)

# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "type_name",
    [
        "Application",
        "InterfaceEndpoint",
        "IntegrationFlow",
        "DataFlowStep",
        "TransformationRule",
    ],
)
def test_system_lineage_types_registered(type_name: str) -> None:
    entry = get_entry(type_name)
    assert entry is not None
    assert entry.type_id == type_name


@pytest.mark.parametrize(
    "type_name, expected_field, expected_rel, expected_target",
    [
        ("IntegrationFlow", "source_system", "flows_from", "System"),
        ("IntegrationFlow", "target_system", "flows_to", "System"),
        ("IntegrationFlow", "interface", "part_of_interface", "Interface"),
        ("DataFlowStep", "integration_flow", "part_of_flow", "IntegrationFlow"),
        ("DataFlowStep", "source_step", "preceded_by", "DataFlowStep"),
        ("DataFlowStep", "target_step", "followed_by", "DataFlowStep"),
        ("DataFlowStep", "transformation_rule", "applies_transformation", "TransformationRule"),
        ("TransformationRule", "source_field_endpoint", "reads_from", "FieldEndpoint"),
        ("TransformationRule", "target_field_endpoint", "writes_to", "FieldEndpoint"),
        ("InterfaceEndpoint", "interface", "part_of_interface", "Interface"),
        ("InterfaceEndpoint", "application", "used_by_application", "Application"),
        ("Application", "system", "located_in_system", "System"),
    ],
)
def test_system_lineage_reference_fields(
    type_name: str, expected_field: str, expected_rel: str, expected_target: str | None
) -> None:
    rels = get_relationship_fields(type_name)
    targets = get_expected_target_types(type_name)
    assert rels.get(expected_field) == expected_rel
    assert targets.get(expected_field) == expected_target


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_validate_system_lineage_objects(tmp_path: Path) -> None:
    from modelops_core.repository.parser import ParsedObject
    from modelops_core.validation import validate_objects

    objects = [
        ParsedObject(
            source_path="SYSTEM-TEST.md",
            content_hash="abc",
            frontmatter={"id": "SYSTEM-TEST", "type": "System", "status": "active", "name": "Test"},
            body=None,
            parser_error=None,
        ),
        ParsedObject(
            source_path="FLOW-TEST.md",
            content_hash="abc",
            frontmatter={
                "id": "FLOW-TEST",
                "type": "IntegrationFlow",
                "status": "draft",
                "name": "Test Flow",
                "source_system": "SYSTEM-TEST",
            },
            body=None,
            parser_error=None,
        ),
        ParsedObject(
            source_path="STEP-TEST.md",
            content_hash="abc",
            frontmatter={
                "id": "STEP-TEST",
                "type": "DataFlowStep",
                "status": "draft",
                "name": "Test Step",
                "integration_flow": "FLOW-TEST",
            },
            body=None,
            parser_error=None,
        ),
        ParsedObject(
            source_path="TRULE-TEST.md",
            content_hash="abc",
            frontmatter={
                "id": "TRULE-TEST",
                "type": "TransformationRule",
                "status": "draft",
                "name": "Test Rule",
            },
            body=None,
            parser_error=None,
        ),
        ParsedObject(
            source_path="APP-TEST.md",
            content_hash="abc",
            frontmatter={
                "id": "APP-TEST",
                "type": "Application",
                "status": "active",
                "name": "Test App",
            },
            body=None,
            parser_error=None,
        ),
        ParsedObject(
            source_path="IEP-TEST.md",
            content_hash="abc",
            frontmatter={
                "id": "IEP-TEST",
                "type": "InterfaceEndpoint",
                "status": "active",
                "name": "Test Endpoint",
            },
            body=None,
            parser_error=None,
        ),
    ]

    summary = validate_objects(objects)
    assert summary.error_count == 0
    assert summary.is_valid is True


# ---------------------------------------------------------------------------
# Index / lineage edge tests
# ---------------------------------------------------------------------------


def test_index_generates_system_lineage_edges(tmp_path: Path) -> None:
    from modelops_core.index.sqlite_builder import build_index

    repo_root = tmp_path / "repo"
    model_path = repo_root / "model"
    model_path.mkdir(parents=True)

    (model_path / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: active\n"
        "name: Test Domain\n"
        "---\n\n# Test Domain\n",
        encoding="utf-8",
    )
    (model_path / "SYSTEM-A.md").write_text(
        "---\n"
        "id: SYSTEM-A\n"
        "type: System\n"
        "status: active\n"
        "name: System A\n"
        "domain: DOMAIN-TEST\n"
        "---\n\n# System A\n",
        encoding="utf-8",
    )
    (model_path / "FLOW-A.md").write_text(
        "---\n"
        "id: FLOW-A\n"
        "type: IntegrationFlow\n"
        "status: active\n"
        "name: Flow A\n"
        "domain: DOMAIN-TEST\n"
        "source_system: SYSTEM-A\n"
        "---\n\n# Flow A\n",
        encoding="utf-8",
    )

    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT relationship_type, to_object_id FROM object_relationships WHERE from_object_id = ?",
        ("FLOW-A",),
    ).fetchall()
    conn.close()

    rels = {row["relationship_type"]: row["to_object_id"] for row in rows}
    assert rels.get("flows_from") == "SYSTEM-A"


# ---------------------------------------------------------------------------
# Trace / impact compatibility tests
# ---------------------------------------------------------------------------


def test_trace_includes_system_lineage_nodes(tmp_path: Path) -> None:
    from modelops_core.index.sqlite_builder import build_index
    from modelops_core.trace.trace_service import trace_object

    repo_root = tmp_path / "repo"
    model_path = repo_root / "model"
    model_path.mkdir(parents=True)

    (model_path / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: active\n"
        "name: Test Domain\n"
        "---\n\n# Test Domain\n",
        encoding="utf-8",
    )
    (model_path / "SYSTEM-A.md").write_text(
        "---\n"
        "id: SYSTEM-A\n"
        "type: System\n"
        "status: active\n"
        "name: System A\n"
        "domain: DOMAIN-TEST\n"
        "---\n\n# System A\n",
        encoding="utf-8",
    )
    (model_path / "FLOW-A.md").write_text(
        "---\n"
        "id: FLOW-A\n"
        "type: IntegrationFlow\n"
        "status: active\n"
        "name: Flow A\n"
        "domain: DOMAIN-TEST\n"
        "source_system: SYSTEM-A\n"
        "---\n\n# Flow A\n",
        encoding="utf-8",
    )

    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    result = trace_object(db_path, "SYSTEM-A", max_depth=2, direction="both")
    node_ids = {n.object_id for n in result.nodes}
    assert "FLOW-A" in node_ids

    edge_pairs = {(e.from_object_id, e.to_object_id) for e in result.edges}
    assert ("FLOW-A", "SYSTEM-A") in edge_pairs

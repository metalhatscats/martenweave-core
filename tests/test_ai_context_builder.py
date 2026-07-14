"""Tests for AI context builder (task 1.3)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest import mock

import pytest

from modelops_core.ai.context_builder import (
    ContextBundle,
    _compact_objects,
    build_context_bundle,
)
from modelops_core.trace.trace_service import TraceEdge, TraceNode, TraceResult


def _init_test_db(
    db_path: Path,
    objects: list[dict],
    relationships: list[dict] | None = None,
    validation_results: list[dict] | None = None,
) -> None:
    """Create a minimal SQLite index for context builder tests."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS objects (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            name TEXT,
            title TEXT,
            domain TEXT,
            description TEXT,
            source_file TEXT NOT NULL,
            content_hash TEXT NOT NULL DEFAULT '',
            frontmatter_json TEXT NOT NULL DEFAULT '{}',
            body TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS validation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            severity TEXT NOT NULL,
            code TEXT NOT NULL,
            message TEXT NOT NULL,
            object_id TEXT,
            object_type TEXT,
            source_file TEXT,
            field_path TEXT,
            details_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS object_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_object_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            relationship_class TEXT NOT NULL DEFAULT 'reference',
            to_object_id TEXT NOT NULL,
            source_file TEXT NOT NULL,
            confidence TEXT NOT NULL DEFAULT 'explicit'
        );
        """
    )
    obj_sql = (
        "INSERT OR REPLACE INTO objects "
        "(id, type, status, name, title, domain, description, source_file, frontmatter_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    for obj in objects:
        conn.execute(
            obj_sql,
            (
                obj["id"],
                obj["type"],
                obj.get("status", "draft"),
                obj.get("name"),
                obj.get("title"),
                obj.get("domain"),
                obj.get("description"),
                obj.get("source_file", f"model/{obj['id']}.md"),
                json.dumps(obj.get("frontmatter", {}), default=str),
            ),
        )
    rel_sql = (
        "INSERT INTO object_relationships "
        "(from_object_id, relationship_type, relationship_class, to_object_id, source_file) "
        "VALUES (?, ?, ?, ?, ?)"
    )
    for rel in relationships or []:
        conn.execute(
            rel_sql,
            (
                rel["from"],
                rel["type"],
                rel.get("class", "reference"),
                rel["to"],
                rel.get("source_file", "model/test.md"),
            ),
        )
    val_sql = (
        "INSERT INTO validation_results "
        "(severity, code, message, object_id, object_type, source_file, field_path, details_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    for vr in validation_results or []:
        conn.execute(
            val_sql,
            (
                vr["severity"],
                vr["code"],
                vr["message"],
                vr.get("object_id"),
                vr.get("object_type", ""),
                vr.get("source_file", ""),
                vr.get("field_path", ""),
                json.dumps(vr.get("details", {})),
            ),
        )
    conn.commit()
    conn.close()


@pytest.fixture
def trace_result_factory():
    """Factory for TraceResult objects."""

    def _factory(root_id: str, nodes: list[dict] | None = None, edges: list[dict] | None = None):
        return TraceResult(
            root_object_id=root_id,
            nodes=[TraceNode(**n) for n in (nodes or [])],
            edges=[TraceEdge(**e) for e in (edges or [])],
        )

    return _factory


class TestSingleTracePerSeed:
    def test_trace_object_called_once_per_seed(self, tmp_path: Path, trace_result_factory) -> None:
        db_path = tmp_path / "generated" / "modelops.db"
        _init_test_db(
            db_path,
            objects=[
                {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
                {"id": "FEP-1", "type": "FieldEndpoint", "status": "active", "name": "F1"},
            ],
            relationships=[{"from": "ATTR-1", "to": "FEP-1", "type": "has_attribute"}],
        )

        trace_result = trace_result_factory(
            root_id="ATTR-1",
            nodes=[
                {"object_id": "FEP-1", "object_type": "FieldEndpoint", "object_name": "F1"},
            ],
            edges=[
                {
                    "from_object_id": "ATTR-1",
                    "to_object_id": "FEP-1",
                    "relationship_type": "has_attribute",
                    "direction": "downstream",
                },
            ],
        )

        call_count = 0
        original_trace = None

        def fake_trace(db_path_arg, object_id, **kwargs):
            nonlocal call_count, original_trace
            call_count += 1
            # Return the trace result only for ATTR-1; empty for others
            if object_id == "ATTR-1":
                return trace_result
            return trace_result_factory(root_id=object_id)

        with mock.patch(
            "modelops_core.ai.context_builder.trace_object", side_effect=fake_trace
        ) as mock_trace:
            bundle = build_context_bundle(
                db_path=db_path,
                workflow="chat-to-model",
                target_object_id="ATTR-1",
                target_object_ids=["FEP-1"],
                max_depth=2,
            )

        assert mock_trace.call_count == 2  # once per seed
        seed_ids = {call.args[1] for call in mock_trace.call_args_list}
        assert seed_ids == {"ATTR-1", "FEP-1"}

        # Both nodes and edges are derived from the single trace result
        assert any(o["object_id"] == "FEP-1" for o in bundle.included_objects)
        assert any(
            r["from_object_id"] == "ATTR-1" and r["to_object_id"] == "FEP-1"
            for r in bundle.relationship_refs
        )

    def test_nodes_and_edges_from_single_trace(self, tmp_path: Path, trace_result_factory) -> None:
        db_path = tmp_path / "generated" / "modelops.db"
        _init_test_db(
            db_path,
            objects=[
                {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
                {"id": "FEP-1", "type": "FieldEndpoint", "status": "active", "name": "F1"},
                {"id": "FEP-2", "type": "FieldEndpoint", "status": "active", "name": "F2"},
            ],
            relationships=[
                {"from": "ATTR-1", "to": "FEP-1", "type": "has_attribute"},
                {"from": "ATTR-1", "to": "FEP-2", "type": "has_attribute"},
            ],
        )

        trace_result = trace_result_factory(
            root_id="ATTR-1",
            nodes=[
                {"object_id": "FEP-1", "object_type": "FieldEndpoint", "object_name": "F1"},
                {"object_id": "FEP-2", "object_type": "FieldEndpoint", "object_name": "F2"},
            ],
            edges=[
                {
                    "from_object_id": "ATTR-1",
                    "to_object_id": "FEP-1",
                    "relationship_type": "has_attribute",
                    "direction": "downstream",
                },
                {
                    "from_object_id": "ATTR-1",
                    "to_object_id": "FEP-2",
                    "relationship_type": "has_attribute",
                    "direction": "downstream",
                },
            ],
        )

        with mock.patch(
            "modelops_core.ai.context_builder.trace_object", return_value=trace_result
        ) as mock_trace:
            bundle = build_context_bundle(
                db_path=db_path,
                workflow="chat-to-model",
                target_object_id="ATTR-1",
                max_depth=2,
            )

        assert mock_trace.call_count == 1
        assert len(bundle.included_objects) == 3
        assert len(bundle.relationship_refs) == 2


class TestCompactObjectsPriority:
    def test_validation_errors_priority(self) -> None:
        objects = [
            {"object_id": "ATTR-1", "object_type": "Attribute"},
            {"object_id": "ATTR-2", "object_type": "Attribute"},
            {"object_id": "ATTR-3", "object_type": "Attribute"},
        ]
        validation_summary = {
            "errors": 1,
            "warnings": 0,
            "details": [
                {
                    "severity": "ERROR",
                    "code": "TEST-1",
                    "message": "Error",
                    "object_id": "ATTR-2",
                },
            ],
        }
        kept, _ = _compact_objects(objects, max_objects=2, validation_summary=validation_summary)
        assert kept[0]["object_id"] == "ATTR-2"

    def test_same_type_priority_without_errors(self) -> None:
        objects = [
            {"object_id": "ATTR-1", "object_type": "Attribute"},
            {"object_id": "ATTR-2", "object_type": "Attribute"},
        ]
        kept, _ = _compact_objects(objects, max_objects=2, validation_summary=None)
        assert len(kept) == 2


class TestIncludedSourcesRedacted:
    def test_includes_redacted_source_metadata(self, tmp_path: Path, trace_result_factory) -> None:
        db_path = tmp_path / "generated" / "modelops.db"
        _init_test_db(
            db_path,
            objects=[
                {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
                {"id": "DS-1", "type": "Dataset", "status": "active", "name": "Dataset 1"},
            ],
            relationships=[{"from": "ATTR-1", "to": "DS-1", "type": "sourced_from"}],
        )

        # Register a dataset profile source in the registry
        registry_path = db_path.parent / "source_registry.jsonl"
        source_entry = {
            "source_id": "DS-1",
            "source_type": "dataset_profile",
            "display_name": "Dataset profile: DS-1",
            "file_path": str(tmp_path / "data" / "sample.csv"),
            "file_hash": "abc123",
            "registered_at": "2024-01-01T00:00:00Z",
            "last_seen_at": "2024-01-01T00:00:00Z",
            "status": "ok",
            "metadata": {
                "row_count": 100,
                "column_count": 5,
                "inferred_types": ["string", "integer"],
            },
        }
        registry_path.write_text(json.dumps(source_entry) + "\n", encoding="utf-8")

        trace_result = trace_result_factory(
            root_id="ATTR-1",
            nodes=[{"object_id": "DS-1", "object_type": "Dataset", "object_name": "Dataset 1"}],
            edges=[
                {
                    "from_object_id": "ATTR-1",
                    "to_object_id": "DS-1",
                    "relationship_type": "sourced_from",
                    "direction": "downstream",
                },
            ],
        )

        with mock.patch(
            "modelops_core.ai.context_builder.trace_object", return_value=trace_result
        ):
            bundle = build_context_bundle(
                db_path=db_path,
                workflow="chat-to-model",
                target_object_id="ATTR-1",
                redaction_policy="metadata_with_counts",
                max_depth=2,
            )

        assert len(bundle.included_sources) == 1
        source = bundle.included_sources[0]
        assert source["source_id"] == "DS-1"
        assert source["dataset_id"] == "DS-1"
        assert source["row_count"] == 100
        assert source["column_count"] == 5
        assert source["inferred_types"] == ["string", "integer"]
        # Never include raw samples
        assert "sample_values" not in source
        assert "samples" not in source

    def test_summary_only_excludes_sources(self, tmp_path: Path, trace_result_factory) -> None:
        db_path = tmp_path / "generated" / "modelops.db"
        _init_test_db(
            db_path,
            objects=[
                {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
                {"id": "DS-1", "type": "Dataset", "status": "active", "name": "Dataset 1"},
            ],
            relationships=[{"from": "ATTR-1", "to": "DS-1", "type": "sourced_from"}],
        )

        registry_path = db_path.parent / "source_registry.jsonl"
        source_entry = {
            "source_id": "DS-1",
            "source_type": "dataset_profile",
            "display_name": "Dataset profile: DS-1",
            "file_path": str(tmp_path / "data" / "sample.csv"),
            "file_hash": "abc123",
            "registered_at": "2024-01-01T00:00:00Z",
            "last_seen_at": "2024-01-01T00:00:00Z",
            "status": "ok",
            "metadata": {"row_count": 100, "column_count": 5},
        }
        registry_path.write_text(json.dumps(source_entry) + "\n", encoding="utf-8")

        trace_result = trace_result_factory(
            root_id="ATTR-1",
            nodes=[{"object_id": "DS-1", "object_type": "Dataset", "object_name": "Dataset 1"}],
            edges=[
                {
                    "from_object_id": "ATTR-1",
                    "to_object_id": "DS-1",
                    "relationship_type": "sourced_from",
                    "direction": "downstream",
                },
            ],
        )

        with mock.patch(
            "modelops_core.ai.context_builder.trace_object", return_value=trace_result
        ):
            bundle = build_context_bundle(
                db_path=db_path,
                workflow="chat-to-model",
                target_object_id="ATTR-1",
                redaction_policy="summary_only",
                max_depth=2,
            )

        assert bundle.included_sources == []


class TestOversizedBundleSummaryFallback:
    def test_returns_summary_only_when_over_budget(
        self, tmp_path: Path, trace_result_factory
    ) -> None:
        db_path = tmp_path / "generated" / "modelops.db"
        # Create many large objects to force the summary fallback
        objects = []
        for i in range(50):
            objects.append(
                {
                    "id": f"ATTR-{i:03d}",
                    "type": "Attribute",
                    "status": "active",
                    "name": f"Attribute {i}",
                    "description": "x" * 500,
                }
            )
        _init_test_db(db_path, objects=objects)

        trace_nodes = [
            {
                "object_id": f"ATTR-{i:03d}",
                "object_type": "Attribute",
                "object_name": f"A{i}",
            }
            for i in range(1, 50)
        ]
        trace_result = trace_result_factory(
            root_id="ATTR-000",
            nodes=trace_nodes,
            edges=[],
        )

        with mock.patch(
            "modelops_core.ai.context_builder.trace_object", return_value=trace_result
        ):
            bundle = build_context_bundle(
                db_path=db_path,
                workflow="chat-to-model",
                target_object_id="ATTR-000",
                token_budget=100,
                max_objects=100,
                max_depth=2,
            )

        assert any("summary only" in str(w).lower() for w in bundle.warnings)
        assert len(bundle.included_objects) <= 20
        for obj in bundle.included_objects:
            assert set(obj.keys()) <= {"object_id", "object_type", "name"}
        assert bundle.relationship_refs == []


class TestContextBundle:
    def test_bundle_metadata(self) -> None:
        bundle = ContextBundle(bundle_id="test", workflow="chat-to-model")
        meta = bundle.to_metadata()
        assert meta["bundle_id"] == "test"
        assert meta["workflow"] == "chat-to-model"
        assert meta["object_count"] == 0
        assert meta["relationship_count"] == 0

    def test_empty_bundle_when_db_missing(self, tmp_path: Path) -> None:
        db_path = tmp_path / "missing.db"
        bundle = build_context_bundle(db_path=db_path, workflow="chat-to-model")
        assert "not found" in str(bundle.warnings[0]).lower()
        assert bundle.included_objects == []

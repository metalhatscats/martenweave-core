"""Tests for query and search over the generated index."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.index.query_service import (
    get_object_by_id,
    list_related_objects,
    query_objects,
    search_objects,
)

runner = CliRunner()


def _build_index(db_path: Path) -> None:
    """Create a minimal SQLite index for testing."""
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE objects (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            name TEXT,
            title TEXT,
            domain TEXT,
            description TEXT,
            source_file TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            frontmatter_json TEXT NOT NULL,
            body TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE object_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_object_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            relationship_class TEXT NOT NULL DEFAULT 'reference',
            to_object_id TEXT NOT NULL,
            source_file TEXT NOT NULL,
            confidence TEXT NOT NULL DEFAULT 'explicit'
        );
        CREATE TABLE tags (
            object_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (object_id, tag)
        );
        """
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-001",
            "Attribute",
            "active",
            "Customer Group",
            "Customer Group Title",
            "DOMAIN-A",
            "Sales-area-dependent customer grouping",
            "model/ATTR-001.md",
            "abc",
            '{"id": "ATTR-001", "type": "Attribute", "tags": ["customer", "sales"]}',
            "# Customer Group\n\nBody text here.",
            None,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-001",
            "FieldEndpoint",
            "active",
            "KNVV KDGRP",
            None,
            "DOMAIN-A",
            "SAP field for customer group",
            "model/FEP-001.md",
            "def",
            '{"id": "FEP-001", "type": "FieldEndpoint", "tags": ["customer"], "sap_table": "KNVV"}',
            "# KNVV KDGRP",
            None,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-002",
            "FieldEndpoint",
            "active",
            "BUT000 NAME",
            None,
            "DOMAIN-A",
            "SAP field for name",
            "model/FEP-002.md",
            "def",
            '{"id": "FEP-002", "type": "FieldEndpoint", "sap_table": "BUT000"}',
            "# BUT000 NAME",
            None,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "VLIST-002",
            "ValueList",
            "active",
            "Owned List",
            None,
            None,
            None,
            "model/VLIST-002.md",
            "ghi",
            '{"id": "VLIST-002", "type": "ValueList", "business_owner": "PERSON-001"}',
            None,
            None,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "VLIST-001",
            "ValueList",
            "draft",
            "Customer Groups",
            None,
            None,
            None,
            "model/VLIST-001.md",
            "ghi",
            '{"id": "VLIST-001", "type": "ValueList"}',
            None,
            None,
            None,
        ),
    )
    conn.execute("INSERT INTO tags VALUES (?, ?)", ("ATTR-001", "customer"))
    conn.execute("INSERT INTO tags VALUES (?, ?)", ("ATTR-001", "sales"))
    conn.execute("INSERT INTO tags VALUES (?, ?)", ("FEP-001", "customer"))
    conn.execute(
        "INSERT INTO object_relationships "
        "(from_object_id, relationship_type, to_object_id, source_file) "
        "VALUES (?, ?, ?, ?)",
        ("ATTR-001", "has_field", "FEP-001", "model/ATTR-001.md"),
    )
    conn.commit()
    conn.close()


class TestSearchObjects:
    def test_search_by_name(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer Group")
        assert len(results) == 3
        # Best match first (score 4)
        assert results[0].object_id == "ATTR-001"
        assert "name" in results[0].matched_fields

    def test_search_by_body(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Body text")
        assert len(results) == 1
        assert results[0].object_id == "ATTR-001"
        assert "body" in results[0].matched_fields

    def test_search_with_type_filter(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer", object_type="FieldEndpoint")
        assert len(results) == 1
        assert results[0].object_id == "FEP-001"

    def test_search_no_results(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "nonexistent")
        assert results == []

    def test_search_missing_db(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        results = search_objects(db, "test")
        assert results == []

    def test_search_limit(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "a", limit=1)
        assert len(results) == 1

    def test_search_offset(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        # "Customer" matches ATTR-001, FEP-001, FEP-002 (3 results)
        # Score order: ATTR-001 (name+description), FEP-001 (description), FEP-002 (description)
        all_results = search_objects(db, "Customer")
        assert len(all_results) == 3
        offset_results = search_objects(db, "Customer", offset=1)
        assert len(offset_results) == 2
        assert offset_results[0].object_id == all_results[1].object_id

    def test_search_limit_offset(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        all_results = search_objects(db, "Customer")
        assert len(all_results) == 3
        results = search_objects(db, "Customer", limit=1, offset=1)
        assert len(results) == 1
        assert results[0].object_id == all_results[1].object_id

    def test_search_offset_beyond_results(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer", offset=10)
        assert results == []

    def test_search_scores_sorted(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_with_tag_filter(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer", tags=["sales"])
        assert len(results) == 1
        assert results[0].object_id == "ATTR-001"

    def test_search_with_multiple_tags(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer", tags=["customer", "sales"])
        assert len(results) == 2

    def test_search_tag_no_match(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer", tags=["nonexistent"])
        assert results == []


class TestQueryObjects:
    def test_query_by_type(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, object_type="FieldEndpoint")
        assert len(results) == 2
        assert any(r.object_id == "FEP-001" for r in results)

    def test_query_by_status(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, status="draft")
        assert len(results) == 1
        assert results[0].object_id == "VLIST-001"

    def test_query_by_domain(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, domain="DOMAIN-A")
        assert len(results) == 3

    def test_query_name_like(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, name_like="Group")
        assert len(results) == 2

    def test_query_combined_filters(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, object_type="Attribute", domain="DOMAIN-A")
        assert len(results) == 1
        assert results[0].object_id == "ATTR-001"

    def test_query_no_results(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, object_type="Nonexistent")
        assert results == []

    def test_query_missing_db(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        results = query_objects(db, object_type="Attribute")
        assert results == []

    def test_query_offset(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        all_results = query_objects(db, object_type="FieldEndpoint")
        assert len(all_results) == 2
        offset_results = query_objects(db, object_type="FieldEndpoint", offset=1)
        assert len(offset_results) == 1
        assert offset_results[0].object_id in {r.object_id for r in all_results}

    def test_query_limit_offset(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        all_results = query_objects(db, domain="DOMAIN-A")
        assert len(all_results) == 3
        results = query_objects(db, domain="DOMAIN-A", limit=1, offset=1)
        assert len(results) == 1
        assert results[0].object_id in {r.object_id for r in all_results}

    def test_query_offset_beyond_results(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, object_type="Attribute", offset=10)
        assert results == []

    def test_query_by_tag(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, tags=["sales"])
        assert len(results) == 1
        assert results[0].object_id == "ATTR-001"

    def test_query_by_multiple_tags(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, tags=["customer"])
        assert len(results) == 2

    def test_query_tag_combined_with_type(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, object_type="FieldEndpoint", tags=["customer"])
        assert len(results) == 1
        assert results[0].object_id == "FEP-001"


class TestGetObjectById:
    def test_found(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        obj = get_object_by_id(db, "ATTR-001")
        assert obj is not None
        assert obj["id"] == "ATTR-001"

    def test_not_found(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        assert get_object_by_id(db, "MISSING") is None

    def test_missing_db(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        assert get_object_by_id(db, "ATTR-001") is None


class TestListRelatedObjects:
    def test_related(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        rels = list_related_objects(db, "ATTR-001")
        assert len(rels) == 1
        assert rels[0]["to_object_id"] == "FEP-001"

    def test_filtered_by_type(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        rels = list_related_objects(db, "ATTR-001", relationship_type="has_field")
        assert len(rels) == 1

    def test_no_relationships(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        rels = list_related_objects(db, "FEP-001")
        assert rels == []

    def test_missing_db(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        rels = list_related_objects(db, "ATTR-001")
        assert rels == []


    def test_query_by_owner(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, owner="PERSON-001")
        assert len(results) == 1
        assert results[0].object_id == "VLIST-002"

    def test_query_by_sap_table(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, sap_table="KNVV")
        assert len(results) == 1
        assert results[0].object_id == "FEP-001"

    def test_query_combined_owner_and_type(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, object_type="ValueList", owner="PERSON-001")
        assert len(results) == 1
        assert results[0].object_id == "VLIST-002"

    def test_query_owner_no_match(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, owner="UNKNOWN")
        assert results == []

    def test_query_sap_table_no_match(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, sap_table="NONEXISTENT")
        assert results == []


class TestJsonContract:
    def test_search_result_fields_present(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer")
        assert len(results) > 0
        for r in results:
            assert isinstance(r.object_id, str)
            assert isinstance(r.object_type, str)
            assert isinstance(r.status, str)
            assert r.name is None or isinstance(r.name, str)
            assert r.title is None or isinstance(r.title, str)
            assert r.domain is None or isinstance(r.domain, str)
            assert isinstance(r.source_file, str)
            assert isinstance(r.score, (int, float))
            assert isinstance(r.matched_fields, list)

    def test_query_result_fields_consistent(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)

        # Run multiple queries with different filters
        queries = [
            query_objects(db, object_type="Attribute"),
            query_objects(db, status="active"),
            query_objects(db, domain="DOMAIN-A"),
            query_objects(db, name_like="Group"),
            query_objects(db, tags=["customer"]),
            query_objects(db, owner="PERSON-001"),
            query_objects(db, sap_table="KNVV"),
        ]

        for results in queries:
            for r in results:
                assert isinstance(r.object_id, str)
                assert isinstance(r.object_type, str)
                assert isinstance(r.status, str)
                assert r.name is None or isinstance(r.name, str)
                assert r.title is None or isinstance(r.title, str)
                assert r.domain is None or isinstance(r.domain, str)
                assert isinstance(r.source_file, str)

    def test_empty_results_are_lists(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        assert search_objects(db, "nonexistent_xyz") == []
        assert query_objects(db, object_type="Nonexistent") == []
        assert query_objects(db, owner="UNKNOWN") == []
        assert query_objects(db, sap_table="UNKNOWN") == []

    def test_search_scores_sorted_descending(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_cli_query_json_roundtrip(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        generated = repo / "generated"
        generated.mkdir()
        db = generated / "modelops.db"
        _build_index(db)

        result = runner.invoke(
            app, ["query", "--repo", str(repo), "--type", "Attribute", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert "results" in data
        assert "total_count" in data
        assert len(data["results"]) >= 1
        assert "object_id" in data["results"][0]
        assert "object_type" in data["results"][0]
        assert "status" in data["results"][0]

    def test_cli_search_json_roundtrip(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        generated = repo / "generated"
        generated.mkdir()
        db = generated / "modelops.db"
        _build_index(db)

        result = runner.invoke(
            app, ["search", "Customer", "--repo", str(repo), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert "results" in data
        assert "total_count" in data
        assert len(data["results"]) >= 1
        assert "object_id" in data["results"][0]
        assert "score" in data["results"][0]
        assert "matched_fields" in data["results"][0]


class TestFilterCombinations:
    def test_type_plus_status(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, object_type="FieldEndpoint", status="active")
        assert len(results) == 2
        for r in results:
            assert r.object_type == "FieldEndpoint"
            assert r.status == "active"

    def test_domain_plus_owner(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, domain="DOMAIN-A", owner="PERSON-001")
        # No object in DOMAIN-A has owner PERSON-001
        assert results == []

    def test_tags_plus_name_like(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, tags=["customer"], name_like="Group")
        assert len(results) == 1
        assert results[0].object_id == "ATTR-001"

    def test_sap_table_plus_type(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, sap_table="KNVV", object_type="FieldEndpoint")
        assert len(results) == 1
        assert results[0].object_id == "FEP-001"

    def test_all_filters_together(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(
            db,
            object_type="FieldEndpoint",
            status="active",
            domain="DOMAIN-A",
            sap_table="KNVV",
        )
        assert len(results) == 1
        assert results[0].object_id == "FEP-001"

    def test_all_filters_no_match(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(
            db,
            object_type="FieldEndpoint",
            status="active",
            domain="DOMAIN-A",
            sap_table="NONEXISTENT",
        )
        assert results == []

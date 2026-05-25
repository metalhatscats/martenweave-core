"""Tests for query and search over the generated index."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index.query_service import (
    get_object_by_id,
    list_related_objects,
    query_objects,
    search_objects,
)


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
            body TEXT
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
        """
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            '{"id": "ATTR-001", "type": "Attribute"}',
            "# Customer Group\n\nBody text here.",
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            '{"id": "FEP-001", "type": "FieldEndpoint"}',
            "# KNVV KDGRP",
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
        ),
    )
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

    def test_search_scores_sorted(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = search_objects(db, "Customer")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


class TestQueryObjects:
    def test_query_by_type(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        _build_index(db)
        results = query_objects(db, object_type="FieldEndpoint")
        assert len(results) == 1
        assert results[0].object_id == "FEP-001"

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
        assert len(results) == 2

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

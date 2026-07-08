"""Tests for the local-first semantic search index."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from modelops_core.index.semantic_search import (
    SemanticIndexBuilder,
    SemanticSearcher,
    _compute_idf,
    _cosine_similarity,
    _term_frequencies,
    _tokenize,
)


def _build_objects_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE objects (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT,
            title TEXT,
            description TEXT,
            body TEXT,
            source_file TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            frontmatter_json TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO objects "
        "(id, type, name, title, description, body, source_file, content_hash, frontmatter_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-001",
            "Attribute",
            "Customer Group",
            "Customer Group",
            "Sales-area-dependent customer grouping",
            "# Customer Group",
            "model/ATTR-001.md",
            "hash",
            '{"id": "ATTR-001", "type": "Attribute"}',
        ),
    )
    conn.execute(
        "INSERT INTO objects "
        "(id, type, name, title, description, body, source_file, content_hash, frontmatter_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-001",
            "FieldEndpoint",
            "KNVV KDGRP",
            None,
            "SAP field for customer group",
            "# KNVV KDGRP",
            "model/FEP-001.md",
            "hash",
            '{"id": "FEP-001", "type": "FieldEndpoint", "technical_name": "KDGRP"}',
        ),
    )


def test_tokenize_lowercase_and_splits() -> None:
    assert _tokenize("Customer Group, KNVV-KDGRP!") == [
        "customer", "group", "knvv", "kdgrp"
    ]


def test_term_frequencies_counts() -> None:
    assert _term_frequencies(["a", "b", "a"]) == {"a": 2, "b": 1}


def test_compute_idf_basic() -> None:
    assert _compute_idf(10, 1) > _compute_idf(10, 5)
    assert _compute_idf(0, 1) == 0.0
    assert _compute_idf(10, 0) == 0.0


def test_cosine_similarity_orthogonal() -> None:
    assert _cosine_similarity({"a": 1.0}, {"b": 1.0}) == 0.0


def test_cosine_similarity_identical() -> None:
    assert _cosine_similarity({"a": 1.0, "b": 1.0}, {"a": 1.0, "b": 1.0}) == 1.0


def test_builder_creates_tables_and_vectors(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    builder = SemanticIndexBuilder()
    builder.build(conn)

    vocab = conn.execute("SELECT term FROM semantic_vocabulary").fetchall()
    assert ("customer",) in vocab
    index = conn.execute("SELECT object_id, magnitude FROM semantic_index").fetchall()
    assert any(row[0] == "ATTR-001" for row in index)
    conn.close()


def test_semantic_search_ranks_related_terms(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    SemanticIndexBuilder().build(conn)
    conn.close()

    searcher = SemanticSearcher()
    results = searcher.search(db, "customer grouping")
    ids = [r.object_id for r in results]
    assert "ATTR-001" in ids
    assert "FEP-001" in ids
    assert results[0].semantic_score >= results[1].semantic_score


def test_semantic_search_empty_query(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    SemanticIndexBuilder().build(conn)
    conn.close()

    assert SemanticSearcher().search(db, "   ") == []


def test_semantic_search_missing_index(tmp_path: Path) -> None:
    db = tmp_path / "empty.db"
    conn = __import__("sqlite3").connect(str(db))
    conn.executescript("CREATE TABLE objects (id TEXT PRIMARY KEY);")
    conn.close()
    assert SemanticSearcher().search(db, "customer") == []

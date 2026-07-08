"""Tests for the local-first semantic search index."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import patch

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.index.semantic_search import (
    SemanticIndexBuilder,
    SemanticSearcher,
    _compute_idf,
    _cosine_similarity,
    _term_frequencies,
    _tokenize,
)
from modelops_core.index.sqlite_builder import build_index


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


def _build_relationships_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE object_relationships (
            from_object_id TEXT NOT NULL,
            to_object_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            weight REAL
        );
        """
    )


def _insert_object(
    conn: sqlite3.Connection,
    object_id: str,
    obj_type: str,
    name: str,
    description: str,
    frontmatter: dict[str, Any] | None = None,
) -> None:
    if frontmatter is None:
        frontmatter = {"id": object_id, "type": obj_type}
    conn.execute(
        "INSERT INTO objects "
        "(id, type, name, title, description, body, source_file, content_hash, frontmatter_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            object_id,
            obj_type,
            name,
            name,
            description,
            f"# {name}",
            f"model/{object_id}.md",
            "hash",
            json.dumps(frontmatter),
        ),
    )


def _insert_relationship(
    conn: sqlite3.Connection,
    from_object_id: str,
    to_object_id: str,
    relationship_type: str = "relates_to",
) -> None:
    conn.execute(
        "INSERT INTO object_relationships (from_object_id, to_object_id, relationship_type) "
        "VALUES (?, ?, ?)",
        (from_object_id, to_object_id, relationship_type),
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


def test_semantic_search_missing_vocabulary_returns_empty(tmp_path: Path) -> None:
    db = tmp_path / "partial.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE objects (id TEXT PRIMARY KEY);
        CREATE TABLE semantic_index (
            object_id TEXT PRIMARY KEY,
            term_vector_json TEXT NOT NULL,
            magnitude REAL NOT NULL,
            term_count INTEGER NOT NULL
        );
        """
    )
    conn.close()
    assert SemanticSearcher().search(db, "customer") == []


def test_semantic_search_expand_requires_relationships_table(tmp_path: Path) -> None:
    db = tmp_path / "partial.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    SemanticIndexBuilder().build(conn)
    conn.close()

    # Without expansion the index is usable.
    assert SemanticSearcher().search(db, "grouping", candidate_ids={"ATTR-001"}) != []

    # Expansion requires object_relationships; missing table returns empty gracefully.
    assert (
        SemanticSearcher().search(
            db,
            "grouping",
            candidate_ids={"ATTR-001"},
            expand=True,
        )
        == []
    )


def test_semantic_search_candidate_ids_filter(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    SemanticIndexBuilder().build(conn)
    conn.close()

    searcher = SemanticSearcher()
    results = searcher.search(db, "grouping", candidate_ids={"ATTR-001"})
    assert [r.object_id for r in results] == ["ATTR-001"]


def test_semantic_search_min_score(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    SemanticIndexBuilder().build(conn)
    conn.close()

    searcher = SemanticSearcher()
    all_results = searcher.search(db, "customer grouping")
    assert len(all_results) == 2

    threshold = all_results[0].semantic_score - 0.001
    filtered = searcher.search(db, "customer grouping", min_score=threshold)
    assert len(filtered) == 1
    assert filtered[0].object_id == all_results[0].object_id
    assert filtered[0].semantic_score >= threshold


def test_semantic_search_limit(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    _insert_object(
        conn,
        "OBJ-EXTRA",
        "Attribute",
        "Extra Grouping",
        "Another customer grouping object",
    )
    SemanticIndexBuilder().build(conn)
    conn.close()

    searcher = SemanticSearcher()
    results = searcher.search(db, "grouping", limit=1)
    assert len(results) == 1


def test_semantic_search_expand_surfaces_related_objects(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    _insert_object(
        conn,
        "OBJ-SOURCE",
        "BusinessEntity",
        "Customer Master",
        "Central customer master record",
    )
    _insert_object(
        conn,
        "OBJ-TARGET",
        "Attribute",
        "Region Classification",
        "Geographic region classification",
    )
    _build_relationships_table(conn)
    _insert_relationship(conn, "OBJ-SOURCE", "OBJ-TARGET")
    SemanticIndexBuilder().build(conn)
    conn.close()

    searcher = SemanticSearcher()
    candidate_ids = {"OBJ-SOURCE", "OBJ-TARGET"}

    no_expand = searcher.search(db, "customer master", candidate_ids=candidate_ids, expand=False)
    with_expand = searcher.search(db, "customer master", candidate_ids=candidate_ids, expand=True)

    target_no_expand = next(r for r in no_expand if r.object_id == "OBJ-TARGET")
    target_with_expand = next(r for r in with_expand if r.object_id == "OBJ-TARGET")

    # Without expansion the related object shares no query terms and scores zero.
    assert target_no_expand.semantic_score == 0.0
    # With expansion the related object's vector is blended into the query,
    # surfacing the related object with a non-zero score.
    assert target_with_expand.semantic_score > target_no_expand.semantic_score


def test_build_index_creates_semantic_index(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated = tmp_path / "generated"
    generated.mkdir()
    (model_dir / "DOMAIN-EXAMPLE.md").write_text(
        "---\n"
        "id: DOMAIN-EXAMPLE\n"
        "type: MasterDataDomain\n"
        "status: active\n"
        "name: Example Domain\n"
        "---\n"
        "\n"
        "# Example\n"
    )

    build_index(repo_root=tmp_path)

    db = generated / "modelops.db"
    conn = sqlite3.connect(str(db))
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='semantic_index'"
    ).fetchone()
    assert row is not None
    conn.close()


def test_cli_search_semantic_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    generated = repo / "generated"
    generated.mkdir()

    db = generated / "modelops.db"
    conn = __import__("sqlite3").connect(str(db))
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
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-001", "Attribute", "active", "Customer Group", "Customer Group", None,
            "Sales-area-dependent customer grouping", "# Customer Group",
            "model/ATTR-001.md", "hash", '{"id": "ATTR-001", "type": "Attribute"}',
            None, None,
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-001", "FieldEndpoint", "active", "KNVV KDGRP", None, None,
            "SAP field for customer grouping", "# KNVV KDGRP",
            "model/FEP-001.md",
            "hash",
            '{"id": "FEP-001", "type": "FieldEndpoint", "technical_name": "KDGRP"}',
            None, None,
        ),
    )
    SemanticIndexBuilder().build(conn)
    conn.close()

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["search", "customer grouping", "--repo", str(repo), "--semantic", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "results" in data
    assert data["total_count"] == 2
    assert all("semantic_score" in r for r in data["results"])
    assert data["results"][0]["semantic_score"] >= data["results"][1]["semantic_score"]


def test_cli_search_semantic_keyword_only_ranks_last(tmp_path: Path) -> None:
    """Keyword-only fallback matches must receive a zero semantic score and rank below
    objects that have a real semantic score.
    """
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    generated = repo / "generated"
    generated.mkdir()

    db = generated / "modelops.db"
    conn = __import__("sqlite3").connect(str(db))
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
            body TEXT,
            source_file TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            frontmatter_json TEXT,
            body_hash TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO objects ("
        "id, type, status, name, title, domain, description, body, "
        "source_file, content_hash, frontmatter_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-001", "Attribute", "active", "Customer Group", "Customer Group", None,
            "Sales-area-dependent customer grouping", "# Customer Group",
            "model/ATTR-001.md", "hash",
            '{"id": "ATTR-001", "type": "Attribute"}',
        ),
    )
    conn.execute(
        "INSERT INTO objects ("
        "id, type, status, name, title, domain, description, body, "
        "source_file, content_hash, frontmatter_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-001", "FieldEndpoint", "active", "KNVV KDGRP", None, None,
            "SAP field for customer grouping", "# KNVV KDGRP",
            "model/FEP-001.md", "hash",
            '{"id": "FEP-001", "type": "FieldEndpoint", "technical_name": "KDGRP"}',
        ),
    )
    conn.commit()
    conn.close()

    from modelops_core.index.semantic_search import SemanticSearchResult

    def _fake_semantic_search(*_args, **_kwargs):
        # Simulate a semantic index that only recognises ATTR-001.
        return [
            SemanticSearchResult(
                object_id="ATTR-001",
                object_type="Attribute",
                semantic_score=0.75,
                matched_terms=["customer", "grouping"],
            ),
        ]

    with patch("modelops_core.cli.semantic_search_objects", side_effect=_fake_semantic_search):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "search",
                "customer grouping",
                "--repo",
                str(repo),
                "--semantic",
                "--json",
            ],
        )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_count"] == 2
    scores = [r["score"] for r in data["results"]]
    assert scores == sorted(scores, reverse=True)
    assert scores[-1] == 0.0
    assert data["results"][-1]["object_id"] == "FEP-001"
    assert data["results"][-1]["semantic_score"] == 0.0
    assert data["results"][-1]["semantic_matched_terms"] == []
    attr = next(r for r in data["results"] if r["object_id"] == "ATTR-001")
    assert attr["score"] == 0.75
    assert attr["semantic_score"] == 0.75
    assert set(attr["semantic_matched_terms"]) == {"customer", "grouping"}

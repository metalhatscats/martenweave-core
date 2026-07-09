"""Tests for SQLite index builder."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.config import resolve_generated_path
from modelops_core.index import build_index
from modelops_core.index.queries import get_object_by_id


def test_build_index_warns_above_threshold(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    model_dir = repo_root / "model"
    model_dir.mkdir()
    # Create enough objects to exceed the default 80% warning threshold with max=10.
    (repo_root / "modelops.config.yaml").write_text(
        "resource_limits:\n  max_index_objects: 10\n", encoding="utf-8"
    )
    for i in range(9):
        (model_dir / f"OBJ-{i:04d}.md").write_text(
            f"---\nid: OBJ-{i:04d}\ntype: MasterDataDomain\nstatus: draft\nname: Object {i}\n---\n",
            encoding="utf-8",
        )

    with pytest.warns(UserWarning, match="above the recommended warning threshold"):
        build_index(repo_root=repo_root)


def test_build_index_creates_db(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    summary = build_index(repo_root=repo_root, db_path=db_path)
    assert db_path.exists()
    assert summary.is_valid


def test_build_index_populates_objects(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    obj = get_object_by_id(db_path, "DOMAIN-TEST")
    assert obj is not None
    assert obj["type"] == "MasterDataDomain"


def test_build_index_export_jsonl(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path, export_jsonl=True)

    gen = resolve_generated_path(repo_root)
    assert (gen / "search_documents.jsonl").exists()
    assert (gen / "lineage_edges.jsonl").exists()


def test_build_index_rejects_invalid(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    # Add an invalid object
    (temp_model_dir / "invalid.md").write_text(
        "---\nid: bad\ntype: BadType\nstatus: draft\n---\n", encoding="utf-8"
    )
    db_path = repo_root / "generated" / "modelops.db"
    with pytest.raises(ValueError, match="Validation failed"):
        build_index(repo_root=repo_root, db_path=db_path, allow_invalid=False)


def test_build_index_creates_relationship_indexes(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    import sqlite3

    conn = sqlite3.connect(db_path)
    indexes = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'index' AND tbl_name = 'object_relationships'"
        )
    }
    conn.close()
    assert "idx_rel_from" in indexes
    assert "idx_rel_to" in indexes
    assert "idx_rel_to_type" in indexes


def test_build_index_creates_object_filter_indexes(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    import sqlite3

    conn = sqlite3.connect(db_path)
    indexes = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'objects'"
        )
    }
    conn.close()
    assert "idx_objects_type" in indexes
    assert "idx_objects_status" in indexes
    assert "idx_objects_domain" in indexes


def test_build_index_creates_tag_index(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    import sqlite3

    conn = sqlite3.connect(db_path)
    indexes = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'tags'"
        )
    }
    conn.close()
    assert "idx_tag_tag" in indexes


def test_build_index_stores_timestamps(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    import sqlite3

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT created_at, updated_at FROM objects WHERE id = ?", ("DOMAIN-TEST",)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] is not None
    assert row[1] is not None
    assert "T" in row[0]  # ISO 8601 format
    assert "T" in row[1]

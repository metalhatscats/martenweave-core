"""Tests for search document JSONL export."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from modelops_core.index.search_documents import export_search_jsonl


class TestExportSearchJsonl:
    def _build_db(self, db_path: Path) -> None:
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """
            CREATE TABLE objects (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                name TEXT,
                title TEXT,
                domain TEXT,
                source_file TEXT NOT NULL,
                frontmatter_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ATTR-001",
                "Attribute",
                "active",
                "Customer Group",
                None,
                "DOMAIN-A",
                "model/ATTR-001.md",
                '{"id": "ATTR-001", "tags": ["sales"]}',
            ),
        )
        conn.commit()
        conn.close()

    def test_exports_jsonl(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        out = tmp_path / "search_documents.jsonl"
        self._build_db(db)
        export_search_jsonl(db, out)
        assert out.exists()
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["id"] == "ATTR-001"
        assert obj["frontmatter"]["tags"] == ["sales"]

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        out = tmp_path / "sub" / "dir" / "search_documents.jsonl"
        self._build_db(db)
        export_search_jsonl(db, out)
        assert out.exists()

    def test_empty_db_creates_empty_file(self, tmp_path: Path) -> None:
        db = tmp_path / "modelops.db"
        out = tmp_path / "search_documents.jsonl"
        conn = sqlite3.connect(str(db))
        conn.execute(
            """
            CREATE TABLE objects (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                name TEXT,
                title TEXT,
                domain TEXT,
                source_file TEXT NOT NULL,
                frontmatter_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
        export_search_jsonl(db, out)
        assert out.exists()
        assert out.read_text(encoding="utf-8").strip() == ""

    def test_missing_db_raises(self, tmp_path: Path) -> None:
        import sqlite3

        db = tmp_path / "missing.db"
        out = tmp_path / "search_documents.jsonl"
        with pytest.raises(sqlite3.OperationalError):
            export_search_jsonl(db, out)

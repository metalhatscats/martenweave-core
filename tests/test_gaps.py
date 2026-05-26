"""Tests for gap detection CLI and service."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.gaps.gap_detection import (
    _find_matches,
    detect_dataset_gaps,
)
from modelops_core.imports.dataset_profiler import ColumnProfile, DatasetProfile

runner = CliRunner()


def _make_profile(columns: list[str]) -> DatasetProfile:
    return DatasetProfile(
        dataset_id="test-dataset",
        file_path="/tmp/test.csv",
        file_hash="abc",
        row_count=10,
        column_count=len(columns),
        columns=[
            ColumnProfile(name=c, position=idx, inferred_type="text")
            for idx, c in enumerate(columns)
        ],
    )


def test_find_matches_exact() -> None:
    endpoints = {
        "FEP-001": {
            "id": "FEP-001",
            "column_name": "CUSTOMER_ID",
            "field_name": None,
        }
    }
    matches = _find_matches("CUSTOMER_ID", endpoints)
    assert len(matches) == 1
    assert matches[0].matched_endpoint_id == "FEP-001"
    assert matches[0].match_type == "exact"


def test_find_matches_normalized() -> None:
    endpoints = {
        "FEP-001": {
            "id": "FEP-001",
            "column_name": None,
            "field_name": "customer-id",
        }
    }
    matches = _find_matches("CUSTOMER_ID", endpoints)
    assert len(matches) == 1
    assert matches[0].matched_endpoint_id == "FEP-001"
    assert matches[0].match_type == "normalized"


def test_find_matches_no_match() -> None:
    endpoints = {"FEP-001": {"id": "FEP-001", "column_name": "OTHER"}}
    matches = _find_matches("UNKNOWN", endpoints)
    assert matches == []


def test_detect_dataset_gaps_unmodeled_column(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    import sqlite3

    conn = sqlite3.connect(str(db))
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
        """
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-001",
            "FieldEndpoint",
            "active",
            "Customer ID",
            None,
            None,
            None,
            "model/FEP-001.md",
            "abc",
            '{"id": "FEP-001", "column_name": "CUSTOMER_ID"}',
            None,
            None,
            None,
        ),
    )
    conn.commit()
    conn.close()

    profile = _make_profile(["CUSTOMER_ID", "UNKNOWN_LEGACY_FIELD"])
    report = detect_dataset_gaps(profile, db)

    assert len(report.gaps) == 1
    assert report.gaps[0].gap_code == "UNMODELED_DATASET_COLUMN"
    assert report.gaps[0].column_name == "UNKNOWN_LEGACY_FIELD"
    assert len(report.matches) == 1
    assert report.matches[0].column_name == "CUSTOMER_ID"


def test_detect_dataset_gaps_multiple_matches(tmp_path: Path) -> None:
    db = tmp_path / "modelops.db"
    import sqlite3

    conn = sqlite3.connect(str(db))
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
        """
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-001",
            "FieldEndpoint",
            "active",
            "Customer ID",
            None,
            None,
            None,
            "model/FEP-001.md",
            "abc",
            '{"id": "FEP-001", "column_name": "CUSTOMER_ID"}',
            None,
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
            "Customer ID Alt",
            None,
            None,
            None,
            "model/FEP-002.md",
            "def",
            '{"id": "FEP-002", "column_name": "CUSTOMER_ID"}',
            None,
            None,
            None,
        ),
    )
    conn.commit()
    conn.close()

    profile = _make_profile(["CUSTOMER_ID"])
    report = detect_dataset_gaps(profile, db)

    assert len(report.gaps) == 1
    assert report.gaps[0].gap_code == "DATASET_COLUMN_MULTIPLE_MATCHES"


class TestGapsCli:
    def test_gaps_no_index(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["gaps", str(tmp_path / "data.csv"), "--repo", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "build-index" in result.output or "No index found" in result.output

    def test_gaps_missing_dataset(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        generated = repo / "generated"
        generated.mkdir()
        (generated / "modelops.db").write_text("")

        result = runner.invoke(
            app,
            ["gaps", str(tmp_path / "missing.csv"), "--repo", str(repo)],
        )
        assert result.exit_code == 1
        assert "Dataset not found" in result.output

    def test_gaps_json_output(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        generated = repo / "generated"
        generated.mkdir()
        db = generated / "modelops.db"

        import sqlite3

        conn = sqlite3.connect(str(db))
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
            """
        )
        conn.execute(
            "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "FEP-001",
                "FieldEndpoint",
                "active",
                "Customer ID",
                None,
                None,
                None,
                "model/FEP-001.md",
                "abc",
                '{"id": "FEP-001", "column_name": "CUSTOMER_ID"}',
                None,
                None,
                None,
            ),
        )
        conn.commit()
        conn.close()

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("CUSTOMER_ID,UNKNOWN\n1,a\n", encoding="utf-8")

        result = runner.invoke(
            app, ["gaps", str(csv_path), "--repo", str(repo), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dataset_id"] == "data"
        assert len(data["gaps"]) == 1
        assert data["gaps"][0]["column_name"] == "UNKNOWN"
        assert len(data["matches"]) == 1

    def test_gaps_create_issues(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        generated = repo / "generated"
        generated.mkdir()
        db = generated / "modelops.db"

        import sqlite3

        conn = sqlite3.connect(str(db))
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
            """
        )
        conn.commit()
        conn.close()

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("UNKNOWN_COL\n1\n", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "gaps",
                str(csv_path),
                "--repo",
                str(repo),
                "--create-issues",
            ],
        )
        assert result.exit_code == 0
        issue_file = model_dir / "issues" / "ISSUE-GAP-DATA-001.md"
        assert issue_file.exists()
        text = issue_file.read_text(encoding="utf-8")
        assert "Issue" in text
        assert "UNKNOWN_COL" in text

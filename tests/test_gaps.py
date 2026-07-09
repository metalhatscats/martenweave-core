"""Tests for gap detection CLI and service."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.gaps.gap_detection import (
    ColumnGap,
    DatasetGapReport,
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

    assert report.coverage is not None
    assert report.coverage.total_columns == 2
    assert report.coverage.matched_columns == 1
    assert report.coverage.unmatched_columns == 1
    assert report.coverage.duplicate_columns == 0
    assert report.coverage.match_rate == 0.5


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
        result = runner.invoke(app, ["gaps", str(tmp_path / "data.csv"), "--repo", str(tmp_path)])
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
            CREATE TABLE object_relationships (
                from_object_id TEXT NOT NULL,
                to_object_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                relationship_class TEXT
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

        result = runner.invoke(app, ["gaps", str(csv_path), "--repo", str(repo), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dataset_id"] == "data"
        assert "coverage" in data
        assert data["coverage"]["total_columns"] == 2
        assert data["coverage"]["matched_columns"] == 1
        assert data["coverage"]["unmatched_columns"] == 1
        assert data["coverage"]["duplicate_columns"] == 0
        assert data["coverage"]["match_rate"] == 0.5
        assert len(data["gaps"]) == 1
        assert data["gaps"][0]["column_name"] == "UNKNOWN"
        assert len(data["matches"]) == 1

    def test_gaps_create_issues_preview_without_write(self, tmp_path: Path) -> None:
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
        assert "Preview only" in result.output
        assert "--write" in result.output
        issue_file = model_dir / "issues" / "ISSUE-GAP-DATA-001.md"
        assert not issue_file.exists()

    def test_gaps_create_issues_with_write(self, tmp_path: Path) -> None:
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
                "--write",
            ],
        )
        assert result.exit_code == 0
        issue_file = model_dir / "issues" / "ISSUE-GAP-DATA-001.md"
        assert issue_file.exists()
        text = issue_file.read_text(encoding="utf-8")
        assert "Issue" in text
        assert "UNKNOWN_COL" in text
        assert "Audit event written" in result.output

    def test_gaps_create_issues_dry_run(self, tmp_path: Path) -> None:
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
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Dry-run" in result.output
        issue_file = model_dir / "issues" / "ISSUE-GAP-DATA-001.md"
        assert not issue_file.exists()


def test_gap_severity_assignment() -> None:
    from modelops_core.gaps.gap_detection import _severity_for_gap

    assert _severity_for_gap("UNMODELED_DATASET_COLUMN") == "warning"
    assert _severity_for_gap("DATASET_COLUMN_MULTIPLE_MATCHES") == "warning"
    assert _severity_for_gap("MODEL_ATTRIBUTE_MISSING_SOURCE") == "critical"
    assert _severity_for_gap("MISSING_OWNER") == "warning"
    assert _severity_for_gap("DUPLICATE_COLUMN_NAME") == "warning"
    assert _severity_for_gap("UNKNOWN_CODE") == "info"


def test_detect_dataset_gaps_includes_metadata(tmp_path: Path) -> None:
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
    gap = report.gaps[0]
    assert gap.gap_code == "UNMODELED_DATASET_COLUMN"
    assert gap.severity == "warning"
    assert gap.source_dataset_metadata.get("dataset_id") == "test-dataset"
    assert gap.source_dataset_metadata.get("row_count") == 10
    assert gap.recommended_proposal_op is not None
    assert gap.recommended_proposal_op["op"] == "create_issue"
    assert gap.recommended_proposal_op.get("object_id") is not None
    assert gap.recommended_proposal_op.get("after", {}).get("type") == "Issue"


def test_detect_dataset_gaps_duplicate_columns(tmp_path: Path) -> None:
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
    conn.commit()
    conn.close()

    profile = DatasetProfile(
        dataset_id="dup-dataset",
        file_path="/tmp/dup.csv",
        file_hash="abc",
        row_count=5,
        column_count=3,
        columns=[
            ColumnProfile(name="COL_A", position=0, inferred_type="text"),
            ColumnProfile(name="COL_A", position=1, inferred_type="text"),
            ColumnProfile(name="COL_B", position=2, inferred_type="text"),
        ],
    )
    report = detect_dataset_gaps(profile, db)

    dup_gaps = [g for g in report.gaps if g.gap_code == "DUPLICATE_COLUMN_NAME"]
    assert len(dup_gaps) == 1
    assert dup_gaps[0].column_name == "COL_A"
    assert dup_gaps[0].severity == "warning"

    assert report.coverage is not None
    assert report.coverage.total_columns == 3
    assert report.coverage.matched_columns == 0
    assert report.coverage.unmatched_columns == 3
    assert report.coverage.duplicate_columns == 1
    assert report.coverage.match_rate == 0.0


def test_promote_gaps_to_proposal(tmp_path: Path) -> None:
    from modelops_core.gaps.gap_detection import promote_gaps_to_proposal

    model_dir = tmp_path / "model"
    model_dir.mkdir()

    report = DatasetGapReport(
        dataset_id="test-dataset",
        gaps=[
            ColumnGap(
                column_name="UNKNOWN_COL",
                gap_code="UNMODELED_DATASET_COLUMN",
                severity="warning",
                message="No matching endpoint.",
                recommended_proposal_op={
                    "op": "create_issue",
                    "object_id": "ISSUE-GAP-TEST-DATASET-UNKNOWN-COL-UNMODELED",
                    "object_type": "Issue",
                    "after": {
                        "id": "ISSUE-GAP-TEST-DATASET-UNKNOWN-COL-UNMODELED",
                        "type": "Issue",
                        "status": "open",
                        "name": "Dataset gap: UNMODELED_DATASET_COLUMN",
                        "issue_type": "dataset_gap",
                        "severity": "warning",
                        "source_dataset_id": "test-dataset",
                        "source_column": "UNKNOWN_COL",
                        "source_gap_code": "UNMODELED_DATASET_COLUMN",
                        "recommended_action": "No matching endpoint.",
                    },
                },
            )
        ],
    )

    proposal_path = promote_gaps_to_proposal(report, model_dir)
    assert proposal_path.exists()
    text = proposal_path.read_text(encoding="utf-8")
    assert "PP-GAP-TEST-DATASET-001" in text
    assert "pending_review" in text
    assert "create_issue" in text
    assert "ISSUE-GAP-TEST-DATASET-UNKNOWN-COL-UNMODELED" in text


class TestGapsPromoteCli:
    def test_gaps_promote_to_proposal(self, tmp_path: Path) -> None:
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
                "--promote-to-proposal",
                "--write",
            ],
        )
        assert result.exit_code == 0
        proposal_file = model_dir / "patch-proposals" / "PP-GAP-DATA-001.md"
        assert proposal_file.exists()
        text = proposal_file.read_text(encoding="utf-8")
        assert "PatchProposal" in text
        assert "pending_review" in text
        assert "Audit event written" in result.output


def test_detect_dataset_gaps_empty_dataset(tmp_path: Path) -> None:
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
    conn.commit()
    conn.close()

    profile = DatasetProfile(
        dataset_id="empty-dataset",
        file_path="/tmp/empty.csv",
        file_hash="abc",
        row_count=0,
        column_count=0,
        columns=[],
    )
    report = detect_dataset_gaps(profile, db)

    assert len(report.gaps) == 1
    assert report.gaps[0].gap_code == "EMPTY_DATASET"
    assert report.gaps[0].severity == "info"
    assert len(report.matches) == 0

    assert report.coverage is not None
    assert report.coverage.total_columns == 0
    assert report.coverage.matched_columns == 0
    assert report.coverage.unmatched_columns == 0
    assert report.coverage.duplicate_columns == 0
    assert report.coverage.match_rate == 0.0


def test_detect_dataset_gaps_no_matching_endpoints(tmp_path: Path) -> None:
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
            "Other",
            None,
            None,
            None,
            "model/FEP-001.md",
            "abc",
            '{"id": "FEP-001", "column_name": "OTHER"}',
            None,
            None,
            None,
        ),
    )
    conn.commit()
    conn.close()

    profile = _make_profile(["COL_A", "COL_B"])
    report = detect_dataset_gaps(profile, db)

    no_match_gap = [g for g in report.gaps if g.gap_code == "NO_MATCHING_ENDPOINTS"]
    assert len(no_match_gap) == 1
    assert no_match_gap[0].severity == "warning"

    assert report.coverage is not None
    assert report.coverage.total_columns == 2
    assert report.coverage.matched_columns == 0
    assert report.coverage.unmatched_columns == 2
    assert report.coverage.duplicate_columns == 0
    assert report.coverage.match_rate == 0.0


def test_detect_dataset_gaps_case_sensitivity(tmp_path: Path) -> None:
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
            '{"id": "FEP-001", "column_name": "customer_id"}',
            None,
            None,
            None,
        ),
    )
    conn.commit()
    conn.close()

    profile = _make_profile(["CUSTOMER_ID"])
    report = detect_dataset_gaps(profile, db)

    assert len(report.gaps) == 0
    assert len(report.matches) == 1
    assert report.matches[0].match_type == "normalized"


def test_detect_model_gaps_attribute_missing_source(tmp_path: Path) -> None:
    from modelops_core.gaps.gap_detection import detect_model_gaps

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
        CREATE TABLE object_relationships (
            from_object_id TEXT NOT NULL,
            to_object_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            relationship_class TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-001",
            "Attribute",
            "active",
            "Test Attr",
            None,
            None,
            None,
            "model/ATTR-001.md",
            "abc",
            '{"id": "ATTR-001"}',
            None,
            None,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-002",
            "Attribute",
            "active",
            "Linked Attr",
            None,
            None,
            None,
            "model/ATTR-002.md",
            "def",
            '{"id": "ATTR-002"}',
            None,
            None,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO object_relationships VALUES (?, ?, ?, ?)",
        ("FEP-002", "ATTR-002", "represents_attribute", None),
    )
    conn.commit()
    conn.close()

    gaps = detect_model_gaps(db)
    missing = [g for g in gaps if g.gap_code == "MODEL_ATTRIBUTE_MISSING_SOURCE"]
    assert len(missing) == 1
    assert missing[0].column_name == "ATTR-001"
    assert missing[0].severity == "critical"


def test_detect_model_gaps_missing_owner(tmp_path: Path) -> None:
    from modelops_core.gaps.gap_detection import detect_model_gaps

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
        CREATE TABLE object_relationships (
            from_object_id TEXT NOT NULL,
            to_object_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            relationship_class TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-001",
            "Attribute",
            "active",
            "Test Attr",
            None,
            None,
            None,
            "model/ATTR-001.md",
            "abc",
            '{"id": "ATTR-001"}',
            None,
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
            "Test FEP",
            None,
            None,
            None,
            "model/FEP-001.md",
            "def",
            '{"id": "FEP-001", "business_owner": "alice"}',
            None,
            None,
            None,
        ),
    )
    conn.commit()
    conn.close()

    gaps = detect_model_gaps(db)
    missing = [g for g in gaps if g.gap_code == "MISSING_OWNER"]
    assert len(missing) == 1
    assert missing[0].column_name == "ATTR-001"
    assert missing[0].severity == "warning"


class TestGapsCheckModelCli:
    def test_gaps_check_model(self, tmp_path: Path) -> None:
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
            CREATE TABLE object_relationships (
                from_object_id TEXT NOT NULL,
                to_object_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                relationship_class TEXT
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
            app, ["gaps", str(csv_path), "--repo", str(repo), "--check-model", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["gaps"]) >= 1


def test_promote_gaps_to_proposal_avoids_collision(tmp_path: Path) -> None:
    """Repeated promotion on the same dataset must not overwrite."""
    from modelops_core.gaps.gap_detection import promote_gaps_to_proposal

    model_dir = tmp_path / "model"
    model_dir.mkdir()

    report = DatasetGapReport(
        dataset_id="test-dataset",
        gaps=[
            ColumnGap(
                column_name="UNKNOWN_COL",
                gap_code="UNMODELED_DATASET_COLUMN",
                severity="warning",
                message="No matching endpoint.",
                recommended_proposal_op={
                    "op": "create_issue",
                    "object_id": "ISSUE-GAP-TEST-DATASET-UNKNOWN-COL-UNMODELED",
                    "object_type": "Issue",
                    "after": {
                        "id": "ISSUE-GAP-TEST-DATASET-UNKNOWN-COL-UNMODELED",
                        "type": "Issue",
                        "status": "open",
                        "name": "Dataset gap: UNMODELED_DATASET_COLUMN",
                        "issue_type": "dataset_gap",
                        "severity": "warning",
                        "source_dataset_id": "test-dataset",
                        "source_column": "UNKNOWN_COL",
                        "source_gap_code": "UNMODELED_DATASET_COLUMN",
                        "recommended_action": "No matching endpoint.",
                    },
                },
            )
        ],
    )

    # First promotion
    proposal_path_1 = promote_gaps_to_proposal(report, model_dir)
    assert proposal_path_1.exists()
    assert proposal_path_1.name == "PP-GAP-TEST-DATASET-001.md"
    text_1 = proposal_path_1.read_text(encoding="utf-8")
    assert "PP-GAP-TEST-DATASET-001" in text_1

    # Second promotion must create a distinct file
    proposal_path_2 = promote_gaps_to_proposal(report, model_dir)
    assert proposal_path_2.exists()
    assert proposal_path_2.name == "PP-GAP-TEST-DATASET-002.md"
    text_2 = proposal_path_2.read_text(encoding="utf-8")
    assert "PP-GAP-TEST-DATASET-002" in text_2

    # First file must still exist and be unchanged
    assert proposal_path_1.exists()
    assert proposal_path_1.read_text(encoding="utf-8") == text_1

    # Third promotion
    proposal_path_3 = promote_gaps_to_proposal(report, model_dir)
    assert proposal_path_3.name == "PP-GAP-TEST-DATASET-003.md"
    assert len(list((model_dir / "patch-proposals").glob("PP-GAP-TEST-DATASET-*.md"))) == 3


class TestGapsPromoteCliRepeated:
    def test_gaps_promote_to_proposal_twice(self, tmp_path: Path) -> None:
        """CLI repeated --promote-to-proposal creates distinct proposals."""
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

        # First promotion
        result = runner.invoke(
            app,
            [
                "gaps",
                str(csv_path),
                "--repo",
                str(repo),
                "--promote-to-proposal",
                "--write",
            ],
        )
        assert result.exit_code == 0
        proposal_1 = model_dir / "patch-proposals" / "PP-GAP-DATA-001.md"
        assert proposal_1.exists()

        # Second promotion
        result = runner.invoke(
            app,
            [
                "gaps",
                str(csv_path),
                "--repo",
                str(repo),
                "--promote-to-proposal",
                "--write",
            ],
        )
        assert result.exit_code == 0
        proposal_2 = model_dir / "patch-proposals" / "PP-GAP-DATA-002.md"
        assert proposal_2.exists()

        # First must still exist
        assert proposal_1.exists()


class TestGapsMultiSheetXlsx:
    def test_gaps_multi_sheet_xlsx_json(self, tmp_path: Path) -> None:
        """Multi-sheet XLSX gaps include sheet_name in JSON output."""
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
        # Match customer_id on both sheets
        conn.execute(
            "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "FEP-CUSTOMER-ID",
                "FieldEndpoint",
                "active",
                "Customer ID",
                None,
                None,
                None,
                "model/FEP-CUSTOMER-ID.md",
                "abc",
                '{"id": "FEP-CUSTOMER-ID", "column_name": "customer_id"}',
                None,
                None,
                None,
            ),
        )
        conn.commit()
        conn.close()

        xlsx_path = Path(__file__).parent / "fixtures" / "customer_sample_multi.xlsx"
        result = runner.invoke(
            app,
            [
                "gaps",
                str(xlsx_path),
                "--repo",
                str(repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "coverage" in data
        assert data["coverage"]["total_columns"] == 6  # 3 per sheet

        # Matches should include sheet_name
        matches = data["matches"]
        assert len(matches) >= 2
        sheet_names = {m["sheet_name"] for m in matches}
        assert "customers" in sheet_names

        # Gaps should include sheet_name
        gaps = data["gaps"]
        assert len(gaps) > 0
        gap_sheets = {g["sheet_name"] for g in gaps if g["sheet_name"]}
        assert len(gap_sheets) >= 1

    def test_gaps_multi_sheet_xlsx_human(self, tmp_path: Path) -> None:
        """Multi-sheet XLSX gaps show sheet context in human output."""
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

        xlsx_path = Path(__file__).parent / "fixtures" / "customer_sample_multi.xlsx"
        result = runner.invoke(
            app,
            [
                "gaps",
                str(xlsx_path),
                "--repo",
                str(repo),
            ],
        )
        assert result.exit_code == 0
        assert "Coverage" in result.output
        assert "Sheet" in result.output

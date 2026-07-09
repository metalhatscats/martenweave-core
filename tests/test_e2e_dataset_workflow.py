"""End-to-end tests for the dataset-readiness workflow.

These tests exercise the complete operational pipeline:

    init repo → load canonical files → validate → build index → profile dataset
    → detect gaps → run dataset-readiness → promote gaps to proposal
    → review bundle → accept → dry-run → apply → inspect audit log

They also cover important failure paths: missing dataset, unsupported format,
empty dataset, stale index, and no matching endpoints.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def _write_csv(path: Path, columns: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(row))
    path.write_text("\n".join(lines), encoding="utf-8")


def _build_minimal_repo(tmp_path: Path) -> Path:
    """Create a tiny repo with a domain, attribute, and FieldEndpoint."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    (repo / "generated").mkdir(parents=True)

    (repo / "modelops.config.yaml").write_text(
        'schema_version: "1.0"\nworkspace_name: Test Repo\n',
        encoding="utf-8",
    )

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: draft\n"
        "name: Test Domain\n"
        "---\n",
        encoding="utf-8",
    )

    (model_dir / "PERSON-OWNER.md").write_text(
        "---\n"
        "id: PERSON-OWNER\n"
        "type: Person\n"
        "status: active\n"
        "name: Test Owner\n"
        "---\n",
        encoding="utf-8",
    )

    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Customer Group\n"
        "domain: DOMAIN-TEST\n"
        "business_owner: PERSON-OWNER\n"
        "---\n",
        encoding="utf-8",
    )

    (model_dir / "FEP-TEST-CUSTOMER-GROUP.md").write_text(
        "---\n"
        "id: FEP-TEST-CUSTOMER-GROUP\n"
        "type: FieldEndpoint\n"
        "status: draft\n"
        "name: Customer Group Field\n"
        "domain: DOMAIN-TEST\n"
        "attribute: ATTR-TEST\n"
        "column_name: CUSTOMER_GROUP\n"
        "business_owner: PERSON-OWNER\n"
        "---\n",
        encoding="utf-8",
    )

    return repo


def _proposal_id_from_path(path_str: str) -> str:
    return Path(path_str).stem


class TestDatasetReadinessWorkflow:
    """Happy-path and failure-path coverage for the operational dataset flow."""

    def test_profile_dataset_creates_profile(self, tmp_path: Path) -> None:
        """profile-dataset writes a privacy-safe profile JSON."""
        repo = _build_minimal_repo(tmp_path)
        dataset = tmp_path / "customers.csv"
        _write_csv(dataset, ["CUSTOMER_GROUP"], [["A"], ["B"]])

        result = runner.invoke(
            app, ["profile-dataset", str(dataset), "--repo", str(repo)]
        )
        assert result.exit_code == 0, result.output

        profile_path = repo / "generated" / "dataset_profiles" / "customers.json"
        assert profile_path.exists()
        data = json.loads(profile_path.read_text(encoding="utf-8"))
        assert data["dataset_id"] == "customers"
        assert data["column_count"] == 1

    def test_gaps_json_output(self, tmp_path: Path) -> None:
        """gaps emits coverage and gap lists as JSON."""
        repo = _build_minimal_repo(tmp_path)
        dataset = tmp_path / "customers.csv"
        _write_csv(dataset, ["CUSTOMER_GROUP", "LEGACY_CODE"], [["A", "1"]])

        result = runner.invoke(
            app,
            [
                "build-index",
                "--repo",
                str(repo),
            ],
        )
        assert result.exit_code == 0, result.output

        result = runner.invoke(
            app,
            [
                "gaps",
                str(dataset),
                "--repo",
                str(repo),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["coverage"]["total_columns"] == 2
        assert data["coverage"]["matched_columns"] == 1
        assert data["coverage"]["unmatched_columns"] == 1
        assert any(g["gap_code"] == "UNMODELED_DATASET_COLUMN" for g in data["gaps"])

    def test_gaps_warns_stale_index(self, tmp_path: Path) -> None:
        """gaps flags when the index is older than the canonical files."""
        repo = _build_minimal_repo(tmp_path)
        dataset = tmp_path / "customers.csv"
        _write_csv(dataset, ["CUSTOMER_GROUP"], [["A"]])

        result = runner.invoke(app, ["build-index", "--repo", str(repo)])
        assert result.exit_code == 0, result.output

        # Touch a model file to make the index stale.
        (repo / "model" / "DOMAIN-TEST.md").write_text(
            "---\n"
            "id: DOMAIN-TEST\n"
            "type: MasterDataDomain\n"
            "status: draft\n"
            "name: Test Domain Updated\n"
            "---\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            app, ["gaps", str(dataset), "--repo", str(repo), "--json"]
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["stale_index_warning"] is True

    def test_full_readiness_workflow_promote_and_apply(self, tmp_path: Path) -> None:
        """End-to-end: readiness → proposal → review → accept → apply."""
        repo = _build_minimal_repo(tmp_path)
        dataset = tmp_path / "customers.csv"
        _write_csv(
            dataset,
            ["CUSTOMER_GROUP", "LEGACY_CODE"],
            [["A", "1"], ["B", "2"]],
        )
        out_dir = tmp_path / "out"

        # 1. Run dataset-readiness with promotion and issue draft.
        result = runner.invoke(
            app,
            [
                "run",
                "dataset-readiness",
                str(dataset),
                "--repo",
                str(repo),
                "--out",
                str(out_dir),
                "--check-model",
                "--promote-to-proposal",
                "--issue-draft",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        report = json.loads(result.output)
        assert report["verdict"] == "ready_with_warnings"
        assert report["validation"]["error_count"] == 0
        assert report["coverage"]["matched_columns"] == 1
        assert report["coverage"]["unmatched_columns"] == 1
        assert report["promoted_proposal_path"] is not None
        assert report["issue_draft_path"] is not None

        proposal_id = _proposal_id_from_path(report["promoted_proposal_path"])
        assert (out_dir / "readiness.json").exists()
        assert (out_dir / "readiness.md").exists()
        assert Path(report["issue_draft_path"]).exists()

        # 2. Review bundle reports the proposal as safe.
        result = runner.invoke(
            app,
            ["proposal", "review-bundle", proposal_id, "--repo", str(repo), "--json"],
        )
        assert result.exit_code == 0, result.output
        bundle = json.loads(result.output)
        assert bundle["proposal_id"] == proposal_id
        assert bundle["validation"]["is_safe"] is True
        assert bundle["validation"]["error_count"] == 0

        # 3. Accept the proposal.
        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                proposal_id,
                "--repo",
                str(repo),
                "--reviewer",
                "tester",
                "--skip-cr-creation",
            ],
        )
        assert result.exit_code == 0, result.output

        # 4. Dry-run apply.
        result = runner.invoke(
            app,
            [
                "proposal",
                "apply",
                proposal_id,
                "--repo",
                str(repo),
                "--dry-run",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        dry_run = json.loads(result.output)
        assert dry_run["dry_run"] is True
        assert dry_run["would_change"] is True

        # 5. Apply the proposal.
        result = runner.invoke(
            app,
            [
                "proposal",
                "apply",
                proposal_id,
                "--repo",
                str(repo),
                "--apply",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        apply_data = json.loads(result.output)
        assert apply_data["applied"] is True
        assert apply_data["proposal_id"] == proposal_id
        assert apply_data["changed_files"] != []

        # 6. The promoted gaps became Issue canonical files.
        issues_dir = repo / "model" / "issues"
        assert issues_dir.exists()
        issue_files = list(issues_dir.glob("*.md"))
        assert len(issue_files) >= 1

        # 7. Audit log captured the lifecycle events.
        result = runner.invoke(app, ["audit-log", "--repo", str(repo), "--json"])
        assert result.exit_code == 0, result.output
        events = json.loads(result.output)
        event_types = [e["event_type"] for e in events]
        assert "patch_dry_run" in event_types
        assert "patch_apply" in event_types
        assert "proposal_status_changed" in event_types

        apply_event = next(e for e in events if e["event_type"] == "patch_apply")
        assert apply_event["status"] == "success"
        assert apply_event["proposal_id"] == proposal_id


class TestDatasetReadinessFailures:
    """Failure-path coverage for dataset readiness and related commands."""

    def test_dataset_readiness_missing_dataset(self, tmp_path: Path) -> None:
        repo = _build_minimal_repo(tmp_path)
        result = runner.invoke(
            app,
            [
                "run",
                "dataset-readiness",
                str(tmp_path / "missing.csv"),
                "--repo",
                str(repo),
                "--out",
                str(tmp_path / "out"),
            ],
        )
        assert result.exit_code == 1
        assert "Dataset not found" in result.output

    def test_dataset_readiness_unsupported_format(self, tmp_path: Path) -> None:
        repo = _build_minimal_repo(tmp_path)
        dataset = tmp_path / "customers.txt"
        dataset.write_text("CUSTOMER_GROUP\nA\n", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "run",
                "dataset-readiness",
                str(dataset),
                "--repo",
                str(repo),
                "--out",
                str(tmp_path / "out"),
            ],
        )
        assert result.exit_code == 1
        assert "Unsupported" in result.output

    def test_dataset_readiness_blocked_no_matches(self, tmp_path: Path) -> None:
        repo = _build_minimal_repo(tmp_path)
        dataset = tmp_path / "unrelated.csv"
        _write_csv(dataset, ["TOTALLY_UNRELATED"], [["x"]])
        out_dir = tmp_path / "out"

        result = runner.invoke(
            app,
            [
                "run",
                "dataset-readiness",
                str(dataset),
                "--repo",
                str(repo),
                "--out",
                str(out_dir),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["verdict"] == "blocked"
        assert data["coverage"]["match_rate"] == 0.0

    def test_dataset_readiness_empty_dataset_blocked(self, tmp_path: Path) -> None:
        repo = _build_minimal_repo(tmp_path)
        dataset = tmp_path / "empty.csv"
        _write_csv(dataset, [], [])
        out_dir = tmp_path / "out"

        result = runner.invoke(
            app,
            [
                "run",
                "dataset-readiness",
                str(dataset),
                "--repo",
                str(repo),
                "--out",
                str(out_dir),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["verdict"] == "blocked"
        assert any(g["gap_code"] == "EMPTY_DATASET" for g in data["dataset_gaps"])

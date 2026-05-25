"""Tests for CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "modelops" in result.output


def test_cli_init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path / "new-repo")])
    assert result.exit_code == 0
    assert (tmp_path / "new-repo" / "modelops.config.yaml").exists()


def test_cli_validate(sample_repo: Path) -> None:
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Validation Results" in result.output


def test_cli_validate_json_output(sample_repo: Path) -> None:
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "is_valid" in data
    assert "error_count" in data
    assert "warning_count" in data
    assert "info_count" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_cli_build_index(sample_repo: Path) -> None:
    result = runner.invoke(app, ["build-index", "--repo", str(sample_repo), "--jsonl"])
    assert result.exit_code == 0
    assert "Index built" in result.output


def test_cli_health(sample_repo: Path) -> None:
    # Need index first
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["health", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Repository Health" in result.output


def test_cli_impact(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["impact", "FEP-S4-KNVV-KDGRP", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Impact Report" in result.output


def test_cli_profile_dataset_csv(sample_repo: Path) -> None:
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    result = runner.invoke(
        app, ["profile-dataset", str(csv_file), "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert "Profile saved" in result.output
    assert "Rows: 5" in result.output
    assert "Columns: 3" in result.output

    profile_path = sample_repo / "generated" / "dataset_profiles" / "customer_sample.json"
    assert profile_path.exists()


def test_cli_profile_dataset_xlsx(sample_repo: Path) -> None:
    xlsx_file = FIXTURES_DIR / "customer_sample.xlsx"
    result = runner.invoke(
        app, ["profile-dataset", str(xlsx_file), "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert "Profile saved" in result.output
    assert "Sheets: 1" in result.output

    profile_path = sample_repo / "generated" / "dataset_profiles" / "customer_sample.json"
    assert profile_path.exists()


def test_cli_profile_dataset_json_output(sample_repo: Path) -> None:
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    result = runner.invoke(
        app, ["profile-dataset", str(csv_file), "--repo", str(sample_repo), "--json"]
    )
    assert result.exit_code == 0
    assert '"dataset_id"' in result.output
    assert '"row_count"' in result.output


def test_cli_profile_dataset_privacy_warning(sample_repo: Path, tmp_path: Path) -> None:
    csv_file = tmp_path / "sensitive.csv"
    csv_file.write_text(
        "email,phone,customer_group\nalice@example.com,555-1234,A\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["profile-dataset", str(csv_file), "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert "Privacy warning" in result.output
    assert "email" in result.output
    assert "phone" in result.output

    # Verify saved profile has redacted samples
    profile_path = sample_repo / "generated" / "dataset_profiles" / "sensitive.json"
    assert profile_path.exists()
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    for col in data["columns"]:
        if col["name"] in ("email", "phone"):
            assert all(v == "[REDACTED]" for v in col["sample_values"])


def test_cli_profile_dataset_include_raw_samples(sample_repo: Path, tmp_path: Path) -> None:
    csv_file = tmp_path / "sensitive.csv"
    csv_file.write_text("email,customer_group\nalice@example.com,A\n", encoding="utf-8")
    result = runner.invoke(
        app, [
            "profile-dataset",
            str(csv_file),
            "--repo",
            str(sample_repo),
            "--include-raw-samples",
        ]
    )
    assert result.exit_code == 0
    profile_path = sample_repo / "generated" / "dataset_profiles" / "sensitive.json"
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    email_col = next(c for c in data["columns"] if c["name"] == "email")
    # Even with --include-raw-samples, high-risk columns are redacted
    assert all(v == "[REDACTED]" for v in email_col["sample_values"])


def test_cli_infer_model(sample_repo: Path) -> None:
    # First profile a dataset
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    runner.invoke(app, ["profile-dataset", str(csv_file), "--repo", str(sample_repo)])

    # Then infer model from the profile
    profile_path = sample_repo / "generated" / "dataset_profiles" / "customer_sample.json"
    result = runner.invoke(
        app, ["infer-model", str(profile_path), "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert "PatchProposal written" in result.output
    assert "PP-INFER-CUSTOMER-SAMPLE" in result.output

    proposal_path = sample_repo / "model" / "patch-proposals" / "PP-INFER-CUSTOMER-SAMPLE.md"
    assert proposal_path.exists()

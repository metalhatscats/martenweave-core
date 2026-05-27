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


def test_cli_impact_markdown_format(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app, ["impact", "FEP-S4-KNVV-KDGRP", "--repo", str(sample_repo), "--format", "markdown"]
    )
    assert result.exit_code == 0
    assert "# Impact Report: FEP-S4-KNVV-KDGRP" in result.output
    assert "| Object ID | Type | Name | Direction | Depth |" in result.output


def test_cli_impact_markdown_output_file(sample_repo: Path, tmp_path: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    output_path = tmp_path / "impact.md"
    result = runner.invoke(
        app,
        [
            "impact",
            "FEP-S4-KNVV-KDGRP",
            "--repo",
            str(sample_repo),
            "--format",
            "markdown",
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code == 0
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# Impact Report: FEP-S4-KNVV-KDGRP" in content


def test_cli_impact_json_format(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app, ["impact", "FEP-S4-KNVV-KDGRP", "--repo", str(sample_repo), "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["root_object_id"] == "FEP-S4-KNVV-KDGRP"


def test_cli_impact_table_output_requires_format(sample_repo: Path, tmp_path: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    output_path = tmp_path / "impact.txt"
    result = runner.invoke(
        app,
        [
            "impact",
            "FEP-S4-KNVV-KDGRP",
            "--repo",
            str(sample_repo),
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code == 1
    assert "--output requires --format markdown or --format json" in result.output


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


# Global option tests ---------------------------------------------------------


def test_cli_quiet_validate_no_output_on_success(sample_repo: Path) -> None:
    result = runner.invoke(
        app, ["--quiet", "validate", "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert result.output == ""


def test_cli_quiet_validate_shows_errors(sample_repo: Path) -> None:
    # Create an invalid object to trigger an error
    bad_file = sample_repo / "model" / "BAD-ID.md"
    bad_file.write_text(
        "---\nid: bad-id-lower\ntype: Attribute\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["--quiet", "validate", "--repo", str(sample_repo)]
    )
    assert result.exit_code == 1
    assert "bad-id-lower" in result.output


def test_cli_no_color_health_no_ansi_codes(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app, ["--no-color", "health", "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert "\033[" not in result.output


def test_cli_json_output_unaffected_by_quiet(sample_repo: Path) -> None:
    result = runner.invoke(
        app, ["--quiet", "validate", "--repo", str(sample_repo), "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["is_valid"] is True


def test_cli_quiet_and_no_color_together(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app, ["--quiet", "--no-color", "health", "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert result.output == ""
    assert "\033[" not in result.output


def test_cli_validate_strict_exits_2_on_warnings(sample_repo: Path) -> None:
    """--strict should exit 2 when warnings exist but no errors."""
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--strict"])
    assert result.exit_code == 2
    assert "Validation Results" in result.output


def test_cli_validate_strict_exits_0_on_clean(tmp_path: Path) -> None:
    """--strict should exit 0 when no warnings and no errors."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: active\n"
        "name: Test Domain\n"
        "schema_version: \"1.0\"\n"
        "---\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate", "--repo", str(tmp_path), "--strict"])
    assert result.exit_code == 0


def test_cli_validate_strict_exits_1_on_errors(sample_repo: Path) -> None:
    """--strict should exit 1 when errors exist regardless of strict mode."""
    bad_file = sample_repo / "model" / "BAD-ID.md"
    bad_file.write_text(
        "---\nid: bad-id-lower\ntype: Attribute\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--strict"])
    assert result.exit_code == 1
    assert "bad-id-lower" in result.output


def test_cli_validate_strict_json_output(sample_repo: Path) -> None:
    """--strict with --json should still output JSON and exit 2 on warnings."""
    result = runner.invoke(
        app, ["validate", "--repo", str(sample_repo), "--strict", "--json"]
    )
    assert result.exit_code == 2
    data = json.loads(result.output)
    assert data["is_valid"] is True
    assert data["warning_count"] > 0

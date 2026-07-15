"""Workbook-first pilot bootstrap tests."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "pilot" / "sap_customer_mapping.xlsx"
DATASET_FIXTURE = Path(__file__).parent / "fixtures" / "customer_sample.csv"


def test_bootstrap_assessment_creates_proposal_only_pilot_repo(tmp_path: Path) -> None:
    repo = tmp_path / "pilot"
    result = runner.invoke(
        app,
        [
            "bootstrap-assessment",
            "--mapping",
            str(FIXTURE),
            "--name",
            "SAP Customer Pilot",
            "--out-repo",
            str(repo),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    proposals = list((repo / "model" / "patch-proposals").glob("*.md"))
    assert len(proposals) == 1
    assert not list((repo / "model").glob("DOMAIN-*.md"))
    assert (repo / "generated" / "bootstrap-assessment" / "bootstrap-report.json").exists()

    validated = runner.invoke(app, ["validate", "--repo", str(repo)])
    assert validated.exit_code == 0, validated.output
    proposal_validation = runner.invoke(
        app, ["proposal", "validate", "--repo", str(repo), proposals[0].stem]
    )
    assert proposal_validation.exit_code == 0, proposal_validation.output


def test_bootstrap_assessment_is_deterministic_and_rejects_nonempty_target(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    command = ["bootstrap-assessment", "--mapping", str(FIXTURE), "--name", "SAP Pilot"]
    assert runner.invoke(app, [*command, "--out-repo", str(first)]).exit_code == 0
    assert runner.invoke(app, [*command, "--out-repo", str(second)]).exit_code == 0
    first_proposal = next((first / "model" / "patch-proposals").glob("*.md"))
    second_proposal = next((second / "model" / "patch-proposals").glob("*.md"))
    assert first_proposal.name == second_proposal.name
    assert first_proposal.read_text() == second_proposal.read_text()
    repeated = runner.invoke(app, [*command, "--out-repo", str(first)])
    assert repeated.exit_code == 1
    assert "must be empty" in repeated.output


def test_bootstrap_assessment_profiles_an_optional_dataset(tmp_path: Path) -> None:
    repo = tmp_path / "pilot"
    result = runner.invoke(
        app,
        [
            "bootstrap-assessment",
            "--mapping",
            str(FIXTURE),
            "--dataset",
            str(DATASET_FIXTURE),
            "--name",
            "SAP Pilot",
            "--out-repo",
            str(repo),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (repo / "generated" / "bootstrap-assessment" / "bootstrap-report.json").read_text()
    assert '"dataset_profile"' in report
    assert '"customer_sample"' in report


def test_bootstrap_assessment_preserves_safe_diagnostics_for_unsupported_workbook(
    tmp_path: Path,
) -> None:
    unsupported = tmp_path / "unsupported.xlsx"
    unsupported.write_text("not an xlsx workbook", encoding="utf-8")
    repo = tmp_path / "pilot"

    result = runner.invoke(
        app,
        [
            "bootstrap-assessment",
            "--mapping",
            str(unsupported),
            "--name",
            "SAP Pilot",
            "--out-repo",
            str(repo),
        ],
    )

    assert result.exit_code == 1
    assert "Unsupported workbook layout" in result.output
    assert (repo / "modelops.config.yaml").exists()
    assert (repo / "generated" / "bootstrap-assessment" / "bootstrap-diagnostics.md").exists()
    assert not list((repo / "model" / "patch-proposals").glob("*.md"))

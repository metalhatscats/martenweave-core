"""Tests for bootstrap-assessment command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()

FIXTURE = Path(__file__).parent / "fixtures" / "pilot" / "sap_customer_mapping.xlsx"


def test_bootstrap_assessment_creates_repository_and_proposal(tmp_path: Path) -> None:
    out_repo = tmp_path / "pilot-repo"

    result = runner.invoke(
        app,
        [
            "bootstrap-assessment",
            "--mapping",
            str(FIXTURE),
            "--name",
            "SAP Customer Pilot",
            "--out-repo",
            str(out_repo),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_repo / "modelops.config.yaml").exists()
    assert (out_repo / "model").is_dir()
    assert (out_repo / "generated").is_dir()
    proposals = list((out_repo / "model" / "patch-proposals").glob("*.md"))
    assert len(proposals) >= 1


def test_bootstrap_assessment_writes_report(tmp_path: Path) -> None:
    out_repo = tmp_path / "pilot-repo"

    result = runner.invoke(
        app,
        [
            "bootstrap-assessment",
            "--mapping",
            str(FIXTURE),
            "--name",
            "SAP Customer Pilot",
            "--out-repo",
            str(out_repo),
        ],
    )
    assert result.exit_code == 0, result.output
    report_md = out_repo / "bootstrap-report.md"
    report_json = out_repo / "bootstrap-report.json"
    assert report_md.exists()
    assert report_json.exists()
    data = json.loads(report_json.read_text(encoding="utf-8"))
    assert data["repo_name"] == "SAP Customer Pilot"
    assert data["inferred_objects_count"] > 0
    assert "warnings" in data


def test_bootstrap_assessment_is_deterministic(tmp_path: Path) -> None:
    out1 = tmp_path / "repo1"
    out2 = tmp_path / "repo2"

    for out in (out1, out2):
        result = runner.invoke(
            app,
            [
                "bootstrap-assessment",
                "--mapping",
                str(FIXTURE),
                "--name",
                "SAP Customer Pilot",
                "--out-repo",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output

    prop1 = list((out1 / "model" / "patch-proposals").glob("*.md"))[0]
    prop2 = list((out2 / "model" / "patch-proposals").glob("*.md"))[0]
    assert prop1.read_text(encoding="utf-8") == prop2.read_text(encoding="utf-8")


def test_bootstrap_assessment_validates_repository(tmp_path: Path) -> None:
    out_repo = tmp_path / "pilot-repo"

    result = runner.invoke(
        app,
        [
            "bootstrap-assessment",
            "--mapping",
            str(FIXTURE),
            "--name",
            "SAP Customer Pilot",
            "--out-repo",
            str(out_repo),
        ],
    )
    assert result.exit_code == 0, result.output

    validate_result = runner.invoke(
        app,
        ["validate", "--repo", str(out_repo)],
    )
    assert validate_result.exit_code == 0, validate_result.output


def test_bootstrap_assessment_fails_on_unsupported_layout(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xlsx"
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["foo", "bar"])
    ws.append(["a", "b"])
    wb.save(bad)
    wb.close()

    out_repo = tmp_path / "pilot-repo"
    result = runner.invoke(
        app,
        [
            "bootstrap-assessment",
            "--mapping",
            str(bad),
            "--name",
            "Bad Pilot",
            "--out-repo",
            str(out_repo),
        ],
    )
    assert result.exit_code == 1, result.output
    assert "unsupported" in result.output.lower() or "missing" in result.output.lower()

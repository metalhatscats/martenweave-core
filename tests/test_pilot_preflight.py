"""Tests for the pilot input privacy preflight command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()

MAPPING_WORKBOOK = (
    Path(__file__).parent / "fixtures" / "pilot" / "sap_customer_mapping.xlsx"
)
SAMPLE_DATASET = (
    Path(__file__).parent.parent
    / "examples"
    / "customer_bp_model"
    / "data"
    / "samples"
    / "customer_messy.csv"
)


def _write_evidence_with_secret(path: Path) -> None:
    path.write_text(
        "# Pilot evidence\n\n"
        "The legacy API password=supersecret123 was found in a test script.\n",
        encoding="utf-8",
    )


def _write_unsupported_file(path: Path) -> None:
    path.write_bytes(b"\x00\x01\x02\x03")


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_pilot_preflight_produces_reports_and_detects_issues(tmp_path: Path) -> None:
    out_dir = tmp_path / "preflight"
    evidence = tmp_path / "evidence.md"
    unsupported = tmp_path / "raw_dump.bin"
    _write_evidence_with_secret(evidence)
    _write_unsupported_file(unsupported)

    result = runner.invoke(
        app,
        [
            "pilot-preflight",
            "--mapping",
            str(MAPPING_WORKBOOK),
            "--dataset",
            str(SAMPLE_DATASET),
            "--evidence",
            str(evidence),
            "--evidence",
            str(unsupported),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (out_dir / "preflight_report.json").exists()
    assert (out_dir / "preflight_report.md").exists()

    report = json.loads((out_dir / "preflight_report.json").read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert "files" in report
    by_path = {f["path"]: f for f in report["files"]}

    mapping = by_path[str(MAPPING_WORKBOOK)]
    assert mapping["status"] == "allowed"
    assert mapping["file_type"] == "xlsx"
    assert "sheet_names" in mapping

    dataset = by_path[str(SAMPLE_DATASET)]
    assert dataset["status"] == "warning"
    assert any("sensitive" in w.lower() for w in dataset["warnings"])

    evidence_result = by_path[str(evidence)]
    assert evidence_result["status"] == "warning"
    assert evidence_result["secret_findings_count"] > 0

    unsupported_result = by_path[str(unsupported)]
    assert unsupported_result["status"] == "blocked"

    # Raw values must not be emitted by default.
    assert "sample_values" not in json.dumps(report)

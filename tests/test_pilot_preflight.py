"""Tests for the pilot input privacy preflight command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.pilot.structural_scan import scan_workbook_structure

runner = CliRunner()

MAPPING_WORKBOOK = Path(__file__).parent / "fixtures" / "pilot" / "sap_customer_mapping.xlsx"
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
        "# Pilot evidence\n\nThe legacy API password=supersecret123 was found in a test script.\n",
        encoding="utf-8",
    )


def _write_unsupported_file(path: Path) -> None:
    path.write_bytes(b"\x00\x01\x02\x03")


def _write_multitable_workbook(path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")

    workbook = openpyxl.Workbook()
    combined = workbook.active
    combined.title = "Combined mappings"
    combined.append(["Customer mapping section"])
    combined.append(["Source Field", "Target Table", "Target Field", "Owner", "Status"])
    combined.append(["KUNNR", "KNVV", "KUNNR", "MDM", "active"])
    combined.append(["Source Field", "Target Table", "Target Field", "Owner", "Status"])
    combined.append(["LIFNR", "LFA1", "LIFNR", "MDM", "active"])

    validation = workbook.create_sheet("Validation Results")
    validation.append(["Validation summary"])
    validation.append(["Rule", "Status", "Comment"])
    validation.append(["Customer owner present", "pass", "Checked"])

    workbook.save(path)


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
    assert (out_dir / "workbook_manifest.json").exists()
    assert (out_dir / "workbook_suggestions.json").exists()
    assert (out_dir / "workbook_suggestions.md").exists()
    assert (out_dir / "workbook_suggestion_review.xlsx").exists()

    report = json.loads((out_dir / "preflight_report.json").read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert "files" in report
    assert str(out_dir / "workbook_manifest.json") in report["generated_artifacts"]
    assert str(out_dir / "workbook_suggestions.json") in report["generated_artifacts"]
    assert str(out_dir / "workbook_suggestions.md") in report["generated_artifacts"]
    assert str(out_dir / "workbook_suggestion_review.xlsx") in report["generated_artifacts"]
    by_path = {f["path"]: f for f in report["files"]}

    suggestions = json.loads((out_dir / "workbook_suggestions.json").read_text(encoding="utf-8"))
    assert suggestions["summary"]["suggestion_count"] > 0
    assert suggestions["summary"]["counts_by_status"]["unresolved"] > 0
    assert any(item["suggestion_id"].startswith("WSUG-") for item in suggestions["suggestions"])
    assert all(item["status"] == "unresolved" for item in suggestions["suggestions"])

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
    assert "Suggestion count" in (out_dir / "workbook_suggestions.md").read_text(encoding="utf-8")


def test_structural_scan_detects_title_rows_and_repeated_headers_deterministically(
    tmp_path: Path,
) -> None:
    workbook = tmp_path / "repeated-sections.xlsx"
    _write_multitable_workbook(workbook)

    first = scan_workbook_structure(workbook).to_dict()
    second = scan_workbook_structure(workbook).to_dict()

    assert first == second
    assert first["scanner_version"] == "1.0"
    assert first["workbook_warnings"]

    combined = next(sheet for sheet in first["sheets"] if sheet["name"] == "Combined mappings")
    assert combined["purpose"] == "mapping"
    assert combined["probable_header_rows"] == [2, 4]
    assert len(combined["tables"]) == 2
    assert combined["tables"][0]["title_rows"] == [1]
    assert combined["tables"][0]["header_row"] == 2
    assert combined["tables"][1]["header_row"] == 4
    assert combined["tables"][1]["repeated_header"] is True
    assert combined["tables"][0]["detected_columns"][0]["role"] == "source_field"
    assert combined["tables"][0]["detected_columns"][1]["role"] == "target_table"

    validation = next(sheet for sheet in first["sheets"] if sheet["name"] == "Validation Results")
    assert validation["purpose"] == "validation_results"
    assert validation["probable_header_rows"] == [2]

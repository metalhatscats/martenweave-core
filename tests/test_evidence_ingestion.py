"""Tests for deterministic proposal-only evidence ingestion."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.evidence_ingestion import ingest_evidence
from modelops_core.patching.patch_validator import validate_patch_proposal
from modelops_core.validation.result import ValidationSeverity

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures" / "evidence"


def test_csv_validation_report_becomes_valid_proposal_without_canonical_writes(
    sample_repo: Path,
) -> None:
    source = FIXTURES / "sample_validation_report.csv"
    before = sorted(path.relative_to(sample_repo) for path in (sample_repo / "model").rglob("*"))

    result = ingest_evidence(source, sample_repo / "model")

    assert result.finding_count == 2
    assert result.proposal["generated_by"] == "deterministic_evidence_ingestion"
    assert source.name in result.proposal["source_evidence"]
    assert not [
        finding
        for finding in validate_patch_proposal(result.proposal, sample_repo / "model")
        if finding.severity == ValidationSeverity.ERROR
    ]
    after = sorted(path.relative_to(sample_repo) for path in (sample_repo / "model").rglob("*"))
    assert after == before


def test_markdown_note_becomes_valid_proposal(sample_repo: Path, tmp_path: Path) -> None:
    note = tmp_path / "review-note.md"
    note.write_text(
        "# Review\n\n- Missing owner for ATTR-CUST-SALES-CUSTOMER-GROUP\n"
        "- Unresolved mapping for FEP-S4-KNVV-KDGRP\n",
        encoding="utf-8",
    )

    result = ingest_evidence(note, sample_repo / "model")

    assert result.finding_count == 2
    assert all(operation["object_type"] == "Issue" for operation in result.proposal["operations"])


def test_xlsx_validation_report_becomes_valid_proposal(sample_repo: Path, tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    source = tmp_path / "validation-report.xlsx"
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["severity", "rule_id", "message"])
    worksheet.append(["high", "OWNER_REQUIRED", "Missing owner for customer mapping"])
    workbook.save(source)
    workbook.close()

    result = ingest_evidence(source, sample_repo / "model")

    assert result.finding_count == 1
    assert "validation_report_xlsx" in result.proposal["source_evidence"]


def test_evidence_ingest_cli_writes_external_proposal_and_validates_it(
    sample_repo: Path, tmp_path: Path
) -> None:
    output = tmp_path / "evidence-proposal.md"
    result = runner.invoke(
        app,
        [
            "evidence",
            "ingest",
            "--repo",
            str(sample_repo),
            "--from",
            str(FIXTURES / "sample_validation_report.csv"),
            "--out",
            str(output),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    validated = runner.invoke(
        app,
        ["proposal", "validate", "--repo", str(sample_repo), "--proposal", str(output), "--json"],
    )
    assert validated.exit_code == 0, validated.output
    assert '"error_count": 0' in validated.output


def test_evidence_ingest_rejects_unsupported_file_without_output(
    sample_repo: Path, tmp_path: Path
) -> None:
    source = tmp_path / "unsupported.json"
    output = tmp_path / "evidence-proposal.md"
    source.write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "evidence",
            "ingest",
            "--repo",
            str(sample_repo),
            "--from",
            str(source),
            "--out",
            str(output),
        ],
    )

    assert result.exit_code == 1
    assert "Evidence must be Markdown, text, CSV, or XLSX" in result.output
    assert not output.exists()

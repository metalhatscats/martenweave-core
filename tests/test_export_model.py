"""Tests for model export service and CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.exports import export_model_csv, export_model_xlsx

runner = CliRunner()


def test_export_model_csv(temp_model_dir: Path) -> None:
    result = export_model_csv(temp_model_dir)
    assert len(result) > 0
    for f in result:
        assert f.exists()
        assert f.suffix == ".csv"


def test_export_model_csv_columns(temp_model_dir: Path) -> None:
    export_model_csv(temp_model_dir)
    csv_dir = temp_model_dir.parent / "generated" / "exports" / "csv"
    domain_csv = csv_dir / "masterdatadomain.csv"
    assert domain_csv.exists()
    content = domain_csv.read_text()
    assert "id" in content
    assert "type" in content
    assert "status" in content
    assert "DOMAIN-TEST" in content


def test_export_model_xlsx(temp_model_dir: Path) -> None:
    pytest.importorskip("openpyxl")
    path = export_model_xlsx(temp_model_dir)
    assert path.exists()
    assert path.suffix == ".xlsx"


def test_export_model_xlsx_sheets(temp_model_dir: Path) -> None:
    pytest.importorskip("openpyxl")
    from openpyxl import load_workbook

    path = export_model_xlsx(temp_model_dir)
    wb = load_workbook(path)
    sheet_names = wb.sheetnames
    assert len(sheet_names) > 0
    assert any("masterdatadomain" in s.lower() for s in sheet_names)
    wb.close()


def test_cli_export_model_csv(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    result = runner.invoke(app, ["export-model", "--repo", repo, "--format", "csv"])
    assert result.exit_code == 0
    assert "Exported" in result.output
    assert ".csv" in result.output


def test_cli_export_model_xlsx(temp_model_dir: Path) -> None:
    pytest.importorskip("openpyxl")
    repo = str(temp_model_dir.parent)
    result = runner.invoke(app, ["export-model", "--repo", repo, "--format", "xlsx"])
    assert result.exit_code == 0
    assert "Exported" in result.output
    assert ".xlsx" in result.output


def test_cli_export_model_unknown_format(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    result = runner.invoke(app, ["export-model", "--repo", repo, "--format", "pdf"])
    assert result.exit_code == 1
    assert "Unknown format" in result.output

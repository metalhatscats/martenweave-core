"""Tests for the one-command local readiness workflow."""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_start_creates_readiness_workspace_without_applying_inferred_model(tmp_path: Path) -> None:
    workspace = tmp_path / "customer-workspace"

    result = runner.invoke(
        app,
        [
            "start",
            str(FIXTURES_DIR / "customer_sample.csv"),
            "--out",
            str(workspace),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["input"]["format"] == "csv"
    assert (
        manifest["generated_outputs"]["profile"]
        == "generated/dataset_profiles/customer_sample.json"
    )
    assert (workspace / "generated" / "readiness" / "readiness.md").is_file()
    assert (workspace / "generated" / "start_manifest.json").is_file()
    assert (workspace / "model" / "patch-proposals" / "PP-INFER-CUSTOMER-SAMPLE.md").is_file()
    assert not list((workspace / "model").glob("ATTR-*.md"))


def test_start_rejects_unsupported_input_without_creating_workspace(tmp_path: Path) -> None:
    input_file = tmp_path / "customers.txt"
    input_file.write_text("not a supported data format", encoding="utf-8")
    workspace = tmp_path / "workspace"

    result = runner.invoke(app, ["start", str(input_file), "--out", str(workspace)])

    assert result.exit_code == 1
    assert "Unsupported input format" in result.output
    assert not workspace.exists()


def test_start_supports_csv_xlsx_xml_and_json_without_opening_browser(tmp_path: Path) -> None:
    inputs = {
        "csv": "CUSTOMER_GROUP\nA\n",
        "json": '[{"CUSTOMER_GROUP": "A"}]',
        "xml": "<customers><customer><CUSTOMER_GROUP>A</CUSTOMER_GROUP></customer></customers>",
    }
    for extension, content in inputs.items():
        input_file = tmp_path / f"customers.{extension}"
        input_file.write_text(content, encoding="utf-8")
        workspace = tmp_path / f"{extension}-workspace"

        result = runner.invoke(
            app,
            ["start", str(input_file), "--out", str(workspace), "--no-open", "--json"],
        )

        assert result.exit_code == 0, result.output
        assert json.loads(result.output)["input"]["format"] == extension

    xlsx_file = tmp_path / "customers.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["CUSTOMER_GROUP"])
    worksheet.append(["A"])
    workbook.save(xlsx_file)
    xlsx_workspace = tmp_path / "xlsx-workspace"

    result = runner.invoke(
        app,
        ["start", str(xlsx_file), "--out", str(xlsx_workspace), "--no-open", "--json"],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["input"]["format"] == "xlsx"

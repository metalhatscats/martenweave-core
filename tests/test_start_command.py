"""Tests for the one-command local readiness workflow."""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.repository import scan_repository
from modelops_core.repository.parser import parse_file
from modelops_core.validation import validate_objects

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


def test_start_workspace_remains_valid_with_draft_created_object_references(
    tmp_path: Path,
) -> None:
    _, workspace = _run_start(tmp_path)

    parsed = [parse_file(path) for path in scan_repository(workspace / "model")]
    summary = validate_objects(parsed)

    assert summary.is_valid, summary.results


def test_start_can_assess_against_packaged_sap_customer_context(tmp_path: Path) -> None:
    workspace = tmp_path / "sap-customer-workspace"
    result = runner.invoke(
        app,
        [
            "start",
            str(FIXTURES_DIR / "customer_sample.csv"),
            "--out",
            str(workspace),
            "--template",
            "sap_bp_customer_migration",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["canonical_model"]["created_workspace_seed_only"] is False
    assert manifest["canonical_model"]["template"] == "sap_bp_customer_migration"
    assert manifest["canonical_model"]["context_domain"] == "DOMAIN-CUSTOMER-MIGRATION"
    assert (workspace / "model" / "FEP-S4-KNVV-KDGRP.md").is_file()
    proposal = parse_file(
        workspace / "model" / "patch-proposals" / "PP-INFER-CUSTOMER-SAMPLE.md"
    ).frontmatter
    assert proposal["validation_status"] == "valid"
    assert not [item for item in proposal["validation_results"] if item["severity"] == "ERROR"]


def _run_start(tmp_path: Path, fixture: str = "customer_sample.csv") -> tuple[dict, Path]:
    workspace = tmp_path / "workspace"
    result = runner.invoke(
        app,
        ["start", str(FIXTURES_DIR / fixture), "--out", str(workspace), "--no-open", "--json"],
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output), workspace


def test_start_manifest_json_and_markdown_share_one_finding_count(tmp_path: Path) -> None:
    """Manifest, readiness.json, and readiness.md must report the same finding count."""
    manifest, workspace = _run_start(tmp_path)
    readiness_json = json.loads(
        (workspace / "generated" / "readiness" / "readiness.json").read_text(encoding="utf-8")
    )
    markdown = (workspace / "generated" / "readiness" / "readiness.md").read_text(encoding="utf-8")

    dataset_gaps = readiness_json["dataset_gaps"]
    model_gaps = readiness_json["model_gaps"]
    total = len(dataset_gaps) + len(model_gaps)

    assert manifest["readiness"]["dataset_gaps"] == len(dataset_gaps)
    assert manifest["readiness"]["model_gaps"] == len(model_gaps)
    assert manifest["readiness"]["total_findings"] == total
    assert readiness_json["gap_summary"]["total_gap_count"] == total
    assert f"- Total gap count: {total}" in markdown
    # Issue #623 assertion: the report summary equals the manifest dataset_gaps count
    # for the no-AI CSV fixture (no model-side gaps on a seed workspace).
    assert model_gaps == []
    assert f"- Total gap count: {manifest['readiness']['dataset_gaps']}" in markdown


def test_start_blocked_report_names_next_action_and_finding_ids(tmp_path: Path) -> None:
    """A blocked report links every displayed finding to a stable ID and names one action."""
    manifest, workspace = _run_start(tmp_path)
    assert manifest["readiness"]["verdict"] == "blocked"
    readiness_json = json.loads(
        (workspace / "generated" / "readiness" / "readiness.json").read_text(encoding="utf-8")
    )
    markdown = (workspace / "generated" / "readiness" / "readiness.md").read_text(encoding="utf-8")

    assert "## Verdict: blocked" in markdown
    assert "**Recommended next action:**" in markdown
    for gap in readiness_json["dataset_gaps"]:
        assert gap["finding"]["id"] in markdown
    assert "readiness.json" in markdown  # evidence link


def test_start_report_separates_facts_assumptions_ai_and_human_review(tmp_path: Path) -> None:
    """Facts, assumptions, AI suggestions, and human dispositions are distinct sections."""
    _, workspace = _run_start(tmp_path)
    markdown = (workspace / "generated" / "readiness" / "readiness.md").read_text(encoding="utf-8")

    assert "## Facts (deterministic)" in markdown
    assert "## Assumptions and privacy boundaries" in markdown
    assert "## AI suggestions" in markdown
    assert "## Human review and dispositions" in markdown
    assert "No AI provider" in markdown


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

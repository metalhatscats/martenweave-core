"""Regression tests for semantic mapping-workbook comparison."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.pilot.workbook_comparison import compare_mapping_workbooks

runner = CliRunner()


def _write_mapping(path: Path, *, changed: bool) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    mapping = workbook.active
    assert mapping is not None
    mapping.title = "Customer mapping"
    mapping.append(
        [
            "Source System",
            "Source Table",
            "Source Field",
            "Target Table",
            "Target Field",
            "Condition",
            "Transformation",
            "Owner",
            "Status",
            "Validation Rule",
        ]
    )
    mapping.append(
        [
            "Legacy CRM",
            "KNA1",
            "CUSTOMER_GROUP",
            "KNVV",
            "KDGRP",
            "if sales area" if changed else "",
            "normalize group" if changed else "direct",
            "sales.steward" if changed else "mdm.steward",
            "approved" if changed else "draft",
            "VAL-CUSTOMER-GROUP" if changed else "",
        ]
    )
    decisions = workbook.create_sheet("Decisions")
    decisions.append(["Decision ID", "Topic", "Decision", "Owner", "Status"])
    decisions.append(
        [
            "DEC-GROUP",
            "Customer group",
            "Use S/4 list" if changed else "TBD",
            "sales.lead",
            "approved" if changed else "pending",
        ]
    )
    workbook.save(path)
    workbook.close()


def test_semantic_workbook_comparison_detects_mapping_governance_and_impact(
    sample_repo: Path, tmp_path: Path
) -> None:
    base = tmp_path / "base.xlsx"
    head = tmp_path / "head.xlsx"
    _write_mapping(base, changed=False)
    _write_mapping(head, changed=True)

    report = compare_mapping_workbooks(base, head, sample_repo)

    assert len(report.mapping_changes) == 1
    assert set(report.mapping_changes[0]["changes"]) == {
        "condition",
        "transformation",
        "owner",
        "status",
        "validation_rule",
    }
    assert report.decision_changes[0]["change_type"] == "decision_changed"
    assert any(item["object_id"] == "FEP-S4-KNVV-KDGRP" for item in report.model_impact)


def test_compare_workbooks_cli_writes_client_review_artifacts(
    sample_repo: Path, tmp_path: Path
) -> None:
    base = tmp_path / "base.xlsx"
    head = tmp_path / "head.xlsx"
    out = tmp_path / "comparison"
    _write_mapping(base, changed=False)
    _write_mapping(head, changed=True)

    result = runner.invoke(
        app,
        [
            "assessment",
            "compare-workbooks",
            str(base),
            str(head),
            "--repo",
            str(sample_repo),
            "--out",
            str(out),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["counts"]["changed"] == 1
    assert (out / "mapping-workbook-comparison.json").exists()
    assert (out / "mapping-workbook-comparison.html").exists()
    assert (out / "mapping-workbook-comparison.xlsx").exists()

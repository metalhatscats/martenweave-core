"""Golden assessment test for the realistic SAP mapping workbook fixture.

The fixture is a fully synthetic Customer/Business Partner mapping workbook with
known, deliberately-injected data-quality findings. This test runs the full
migration-assessment workflow and asserts that each finding class is detected
with the expected cardinality.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pilot"
MAPPING_WORKBOOK = FIXTURE_DIR / "sap_customer_mapping.xlsx"


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_pilot_mapping_workbook_golden_findings(sample_repo: Path, tmp_path: Path) -> None:
    """Run migration-assessment against the synthetic workbook and verify findings."""
    out_dir = tmp_path / "golden-assessment"

    result = runner.invoke(
        app,
        [
            "run",
            "migration-assessment",
            "--repo",
            str(sample_repo),
            "--mapping",
            str(MAPPING_WORKBOOK),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "mapping_profile.json").exists()

    profile = json.loads((out_dir / "mapping_profile.json").read_text(encoding="utf-8"))

    # The workbook contains synthetic rows across multiple sheets.
    assert profile["total_rows"] >= 75

    # Missing owner rows span the mapping and value-mapping sheets.
    assert len(profile["missing_owner_rows"]) == 5

    # Missing target table/field mappings (rows with blank target_table or target_field).
    assert len(profile["missing_mapping_rows"]) == 2

    # Obsolete source fields explicitly marked status=obsolete.
    assert len(profile["obsolete_rows"]) == 2

    # Conditional rules without an accompanying validation_rule.
    assert len(profile["validation_coverage_gaps"]) == 2

    # Pending decisions/mappings (Decisions sheet + Value_Mappings VIP row).
    assert len(profile["unresolved_decisions"]) == 2

    # Conflicting decisions on the same topic in the Decisions sheet.
    assert len(profile["conflicting_decisions"]) == 1

    # Same SAP target table/field reached by more than one source field.
    assert len(profile["duplicate_target_rows"]) == 5

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    status_names = {s["name"]: s["status"] for s in manifest["stage_statuses"]}
    assert status_names["validation"] == "success"
    assert status_names["index"] == "success"
    assert status_names["mapping_profile"] == "success"
    assert status_names["assessment_package"] == "success"
    assert status_names["review_pack"] == "success"

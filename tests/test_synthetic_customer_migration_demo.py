"""Regression coverage for the isolated synthetic multi-system demo."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_synthetic_customer_migration_demo_is_valid_and_traceable(tmp_path: Path) -> None:
    """The fictional source-to-target scenario remains runnable without production data."""
    repo = Path(__file__).resolve().parent.parent / "examples" / "synthetic_customer_migration_demo"

    validation = runner.invoke(app, ["validate", "--repo", str(repo), "--json"])
    assert validation.exit_code == 0, validation.output
    report = json.loads(validation.output)
    assert report["is_valid"] is True
    assert report["error_count"] == 0

    output_repo = tmp_path / "synthetic-demo-index"
    output_repo.mkdir()
    # Index the checked-in source in place; generated outputs are deliberately ignored.
    indexed = runner.invoke(app, ["build-index", "--repo", str(repo), "--jsonl"])
    assert indexed.exit_code == 0, indexed.output

    trace = runner.invoke(
        app,
        ["trace", "FEP-DEMO-HUB-GOLDEN-NAME", "--repo", str(repo), "--json"],
    )
    assert trace.exit_code == 0, trace.output
    trace_data = json.loads(trace.output)
    traced_ids = {node["object_id"] for node in trace_data["nodes"]}
    assert "MAP-DEMO-NIMBUS-NAME-TO-HUB" in traced_ids
    assert "MAP-DEMO-ORBIT-NAME-TO-HUB" in traced_ids
    assert "MAP-DEMO-HUB-NAME-TO-S4" in traced_ids

    impact = runner.invoke(
        app,
        ["impact", "FEP-S4-KNVV-KDGRP", "--repo", str(repo), "--json"],
    )
    assert impact.exit_code == 0, impact.output
    impact_data = json.loads(impact.output)
    affected_ids = {item["object_id"] for item in impact_data["affected_objects"]}
    assert "MAP-CUSTOMER-GROUP" in affected_ids
    assert "STEP-DEMO-HUB-GROUP-TO-S4" in affected_ids

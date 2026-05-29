"""End-to-end CLI demo flow test."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_e2e_init_validate_build_health_impact(tmp_path: Path) -> None:
    repo = tmp_path / "demo-repo"

    # 1. Init
    result = runner.invoke(app, ["init", str(repo)])
    assert result.exit_code == 0
    assert (repo / "modelops.config.yaml").exists()

    # 2. Validate
    result = runner.invoke(app, ["validate", "--repo", str(repo)])
    assert result.exit_code == 0

    # 3. Build index
    result = runner.invoke(app, ["build-index", "--repo", str(repo), "--jsonl"])
    assert result.exit_code == 0
    assert (repo / "generated" / "modelops.db").exists()
    assert (repo / "generated" / "search_documents.jsonl").exists()
    assert (repo / "generated" / "lineage_edges.jsonl").exists()

    # 4. Health
    result = runner.invoke(app, ["health", "--repo", str(repo)])
    assert result.exit_code == 0

    # 5. Impact on example domain
    result = runner.invoke(app, ["impact", "DOMAIN-EXAMPLE", "--repo", str(repo)])
    assert result.exit_code == 0


def test_e2e_propose_patch(sample_repo: Path) -> None:
    note_file = sample_repo / "data" / "patch-note.md"
    note_file.parent.mkdir(parents=True, exist_ok=True)
    note_file.write_text(
        "Update CUSTOMER GROUP mapping for KNVV-KDGRP based on CH01-A17 decision.\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["propose-patch", "--from", str(note_file), "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert "Patch proposal written" in result.output
    assert (sample_repo / "model" / "patch-proposals" / "PP-SCAFFOLD-001.md").exists()


def test_e2e_v0_1_command_surface(sample_repo: Path) -> None:
    """Exercise the broader v0.1 CLI surface on a populated repository."""
    repo = str(sample_repo)

    # 1. Scorecard
    result = runner.invoke(app, ["scorecard", "--repo", repo])
    assert result.exit_code == 0
    assert "readiness" in result.output.lower() or "score" in result.output.lower()

    # 2. Analyze
    result = runner.invoke(app, ["analyze", "--repo", repo, "--json"])
    assert result.exit_code == 0

    # 3. Trace
    result = runner.invoke(
        app,
        [
            "trace",
            "FEP-S4-KNVV-KDGRP",
            "--repo",
            repo,
            "--direction",
            "both",
            "--json",
        ],
    )
    assert result.exit_code == 0

    # 4. Search
    result = runner.invoke(app, ["search", "Customer Group", "--repo", repo, "--json"])
    assert result.exit_code == 0

    # 5. Query
    result = runner.invoke(app, ["query", "--type", "Attribute", "--repo", repo, "--json"])
    assert result.exit_code == 0

    # 6. Export model CSV
    result = runner.invoke(app, ["export-model", "--repo", repo, "--format", "csv"])
    assert result.exit_code == 0

    # 7. Export model XLSX
    result = runner.invoke(app, ["export-model", "--repo", repo, "--format", "xlsx"])
    assert result.exit_code == 0

    # 8. Usage report
    result = runner.invoke(app, ["usage-report", "--repo", repo, "--json"])
    assert result.exit_code == 0

    # 9. Audit log
    result = runner.invoke(app, ["audit-log", "--repo", repo, "--json"])
    assert result.exit_code == 0

    # 10. Config guard
    result = runner.invoke(app, ["config-guard", "--repo", repo, "--json"])
    assert result.exit_code == 0

    # 11. Docs build
    result = runner.invoke(app, ["docs-build", "--repo", repo])
    assert result.exit_code == 0

    # 12. Diff against itself (smoke test)
    result = runner.invoke(app, ["diff", repo, repo, "--json"])
    assert result.exit_code == 0


def test_e2e_v0_4_command_surface(sample_repo: Path) -> None:
    """Exercise v0.4 operational readiness CLI surface."""
    repo = str(sample_repo)

    # 1. Scorecard (with new metrics)
    result = runner.invoke(app, ["scorecard", "--repo", repo, "--json"])
    assert result.exit_code == 0
    assert "evidence_coverage" in result.output
    assert "sap_table_coverage" in result.output

    # 2. Gap report
    result = runner.invoke(app, ["gap-report", "--repo", repo, "--json"])
    assert result.exit_code == 0
    assert "gap_score" in result.output

    # 3. Owners
    result = runner.invoke(app, ["owners", "--repo", repo, "--json"])
    assert result.exit_code == 0
    assert "coverage_percent" in result.output

    # 4. Decisions list
    result = runner.invoke(app, ["decisions", "list", "--repo", repo, "--json"])
    assert result.exit_code == 0

    # 5. Decisions report
    result = runner.invoke(app, ["decisions", "report", "--repo", repo, "--json"])
    assert result.exit_code == 0
    assert "evidence_coverage" in result.output
    assert "category_breakdown" in result.output

    # 6. Proposal report
    result = runner.invoke(app, ["proposal", "report", "--repo", repo])
    assert result.exit_code == 0


def test_generic_product_model_validates_and_indexes() -> None:
    """Regression test for #372: generic_product_model must validate and build cleanly."""
    from pathlib import Path

    repo = Path(__file__).resolve().parent.parent / "examples" / "generic_product_model"

    # Validate
    result = runner.invoke(app, ["validate", "--repo", str(repo), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["is_valid"] is True
    assert data["error_count"] == 0
    assert data["warning_count"] == 0

    # Build index
    result = runner.invoke(app, ["build-index", "--repo", str(repo), "--jsonl"])
    assert result.exit_code == 0, result.output
    assert (repo / "generated" / "modelops.db").exists()
    assert (repo / "generated" / "search_documents.jsonl").exists()
    assert (repo / "generated" / "lineage_edges.jsonl").exists()

    # Trace and impact work
    result = runner.invoke(app, ["trace", "ATTR-PRODUCT-SKU", "--repo", str(repo)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["impact", "FEP-PRODUCT-SKU", "--repo", str(repo)])
    assert result.exit_code == 0, result.output

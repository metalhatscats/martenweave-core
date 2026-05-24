"""End-to-end CLI demo flow test."""

from __future__ import annotations

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

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
    result = runner.invoke(
        app, ["search", "Customer Group", "--repo", repo, "--json"]
    )
    assert result.exit_code == 0

    # 5. Query
    result = runner.invoke(
        app, ["query", "--type", "Attribute", "--repo", repo, "--json"]
    )
    assert result.exit_code == 0

    # 6. Export model CSV
    result = runner.invoke(
        app, ["export-model", "--repo", repo, "--format", "csv"]
    )
    assert result.exit_code == 0

    # 7. Export model XLSX
    result = runner.invoke(
        app, ["export-model", "--repo", repo, "--format", "xlsx"]
    )
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

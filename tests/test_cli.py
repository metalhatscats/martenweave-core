"""Tests for CLI commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "modelops" in result.output


def test_cli_init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path / "new-repo")])
    assert result.exit_code == 0
    assert (tmp_path / "new-repo" / "modelops.config.yaml").exists()


def test_cli_validate(sample_repo: Path) -> None:
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Validation Results" in result.output


def test_cli_build_index(sample_repo: Path) -> None:
    result = runner.invoke(app, ["build-index", "--repo", str(sample_repo), "--jsonl"])
    assert result.exit_code == 0
    assert "Index built" in result.output


def test_cli_health(sample_repo: Path) -> None:
    # Need index first
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["health", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Repository Health" in result.output


def test_cli_impact(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["impact", "FEP-S4-KNVV-KDGRP", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Impact Report" in result.output

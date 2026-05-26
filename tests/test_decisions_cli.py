"""Tests for the decisions CLI subcommands."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_decisions_list_no_index(sample_repo: Path) -> None:
    import shutil
    generated = sample_repo / "generated"
    if generated.exists():
        shutil.rmtree(generated)
    result = runner.invoke(app, ["decisions", "list", "--repo", str(sample_repo)])
    assert result.exit_code == 1
    assert "No index found" in result.output


def test_decisions_list_no_index_json(sample_repo: Path) -> None:
    import shutil
    generated = sample_repo / "generated"
    if generated.exists():
        shutil.rmtree(generated)
    result = runner.invoke(app, ["decisions", "list", "--repo", str(sample_repo), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_decisions_list_table(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["decisions", "list", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "DEC-CH01-A17-" in result.output
    assert "proposed" in result.output


def test_decisions_list_json(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["decisions", "list", "--repo", str(sample_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 1
    ids = [d["id"] for d in data]
    assert "DEC-CH01-A17-CUSTOMER-GROUP" in ids
    decision = next(d for d in data if d["id"] == "DEC-CH01-A17-CUSTOMER-GROUP")
    assert decision["status"] == "proposed"
    assert decision["domain"] == "DOMAIN-CUSTOMER-BP"


def test_decisions_show_not_found(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app, ["decisions", "show", "DEC-NONEXISTENT", "--repo", str(sample_repo)]
    )
    assert result.exit_code == 1
    assert "Decision not found" in result.output


def test_decisions_show_table(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app, ["decisions", "show", "DEC-CH01-A17-CUSTOMER-GROUP", "--repo", str(sample_repo)]
    )
    assert result.exit_code == 0
    assert "DEC-CH01-A17-CUSTOMER-GROUP" in result.output
    assert "proposed" in result.output
    assert "DOMAIN-CUSTOMER-BP" in result.output


def test_decisions_show_json(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app,
        ["decisions", "show", "DEC-CH01-A17-CUSTOMER-GROUP", "--repo", str(sample_repo), "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "DEC-CH01-A17-CUSTOMER-GROUP"
    assert data["type"] == "Decision"
    assert data["status"] == "proposed"
    assert data["domain"] == "DOMAIN-CUSTOMER-BP"


def test_decisions_show_no_index(sample_repo: Path) -> None:
    import shutil
    generated = sample_repo / "generated"
    if generated.exists():
        shutil.rmtree(generated)
    result = runner.invoke(
        app, ["decisions", "show", "DEC-CH01-A17-CUSTOMER-GROUP", "--repo", str(sample_repo)]
    )
    assert result.exit_code == 1
    assert "No index found" in result.output

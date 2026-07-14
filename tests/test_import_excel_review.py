from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_export_model_out_option(sample_repo: Path):
    out = sample_repo.parent / "custom.xlsx"
    result = runner.invoke(
        app,
        [
            "export-model",
            "--repo",
            str(sample_repo),
            "--format",
            "xlsx",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_import_excel_review_command(sample_repo: Path):
    out = sample_repo.parent / "custom.xlsx"
    runner.invoke(
        app,
        [
            "export-model",
            "--repo",
            str(sample_repo),
            "--format",
            "xlsx",
            "--business-review",
            "--out",
            str(out),
        ],
    )
    result = runner.invoke(
        app,
        ["import-excel-review", "--repo", str(sample_repo), str(out)],
    )
    assert result.exit_code == 0, result.output
    assert "PatchProposal" in result.output

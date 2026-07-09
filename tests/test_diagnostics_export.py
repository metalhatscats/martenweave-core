"""Tests for diagnostics bundle export command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def _text_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and p.stat().st_size < 5_000_000]


class TestDiagnosticsExport:
    def test_creates_bundle_with_expected_files(self, sample_repo: Path) -> None:
        out_dir = sample_repo / "generated" / "diagnostics"
        result = runner.invoke(
            app,
            [
                "diagnostics",
                "export",
                "--repo",
                str(sample_repo),
                "--out",
                str(out_dir),
            ],
        )
        assert result.exit_code == 0, result.output
        assert (out_dir / "manifest.json").exists()
        assert (out_dir / "validation.json").exists()
        assert (out_dir / "health.json").exists()
        assert (out_dir / "scorecard.json").exists()
        assert (out_dir / "config.json").exists()
        assert (out_dir / "source_registry.json").exists()
        assert (out_dir / "generated_manifest.json").exists()
        assert (out_dir / "pending_changes.json").exists()
        assert (out_dir / "dataset_samples.json").exists()
        assert not (out_dir / "commands").exists()

        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["repo_name"] == "Customer BP Example"
        assert manifest["object_count"] > 0
        assert "validation" in manifest
        assert manifest["validation"]["ran"] is True

    def test_include_outputs_adds_command_snapshots(self, sample_repo: Path) -> None:
        out_dir = sample_repo / "generated" / "diagnostics-outputs"
        result = runner.invoke(
            app,
            [
                "diagnostics",
                "export",
                "--repo",
                str(sample_repo),
                "--out",
                str(out_dir),
                "--include-outputs",
            ],
        )
        assert result.exit_code == 0, result.output
        commands_dir = out_dir / "commands"
        assert commands_dir.exists()
        assert (commands_dir / "validate.json").exists()
        assert (commands_dir / "health.json").exists()
        assert (commands_dir / "scorecard.json").exists()
        assert (commands_dir / "index-freshness.json").exists()

    def test_no_raw_dataset_values_in_bundle(self, sample_repo: Path) -> None:
        out_dir = sample_repo / "generated" / "diagnostics-privacy"
        result = runner.invoke(
            app,
            [
                "diagnostics",
                "export",
                "--repo",
                str(sample_repo),
                "--out",
                str(out_dir),
                "--include-outputs",
            ],
        )
        assert result.exit_code == 0, result.output

        bundle_text = "\n".join(
            p.read_text(encoding="utf-8", errors="ignore")
            for p in _text_files(out_dir)
        )
        assert "cust001@example.com" not in bundle_text
        assert "1000001" not in bundle_text
        assert "CUSTOMER_ID" not in bundle_text
        assert ".env" not in bundle_text

    def test_requires_index(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        out_dir = repo / "diagnostics"
        result = runner.invoke(
            app,
            [
                "diagnostics",
                "export",
                "--repo",
                str(repo),
                "--out",
                str(out_dir),
            ],
        )
        assert result.exit_code == 1
        assert "build-index" in result.output

    def test_json_output_prints_manifest(self, sample_repo: Path) -> None:
        out_dir = sample_repo / "generated" / "diagnostics-json"
        result = runner.invoke(
            app,
            [
                "diagnostics",
                "export",
                "--repo",
                str(sample_repo),
                "--out",
                str(out_dir),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        manifest = json.loads(result.output)
        assert manifest["repo_name"] == "Customer BP Example"
        assert manifest["bundle_path"] == str(out_dir)

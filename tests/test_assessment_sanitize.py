"""Tests for assessment package sanitization."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def _build_assessment_input(tmp_path: Path) -> Path:
    """Create an assessment-like input directory with sensitive content."""
    src = tmp_path / "assessment_input"
    src.mkdir(parents=True)

    # Shareable report
    (src / "01_readiness_scorecard.md").write_text(
        "# Readiness Scorecard\n\n"
        "Repository: /Users/alice/client/project\n"
        "Contact: alice@example.com\n",
        encoding="utf-8",
    )

    # Finding metadata (shareable)
    (src / "findings.json").write_text(
        json.dumps(
            {
                "finding_count": 1,
                "findings": [
                    {
                        "id": "mapping:missing_owner:sheet1:5",
                        "message": "Missing owner in 'sheet1' row 5.",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Raw dataset must be excluded by default
    raw_dir = src / "dataset_readiness"
    raw_dir.mkdir()
    (raw_dir / "sample.csv").write_text(
        "CUSTOMER_NAME,EMAIL\nAlice Smith,alice@client.com\n", encoding="utf-8"
    )

    # Manifest with absolute paths and secrets
    (src / "manifest.json").write_text(
        json.dumps(
            {
                "martenweave_version": "0.4.1",
                "repo_name": "Client Project",
                "repo_path": "/Users/alice/client/project",
                "inputs": {
                    "mapping": "/Users/alice/client/project/mapping.xlsx",
                    "dataset": "/Users/alice/client/project/sample.csv",
                    "evidence": [],
                },
                "generated_artifacts": [
                    {"path": "dataset_readiness/sample.csv", "sha256": "abc"}
                ],
                "stage_statuses": [],
                "generated_at": "2026-01-01T00:00:00Z",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return src


def test_sanitize_redacts_absolute_paths_and_emails(tmp_path: Path) -> None:
    src = _build_assessment_input(tmp_path)
    out = tmp_path / "sanitized"

    result = runner.invoke(
        app,
        [
            "assessment",
            "sanitize",
            "--input",
            str(src),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output

    scorecard = (out / "01_readiness_scorecard.md").read_text(encoding="utf-8")
    assert "/Users/alice/client/project" not in scorecard
    assert "alice@example.com" not in scorecard
    assert "<redacted-path>" in scorecard or "<redacted-email>" in scorecard


def test_sanitize_excludes_raw_datasets(tmp_path: Path) -> None:
    src = _build_assessment_input(tmp_path)
    out = tmp_path / "sanitized"

    result = runner.invoke(
        app,
        [
            "assessment",
            "sanitize",
            "--input",
            str(src),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert not (out / "dataset_readiness" / "sample.csv").exists()


def test_sanitize_blocks_unknown_binary_files(tmp_path: Path) -> None:
    src = _build_assessment_input(tmp_path)
    (src / "raw_dump.bin").write_bytes(b"\x00\x01\x02\x03")

    out = tmp_path / "sanitized"
    result = runner.invoke(
        app,
        [
            "assessment",
            "sanitize",
            "--input",
            str(src),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 1, result.output
    assert "raw_dump.bin" in result.output
    assert "blocked" in result.output.lower()


def test_sanitize_does_not_modify_source(tmp_path: Path) -> None:
    src = _build_assessment_input(tmp_path)
    original_manifest = (src / "manifest.json").read_text(encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "assessment",
            "sanitize",
            "--input",
            str(src),
            "--out",
            str(tmp_path / "sanitized"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (src / "manifest.json").read_text(encoding="utf-8") == original_manifest


def test_sanitize_produces_deterministic_manifest(tmp_path: Path) -> None:
    src = _build_assessment_input(tmp_path)
    out1 = tmp_path / "sanitized1"
    out2 = tmp_path / "sanitized2"

    result1 = runner.invoke(
        app, ["assessment", "sanitize", "--input", str(src), "--out", str(out1)]
    )
    result2 = runner.invoke(
        app, ["assessment", "sanitize", "--input", str(src), "--out", str(out2)]
    )
    assert result1.exit_code == 0
    assert result2.exit_code == 0

    manifest1 = json.loads((out1 / "sanitization-manifest.json").read_text(encoding="utf-8"))
    manifest2 = json.loads((out2 / "sanitization-manifest.json").read_text(encoding="utf-8"))
    assert manifest1["included_files"] == manifest2["included_files"]
    assert manifest1["redactions"] == manifest2["redactions"]


def test_sanitize_manifest_lists_excluded_and_redactions(tmp_path: Path) -> None:
    src = _build_assessment_input(tmp_path)
    out = tmp_path / "sanitized"

    result = runner.invoke(
        app,
        [
            "assessment",
            "sanitize",
            "--input",
            str(src),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output

    manifest = json.loads((out / "sanitization-manifest.json").read_text(encoding="utf-8"))
    assert manifest["tool"] == "martenweave"
    assert "version" in manifest
    assert "excluded_files" in manifest
    assert any("dataset_readiness/sample.csv" in f for f in manifest["excluded_files"])
    assert len(manifest["redactions"]) > 0

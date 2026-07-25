"""Tests for domain-pack build, validate, and diff CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_domain_pack_build_creates_reference_repo(tmp_path: Path) -> None:
    out_repo = tmp_path / "sap-bp-pack"

    result = runner.invoke(
        app,
        [
            "domain-pack",
            "build",
            "sap-business-partner",
            "--out",
            str(out_repo),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["pack_id"] == "sap-business-partner"
    assert payload["include_generated"] is False
    assert payload["generated_artifacts_copied"] is False
    assert (out_repo / "modelops.config.yaml").exists()
    assert (out_repo / "README.md").exists()
    assert (out_repo / "model").exists()
    assert (out_repo / "generated").exists()
    assert not (out_repo / "generated" / "modelops.db").exists()


def test_domain_pack_build_rejects_nonempty_target(tmp_path: Path) -> None:
    out_repo = tmp_path / "sap-bp-pack"
    out_repo.mkdir()
    (out_repo / "keep.txt").write_text("occupied", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "domain-pack",
            "build",
            "sap-business-partner",
            "--out",
            str(out_repo),
        ],
    )

    assert result.exit_code == 1
    assert "must be empty" in result.output


def test_domain_pack_validate_builtin_reference_json() -> None:
    result = runner.invoke(
        app,
        [
            "domain-pack",
            "validate",
            "sap-business-partner",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["pack_id"] == "sap-business-partner"
    assert payload["is_valid"] is True
    assert payload["enabled_domain_packs"] == ["sap"]
    assert payload["object_count"] > 0


def test_domain_pack_diff_builtin_and_built_copy_has_no_changes(tmp_path: Path) -> None:
    out_repo = tmp_path / "sap-bp-pack"

    build_result = runner.invoke(
        app,
        [
            "domain-pack",
            "build",
            "sap-business-partner",
            "--out",
            str(out_repo),
        ],
    )
    assert build_result.exit_code == 0, build_result.output

    diff_result = runner.invoke(
        app,
        [
            "domain-pack",
            "diff",
            "sap-business-partner",
            str(out_repo),
            "--json",
        ],
    )

    assert diff_result.exit_code == 0, diff_result.output
    payload = json.loads(diff_result.output)
    assert payload["has_changes"] is False
    assert payload["base_count"] == payload["head_count"]

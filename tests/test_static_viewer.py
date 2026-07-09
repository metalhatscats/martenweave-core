"""Regression tests for the static documentation viewer."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_docs_build_generates_viewer_files(sample_repo: Path) -> None:
    """docs-build emits the expected HTML, CSS, JS, and JSON viewer files."""
    out_dir = sample_repo / "generated" / "docs_site"

    result = runner.invoke(
        app,
        [
            "docs-build",
            "--repo",
            str(sample_repo),
            "--site",
            str(out_dir),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)

    assert "files" in data
    files = data["files"]
    assert "index.html" in files
    assert "objects.html" in files
    assert "gaps.html" in files
    assert "search-index.json" in files
    assert any(name.endswith(".css") for name in files)
    assert any(name.endswith(".js") for name in files)

    manifest = data.get("viewer_manifest")
    assert manifest is not None
    assert manifest.get("product_boundary", {}).get("local_static_read_only") is True

    # Object detail page for a known SAP endpoint should exist.
    assert any("fep-s4-knvv-kdgrp.html" in name for name in files)

    # Search index should contain known terms.
    search_index = json.loads((out_dir / "search-index.json").read_text(encoding="utf-8"))
    assert any("KNVV" in str(entry) for entry in search_index)
    assert any("Customer Group" in str(entry) for entry in search_index)


def test_docs_build_fails_without_index(tmp_path: Path) -> None:
    """docs-build must fail gracefully when no index exists."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["docs-build", "--repo", str(tmp_path), "--site", str(tmp_path / "docs_site")],
    )
    assert result.exit_code == 1
    assert "build-index" in result.output or "No index" in result.output

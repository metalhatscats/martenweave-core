"""Tests for static docs generation (#59)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.docs.static_doc_generator import generate_static_docs
from modelops_core.index.sqlite_builder import build_index

runner = CliRunner()


@pytest.fixture
def indexed_repo(sample_repo: Path) -> Path:
    """Ensure the sample repo has a built index."""
    build_index(sample_repo, allow_invalid=True)
    return sample_repo


class TestStaticDocGenerator:
    def test_generates_markdown_files(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        result = generate_static_docs(indexed_repo, output)
        assert result.exists()
        files = {f.name for f in result.iterdir() if f.suffix == ".md"}
        assert "index.md" in files
        assert "objects.md" in files

    def test_index_contains_overview(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)
        index = output / "index.md"
        text = index.read_text(encoding="utf-8")
        assert "Model Documentation" in text
        assert "Generated view" in text
        assert "Total objects" in text

    def test_objects_contains_anchors(self, indexed_repo: Path) -> None:
        output = indexed_repo / "docs_site"
        generate_static_docs(indexed_repo, output)
        objects_md = output / "objects.md"
        text = objects_md.read_text(encoding="utf-8")
        assert "# All Objects" in text
        assert "{#" in text  # anchors present

    def test_per_type_pages_exist(self, indexed_repo: Path) -> None:
        output = indexed_repo / "docs_site"
        generate_static_docs(indexed_repo, output)
        # The sample repo has Attribute objects
        attribute_md = output / "attribute.md"
        assert attribute_md.exists()
        text = attribute_md.read_text(encoding="utf-8")
        assert "Attribute" in text

    def test_raises_when_no_index(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            generate_static_docs(tmp_path, tmp_path / "docs")


class TestDocsBuildCli:
    def test_cli_success(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app, ["docs-build", "--repo", str(indexed_repo)]
        )
        assert result.exit_code == 0
        assert "Documentation generated" in result.output
        assert "index.md" in result.output

    def test_cli_no_index(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["docs-build", "--repo", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "build-index" in result.output

    def test_cli_docs_build_json(self, indexed_repo: Path) -> None:
        import json

        result = runner.invoke(
            app, ["docs-build", "--repo", str(indexed_repo), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "output_dir" in data
        assert isinstance(data["files"], list)
        assert "index.md" in data["files"]

    def test_cli_docs_build_no_index_json(self, tmp_path: Path) -> None:
        import json

        result = runner.invoke(
            app, ["docs-build", "--repo", str(tmp_path), "--json"]
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

"""Tests for static docs generation (#59)."""

from __future__ import annotations

import json
import re
import sqlite3
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

    def test_generates_required_viewer_files(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)

        required = {
            "index.html",
            "objects.html",
            "gaps.html",
            "decisions.html",
            "owners.html",
            "assets/viewer.css",
            "assets/viewer.js",
            "search-index.json",
            "viewer-manifest.json",
            "objects/fep-s4-knvv-kdgrp.html",
            "objects/attr-cust-sales-customer-group.html",
        }
        actual = {str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()}
        assert required <= actual

    def test_manifest_schema_and_product_boundary(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)

        manifest = json.loads((output / "viewer-manifest.json").read_text(encoding="utf-8"))
        assert manifest["viewer_schema_version"] == "1.0"
        assert manifest["index"]["fresh"] is True
        assert manifest["index"]["built_at_utc"]
        assert manifest["object_count"] > 0
        assert manifest["outputs"]["objects"] == "objects.html"
        assert manifest["product_boundary"] == {
            "ai_auto_mutation": False,
            "authentication": False,
            "editing": False,
            "hosted_user_interface": False,
            "local_static_read_only": True,
            "sap_write_back": False,
        }

    def test_search_index_covers_customer_group_path(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)

        search_text = (output / "search-index.json").read_text(encoding="utf-8")
        assert "Customer Group" in search_text
        assert "KNVV" in search_text
        assert "KDGRP" in search_text
        assert "ATTR-CUST-SALES-CUSTOMER-GROUP" in search_text
        assert "FEP-S4-KNVV-KDGRP" in search_text

    def test_viewer_uses_safe_relative_internal_links(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)

        object_files = [path.name for path in (output / "objects").glob("*.html")]
        assert object_files
        assert len(object_files) == len(set(object_files))
        assert all(re.fullmatch(r"[a-z0-9-]+\.html", name) for name in object_files)

        bad_links: list[tuple[str, str]] = []
        external_links: list[tuple[str, str]] = []
        absolute_links: list[tuple[str, str]] = []
        for html_file in output.rglob("*.html"):
            text = html_file.read_text(encoding="utf-8")
            attrs = re.findall(r'(?:href|src)="([^"]+)"', text)
            for href in attrs:
                if href.startswith("data:"):
                    continue
                if href.startswith(("http://", "https://", "//")):
                    external_links.append((str(html_file.relative_to(output)), href))
                    continue
                if href.startswith("/"):
                    absolute_links.append((str(html_file.relative_to(output)), href))
                    continue
                target = (html_file.parent / href).resolve()
                if not target.exists():
                    bad_links.append((str(html_file.relative_to(output)), href))

        assert not external_links
        assert not absolute_links
        assert not bad_links

    def test_viewer_empty_states_and_no_raw_dataset_values(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)

        generated_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in output.rglob("*")
            if path.is_file() and path.suffix in {".html", ".json", ".js", ".css"}
        )
        assert "Dataset-specific metrics are not included" in generated_text
        assert "No owner fields are assigned on this object." in generated_text
        assert "No description is present in the index." in generated_text
        assert "No missing-owner objects were found." in generated_text
        assert "LEGACY-A" not in generated_text

    def test_stale_index_warning_is_embedded(self, indexed_repo: Path) -> None:
        source = next((indexed_repo / "model").rglob("ATTR-CUST-SALES-CUSTOMER-GROUP.md"))
        source.write_text(
            source.read_text(encoding="utf-8") + "\n<!-- changed after index build -->\n",
            encoding="utf-8",
        )
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)

        manifest = json.loads((output / "viewer-manifest.json").read_text(encoding="utf-8"))
        assert manifest["index"]["fresh"] is False
        assert manifest["index"]["reason"] == "content hash mismatch"
        assert "Index freshness: <strong>stale</strong>" in (output / "index.html").read_text(
            encoding="utf-8"
        )

    def test_html_escapes_canonical_content(self, indexed_repo: Path) -> None:
        db_path = indexed_repo / "generated" / "modelops.db"
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "UPDATE objects SET description = ?, body = ? WHERE id = ?",
                (
                    "<script>alert('description')</script>",
                    "<script>alert('body')</script>",
                    "ATTR-CUST-SALES-CUSTOMER-GROUP",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output, db_path=db_path)
        detail = (output / "objects" / "attr-cust-sales-customer-group.html").read_text(
            encoding="utf-8"
        )
        assert "<script>alert" not in detail
        assert "&lt;script&gt;alert" in detail

    def test_viewer_has_inline_favicon(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)
        index_html = (output / "index.html").read_text(encoding="utf-8")
        assert '<link rel="icon" href="data:image/svg+xml' in index_html
        assert "favicon.ico" not in index_html

    def test_viewer_search_input_has_label(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)
        index_html = (output / "index.html").read_text(encoding="utf-8")
        objects_html = (output / "objects.html").read_text(encoding="utf-8")
        assert 'id="viewer-search"' in index_html
        assert 'aria-label="Filter objects"' in index_html
        assert 'aria-label="Search objects"' in objects_html

    def test_viewer_has_landmark_regions(self, indexed_repo: Path) -> None:
        output = indexed_repo / "generated" / "docs_site"
        generate_static_docs(indexed_repo, output)
        index_html = (output / "index.html").read_text(encoding="utf-8")
        assert "<main" in index_html
        assert 'aria-label="Viewer navigation"' in index_html


class TestDocsBuildCli:
    def test_cli_success(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["docs-build", "--repo", str(indexed_repo)])
        assert result.exit_code == 0
        assert "Documentation generated" in result.output
        assert "index.md" in result.output

    def test_cli_no_index(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["docs-build", "--repo", str(tmp_path)])
        assert result.exit_code == 1
        assert "build-index" in result.output

    def test_cli_docs_build_json(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["docs-build", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "output_dir" in data
        assert isinstance(data["files"], list)
        assert "index.md" in data["files"]
        assert "index.html" in data["files"]
        assert "viewer_files" in data
        assert data["viewer_manifest"]["outputs"]["dashboard"] == "index.html"

    def test_cli_docs_build_site_alias(self, indexed_repo: Path, tmp_path: Path) -> None:
        site = tmp_path / "viewer"
        result = runner.invoke(
            app,
            ["docs-build", "--repo", str(indexed_repo), "--site", str(site), "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["output_dir"] == str(site)
        assert (site / "index.html").exists()

    def test_cli_docs_build_no_index_json(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["docs-build", "--repo", str(tmp_path), "--json"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


def test_docs_readme_links_resolve() -> None:
    """Every local Markdown link in docs/README.md must point to an existing file."""
    import re

    docs_dir = Path("docs")
    readme = docs_dir / "README.md"
    assert readme.exists()
    text = readme.read_text(encoding="utf-8")
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
    broken: list[tuple[str, str]] = []
    for label, href in links:
        if href.startswith("http") or href.startswith("#"):
            continue
        target = docs_dir / href
        if not target.exists():
            broken.append((label, href))
    assert not broken, f"Broken docs/README.md links: {broken}"


def test_docs_first_15_minutes_filenames_match_disk() -> None:
    """Every file path referenced in docs/first-15-minutes.md code blocks must exist."""
    import re

    repo_root = Path(".").resolve()
    doc = repo_root / "docs" / "first-15-minutes.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")

    # Find all code blocks
    code_blocks = re.findall(r"```bash\n(.*?)\n```", text, re.DOTALL)

    broken: list[str] = []
    for block in code_blocks:
        for line in block.splitlines():
            # Look for path-like tokens (contain / and don't start with - or --)
            tokens = line.strip().split()
            for token in tokens:
                if token.startswith(("-", "--", "$")):
                    continue
                if "/" in token and not token.startswith("http"):
                    # Strip any trailing backslash for line continuations
                    clean = token.rstrip("\\")
                    # .venv paths are environment-specific and not expected in CI
                    if clean.startswith(".venv/"):
                        continue
                    path = repo_root / clean
                    if not path.exists():
                        broken.append(clean)

    assert not broken, f"Referenced paths in first-15-minutes.md do not exist: {broken}"


def test_docs_cli_commands_are_current() -> None:
    """Docs must not contain obsolete hyphenated CLI commands or wrong package names."""
    import re

    docs_dir = Path("docs")
    stale_patterns = [
        r"modelops\s+proposal-impact",
        r"modelops\s+proposal-validate",
        r"modelops\s+proposal-apply",
        r"modelops\s+cr-create",
        r"modelops\s+cr-approve",
        r"modelops\s+api\b",
        r"pip\s+install\s+modelops-core",
    ]
    found: list[tuple[str, str]] = []
    for doc in docs_dir.rglob("*.md"):
        text = doc.read_text(encoding="utf-8")
        for pattern in stale_patterns:
            for match in re.finditer(pattern, text):
                found.append((str(doc.relative_to(docs_dir)), match.group(0)))
    assert not found, f"Stale CLI commands or package names found in docs: {found}"

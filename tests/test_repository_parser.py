"""Tests for repository parser and scanner."""

from __future__ import annotations

from pathlib import Path

from modelops_core.repository import parse_file, scan_repository


def test_parse_markdown_with_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "test.md"
    path.write_text("---\nid: TEST-001\ntype: Attribute\n---\n\n# Test\n", encoding="utf-8")
    result = parse_file(path)
    assert result.parser_error is None
    assert result.frontmatter == {"id": "TEST-001", "type": "Attribute"}
    assert result.body == "# Test"


def test_parse_yaml_file(tmp_path: Path) -> None:
    path = tmp_path / "test.yaml"
    path.write_text("id: TEST-002\ntype: System\n", encoding="utf-8")
    result = parse_file(path)
    assert result.parser_error is None
    assert result.frontmatter == {"id": "TEST-002", "type": "System"}


def test_parse_unsupported_extension(tmp_path: Path) -> None:
    path = tmp_path / "test.txt"
    path.write_text("hello", encoding="utf-8")
    result = parse_file(path)
    assert result.parser_error is not None
    assert "Unsupported file extension" in result.parser_error


def test_scan_repository(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\n---\n", encoding="utf-8")
    (tmp_path / "b.yaml").write_text("id: B\n", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("skip", encoding="utf-8")
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated" / "c.md").write_text("---\n---\n", encoding="utf-8")

    files = scan_repository(tmp_path)
    assert len(files) == 2
    assert all(f.endswith((".md", ".yaml")) for f in files)

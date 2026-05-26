"""Tests for repository parser and scanner."""

from __future__ import annotations

from pathlib import Path

from modelops_core.repository import parse_file, scan_repository


def test_parse_markdown_with_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "test.md"
    path.write_text("---\nid: TEST-001\ntype: Attribute\n---\n\n# Test\n", encoding="utf-8")
    result = parse_file(path)
    assert result.parser_error is None
    assert result.frontmatter is not None
    assert result.frontmatter["id"] == "TEST-001"
    assert result.frontmatter["type"] == "Attribute"
    assert "created_at" in result.frontmatter
    assert "updated_at" in result.frontmatter
    assert result.body == "# Test"


def test_parse_yaml_file(tmp_path: Path) -> None:
    path = tmp_path / "test.yaml"
    path.write_text("id: TEST-002\ntype: System\n", encoding="utf-8")
    result = parse_file(path)
    assert result.parser_error is None
    assert result.frontmatter is not None
    assert result.frontmatter["id"] == "TEST-002"
    assert result.frontmatter["type"] == "System"
    assert "created_at" in result.frontmatter
    assert "updated_at" in result.frontmatter


def test_parse_preserves_existing_timestamps(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    path = tmp_path / "test.md"
    path.write_text(
        "---\n"
        "id: TEST-003\n"
        "type: Attribute\n"
        "created_at: 2024-01-15T10:30:00+00:00\n"
        "updated_at: 2024-06-20T14:00:00+00:00\n"
        "---\n",
        encoding="utf-8",
    )
    result = parse_file(path)
    assert result.parser_error is None
    assert result.frontmatter is not None
    # PyYAML parses ISO timestamps into datetime objects
    assert isinstance(result.frontmatter["created_at"], datetime)
    assert result.frontmatter["created_at"] == datetime(
        2024, 1, 15, 10, 30, tzinfo=UTC
    )
    assert isinstance(result.frontmatter["updated_at"], datetime)
    assert result.frontmatter["updated_at"] == datetime(
        2024, 6, 20, 14, 0, tzinfo=UTC
    )


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

"""Tests for repository scanner."""

from __future__ import annotations

from pathlib import Path

from modelops_core.repository.scanner import scan_repository


class TestScanRepository:
    def test_finds_markdown_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("---\n---\n")
        results = scan_repository(tmp_path)
        assert any("a.md" in r for r in results)

    def test_finds_yaml_files(self, tmp_path: Path) -> None:
        (tmp_path / "b.yaml").write_text("id: X")
        (tmp_path / "c.yml").write_text("id: Y")
        results = scan_repository(tmp_path)
        assert any("b.yaml" in r for r in results)
        assert any("c.yml" in r for r in results)

    def test_skips_generated_dir(self, tmp_path: Path) -> None:
        gen = tmp_path / "generated"
        gen.mkdir()
        (gen / "x.md").write_text("---\n---\n")
        results = scan_repository(tmp_path)
        assert not any("generated" in r for r in results)

    def test_skips_hidden_dirs(self, tmp_path: Path) -> None:
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "x.md").write_text("---\n---\n")
        results = scan_repository(tmp_path)
        assert not any(".hidden" in r for r in results)

    def test_returns_sorted_absolute_paths(self, tmp_path: Path) -> None:
        (tmp_path / "z.md").write_text("---\n---\n")
        (tmp_path / "a.md").write_text("---\n---\n")
        results = scan_repository(tmp_path)
        assert all(Path(r).is_absolute() for r in results)
        assert results == sorted(results)

    def test_case_insensitive_suffix(self, tmp_path: Path) -> None:
        (tmp_path / "d.MD").write_text("---\n---\n")
        (tmp_path / "e.Yaml").write_text("id: X")
        results = scan_repository(tmp_path)
        assert any("d.MD" in r for r in results)
        assert any("e.Yaml" in r for r in results)

    def test_empty_repo(self, tmp_path: Path) -> None:
        results = scan_repository(tmp_path)
        assert results == []

    def test_skips_non_canonical_suffixes(self, tmp_path: Path) -> None:
        (tmp_path / "f.txt").write_text("text")
        (tmp_path / "g.py").write_text("pass")
        results = scan_repository(tmp_path)
        assert not any("f.txt" in r for r in results)
        assert not any("g.py" in r for r in results)

"""Tests for the release preflight version guard."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.release_preflight import check, get_package_version, normalize_tag


def _write_pyproject(tmp_path: Path, version: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(f'[project]\nversion = "{version}"\n')
    return path


class TestNormalizeTag:
    def test_strip_leading_v(self) -> None:
        assert normalize_tag("v0.4.1") == "0.4.1"

    def test_strip_refs_tags_prefix(self) -> None:
        assert normalize_tag("refs/tags/v0.4.1") == "0.4.1"

    def test_no_leading_v(self) -> None:
        assert normalize_tag("0.4.1") == "0.4.1"

    def test_empty_tag_raises(self) -> None:
        with pytest.raises(ValueError, match="tag is empty"):
            normalize_tag("")

    def test_none_tag_raises(self) -> None:
        with pytest.raises(ValueError, match="tag is empty"):
            normalize_tag(None)

    def test_only_v_raises(self) -> None:
        with pytest.raises(ValueError, match="tag is empty after normalizing"):
            normalize_tag("v")

    def test_whitespace_stripped(self) -> None:
        assert normalize_tag("  v0.4.1  ") == "0.4.1"


class TestGetPackageVersion:
    def test_reads_version(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        assert get_package_version(path) == "0.4.1"

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            get_package_version(tmp_path / "missing.toml")

    def test_missing_version(self, tmp_path: Path) -> None:
        path = tmp_path / "pyproject.toml"
        path.write_text("[project]\nname = 'test'\n")
        with pytest.raises(ValueError, match="project.version is missing"):
            get_package_version(path)


class TestCheck:
    def test_v_tag_matches_package_version(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        ok, message = check("v0.4.1", path)
        assert ok is True
        assert "matches" in message

    def test_bare_tag_matches_package_version(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        ok, message = check("0.4.1", path)
        assert ok is True
        assert "matches" in message

    def test_refs_tags_prefix_matches(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        ok, message = check("refs/tags/v0.4.1", path)
        assert ok is True
        assert "matches" in message

    def test_prerelease_tag_mismatch(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        ok, message = check("v0.4.1a1", path)
        assert ok is False
        assert "tag version '0.4.1a1' does not match package version '0.4.1'" in message

    def test_different_stable_tag_mismatch(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        ok, message = check("v0.4.2", path)
        assert ok is False
        assert "tag version '0.4.2' does not match package version '0.4.1'" in message

    def test_missing_tag_fails(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        ok, message = check(None, path)
        assert ok is False
        assert "invalid tag" in message

    def test_malformed_empty_after_v_fails(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        ok, message = check("v", path)
        assert ok is False
        assert "invalid tag" in message


class TestMain:
    def test_main_returns_zero_on_match(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        from modelops_core.release_preflight import main

        assert main(["--tag", "v0.4.1", "--pyproject", str(path)]) == 0

    def test_main_returns_one_on_mismatch(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        from modelops_core.release_preflight import main

        assert main(["--tag", "v0.4.1a1", "--pyproject", str(path)]) == 1

    def test_main_returns_one_when_tag_missing(self, tmp_path: Path) -> None:
        path = _write_pyproject(tmp_path, "0.4.1")
        from modelops_core.release_preflight import main

        assert main(["--pyproject", str(path)]) == 1

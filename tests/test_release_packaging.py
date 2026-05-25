"""Tests for release packaging and versioning."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from modelops_core import __version__


class TestVersion:
    def test_version_is_string(self) -> None:
        assert isinstance(__version__, str)
        assert len(__version__.split(".")) >= 2

    def test_version_matches_pyproject(self) -> None:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        assert f'version = "{__version__}"' in content


class TestBuild:
    @pytest.mark.slow
    def test_package_builds(self, tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        outdir = tmp_path / "dist"
        result = subprocess.run(
            [sys.executable, "-m", "build", str(repo_root), "--outdir", str(outdir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        artifacts = list(outdir.iterdir())
        assert any(a.suffix == ".gz" for a in artifacts), "sdist missing"
        assert any(a.suffix == ".whl" for a in artifacts), "wheel missing"

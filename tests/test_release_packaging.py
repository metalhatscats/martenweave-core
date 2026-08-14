"""Tests for release packaging and versioning."""

from __future__ import annotations

import subprocess
import sys
import tomllib
import zipfile
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


class TestConsoleScripts:
    def test_console_scripts_include_branded_alias_and_legacy_command(self) -> None:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text())
        scripts = data["project"]["scripts"]

        assert scripts["martenweave"] == "modelops_core.cli:app"
        assert scripts["modelops"] == "modelops_core.cli:app"


class TestRuntimeDependencies:
    def test_workbench_upload_routes_include_multipart_runtime(self) -> None:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        dependencies = tomllib.loads(pyproject.read_text())["project"]["dependencies"]

        assert any(dependency.startswith("python-multipart") for dependency in dependencies)


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

    @pytest.mark.slow
    def test_wheel_carries_first_value_assets(self, tmp_path: Path) -> None:
        """The wheel ships what the installed first-value smoke (issue #625) relies on."""
        repo_root = Path(__file__).resolve().parent.parent
        outdir = tmp_path / "dist"
        result = subprocess.run(
            [sys.executable, "-m", "build", str(repo_root), "--wheel", "--outdir", str(outdir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        wheel = next(outdir.glob("*.whl"))
        with zipfile.ZipFile(wheel) as archive:
            names = set(archive.namelist())
            entry_points = next(name for name in names if name.endswith("entry_points.txt"))
            scripts = archive.read(entry_points).decode("utf-8")

        assert "modelops_core/workbench_static/index.html" in names, "packaged Workbench missing"
        assert any(
            name.startswith("modelops_core/assets/templates/model_spines/") for name in names
        ), "model-spine templates missing"
        assert "martenweave = modelops_core.cli:app" in scripts

"""Tests for the Martenweave Workbench launcher."""

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from modelops_core.api.workbench_app import create_workbench_app
from modelops_core.cli import app as cli_app

runner = CliRunner()


def test_packaged_workbench_static_exists() -> None:
    """The frontend build must be shipped inside the Python package."""
    static_root = importlib.resources.files("modelops_core") / "workbench_static"
    assert static_root.is_dir()
    index_html = static_root / "index.html"
    assert index_html.is_file()


def test_create_workbench_app_requires_static_directory(sample_repo: Path) -> None:
    """create_workbench_app rejects a missing static directory."""
    with pytest.raises(ValueError, match="Workbench static files not found"):
        create_workbench_app(sample_repo, Path("/nonexistent/static/dir"))


def test_workbench_serves_index_html_and_api_routes(sample_repo: Path) -> None:
    """The workbench serves the SPA and keeps API routes functional."""
    static_dir = Path(str(importlib.resources.files("modelops_core") / "workbench_static"))
    app = create_workbench_app(sample_repo, static_dir)
    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    assert "text/html" in root.headers["content-type"]
    assert b"<div id=\"root\"></div>" in root.content

    health = client.get("/health", params={"repo": str(sample_repo)})
    assert health.status_code == 200
    data = health.json()
    assert data["status"] in ("healthy", "no_index")


def test_workbench_spa_fallback(sample_repo: Path) -> None:
    """Unknown paths fall back to index.html so client-side routing works."""
    static_dir = Path(str(importlib.resources.files("modelops_core") / "workbench_static"))
    app = create_workbench_app(sample_repo, static_dir)
    client = TestClient(app)

    response = client.get("/models")
    assert response.status_code == 200
    assert b"<div id=\"root\"></div>" in response.content


def test_workbench_cli_help() -> None:
    """The workbench command is registered and documents its options."""
    result = runner.invoke(cli_app, ["workbench", "--help"])
    assert result.exit_code == 0
    assert "--repo" in result.output
    assert "--no-open" in result.output
    assert "--port" in result.output


def test_workbench_subprocess_launches(sample_repo: Path) -> None:
    """`martenweave workbench` starts a server that serves the SPA and API."""
    import socket
    import subprocess
    import sys
    import time
    import urllib.error
    import urllib.request

    # Find a free ephemeral port.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "modelops_core.cli",
            "workbench",
            "--repo",
            str(sample_repo),
            "--port",
            str(port),
            "--no-open",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 15
        last_error = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"{base}/health", timeout=1) as resp:
                    assert resp.status == 200
                    break
            except (urllib.error.URLError, ConnectionError) as exc:
                last_error = exc
                time.sleep(0.25)
        else:
            proc.terminate()
            proc.wait(timeout=5)
            raise AssertionError(f"Workbench did not start: {last_error}")

        with urllib.request.urlopen(base, timeout=5) as resp:
            assert resp.status == 200
            body = resp.read()
            assert b"<div id=\"root\"></div>" in body

        with urllib.request.urlopen(f"{base}/health?repo={sample_repo}", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert data["status"] in ("healthy", "no_index")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

"""Integration tests for the `modelops serve` CLI command."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=0.5)
            if response.status_code == 200:
                return
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(0.1)
    raise TimeoutError(f"Server did not become ready at {url}: {last_error}")


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("uvicorn") is None,
    reason="uvicorn not installed",
)
def test_cli_serve_starts_and_responds(sample_repo: Path) -> None:
    port = _find_free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "modelops_core.cli",
            "serve",
            "--repo",
            str(sample_repo),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_server(f"http://127.0.0.1:{port}/health", timeout=10.0)

        response = requests.get(
            f"http://127.0.0.1:{port}/objects",
            params={"repo": str(sample_repo)},
            timeout=2.0,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        ids = {obj["id"] for obj in data}
        assert "DOMAIN-CUSTOMER-BP" in ids
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5.0)

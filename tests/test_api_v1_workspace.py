"""Tests for the versioned workspace open/create endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from modelops_core.api.app import app
from modelops_core.api.workspace import clear_workspace, configure_workspace

client = TestClient(app)


def _build_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    (repo / "generated").mkdir(parents=True)
    (repo / "modelops.config.yaml").write_text(
        "name: Test Repository\nenvironment: local\n",
        encoding="utf-8",
    )
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    return repo


def test_api_v1_workspace_validate_valid(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    response = client.post("/api/v1/workspace/validate", json={"path": str(repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["canonical_files"] == 1
    assert any("Index is missing" in w for w in data["warnings"])


def test_api_v1_workspace_validate_invalid_directory(tmp_path: Path) -> None:
    response = client.post(
        "/api/v1/workspace/validate",
        json={"path": str(tmp_path / "missing")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("does not exist" in err for err in data["errors"])


def test_api_v1_workspace_validate_rejects_relative_path(tmp_path: Path) -> None:
    response = client.post("/api/v1/workspace/validate", json={"path": "relative/path"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("absolute" in err for err in data["errors"])


def test_api_v1_workspace_open_switches_workspace(tmp_path: Path) -> None:
    original = _build_repo(tmp_path / "original")
    configure_workspace(original, mutation_token="test-token")
    new_repo = _build_repo(tmp_path / "new")

    response = client.post(
        "/api/v1/workspace/open",
        json={"path": str(new_repo)},
        headers={"X-Martenweave-Token": "test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["canonical_files"] == 1

    clear_workspace()


def test_api_v1_workspace_open_rejects_invalid(tmp_path: Path) -> None:
    original = _build_repo(tmp_path / "original")
    configure_workspace(original, mutation_token="test-token")

    response = client.post(
        "/api/v1/workspace/open",
        json={"path": str(tmp_path / "missing")},
        headers={"X-Martenweave-Token": "test-token"},
    )
    assert response.status_code == 400

    clear_workspace()


def test_api_v1_workspace_create_from_template(tmp_path: Path) -> None:
    configure_workspace(tmp_path / "dummy", mutation_token="test-token")
    target = tmp_path / "new_repo"

    response = client.post(
        "/api/v1/workspace/create",
        json={"path": str(target), "name": "New Repo", "template": "business_partner"},
        headers={"X-Martenweave-Token": "test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["canonical_files"] >= 1
    assert (target / "modelops.config.yaml").is_file()
    assert (target / "model").is_dir()

    clear_workspace()


def test_api_v1_workspace_create_rejects_existing_directory(tmp_path: Path) -> None:
    configure_workspace(tmp_path / "dummy", mutation_token="test-token")
    target = tmp_path / "existing"
    target.mkdir()
    (target / "file.txt").write_text("data", encoding="utf-8")

    response = client.post(
        "/api/v1/workspace/create",
        json={"path": str(target), "name": "Existing"},
        headers={"X-Martenweave-Token": "test-token"},
    )
    assert response.status_code == 400

    clear_workspace()

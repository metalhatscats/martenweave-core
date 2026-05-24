"""Tests for the local API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from modelops_core.api.app import app

client = TestClient(app)


def test_api_health(sample_repo: Path) -> None:
    response = client.get("/health", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "no_index")
    assert data["repository"] == str(sample_repo)


def test_api_list_objects(sample_repo: Path) -> None:
    response = client.get("/objects", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    ids = [obj["id"] for obj in data]
    assert "DOMAIN-CUSTOMER-BP" in ids


def test_api_list_objects_by_type(sample_repo: Path) -> None:
    response = client.get(
        "/objects", params={"repo": str(sample_repo), "type": "MasterDataDomain"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "MasterDataDomain"


def test_api_get_object(sample_repo: Path) -> None:
    response = client.get(
        "/objects/DOMAIN-CUSTOMER-BP", params={"repo": str(sample_repo)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "DOMAIN-CUSTOMER-BP"
    assert data["type"] == "MasterDataDomain"


def test_api_get_object_not_found(sample_repo: Path) -> None:
    response = client.get("/objects/DOES-NOT-EXIST", params={"repo": str(sample_repo)})
    assert response.status_code == 404


def test_api_validate(sample_repo: Path) -> None:
    response = client.get("/validate", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "error_count" in data
    assert "warning_count" in data


def test_api_list_proposals_empty(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.get("/proposals", params={"repo": repo})
    assert response.status_code == 200
    assert response.json() == []


def test_api_get_proposal_not_found(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.get("/proposals/PP-NOPE", params={"repo": repo})
    assert response.status_code == 404


def test_api_export_csv(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.post("/export", params={"repo": repo, "format": "csv"})
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
    assert len(data["files"]) > 0


def test_api_export_xlsx(temp_model_dir: Path) -> None:
    pytest.importorskip("openpyxl")
    repo = str(temp_model_dir.parent)
    response = client.post("/export", params={"repo": repo, "format": "xlsx"})
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "xlsx"
    assert Path(data["file"]).exists()


def test_api_export_invalid_format(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.post("/export", params={"repo": repo, "format": "pdf"})
    assert response.status_code == 400

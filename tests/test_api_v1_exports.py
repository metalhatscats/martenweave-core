"""Tests for the versioned export endpoint."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from modelops_core.api.app import app

client = TestClient(app)


def _build_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    (repo / "generated").mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    return repo


def test_api_v1_export_csv(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    response = client.post(
        "/api/v1/exports",
        params={"repo": str(repo), "format": "csv"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
    assert data["artifact_id"] == "exports/csv"

    download = client.get(
        "/api/v1/reports/exports/csv/masterdatadomain.csv", params={"repo": str(repo)}
    )
    assert download.status_code == 200


def test_api_v1_export_xlsx(tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    repo = _build_repo(tmp_path)
    response = client.post(
        "/api/v1/exports",
        params={"repo": str(repo), "format": "xlsx"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "xlsx"
    assert data["artifact_id"] == "exports/model.xlsx"

    download = client.get("/api/v1/reports/exports/model.xlsx", params={"repo": str(repo)})
    assert download.status_code == 200


def test_api_v1_export_invalid_format(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    response = client.post(
        "/api/v1/exports",
        params={"repo": str(repo), "format": "pdf"},
    )
    assert response.status_code == 400

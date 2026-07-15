"""Tests for the versioned import profile and preview endpoints."""

from __future__ import annotations

from io import BytesIO
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
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n",
        encoding="utf-8",
    )
    return repo


def test_api_v1_import_profile_csv(tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    repo = _build_repo(tmp_path)
    csv_file = BytesIO(b"id,name\n1,Alice\n2,Bob\n")

    response = client.post(
        "/api/v1/imports/profile",
        params={"repo": str(repo), "dataset_id": "customers"},
        files={"file": ("customers.csv", csv_file, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "customers"
    assert data["format"] == "csv"
    assert data["profile"]["row_count"] == 2
    assert data["profile"]["column_count"] == 2


def test_api_v1_import_profile_xlsx(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    repo = _build_repo(tmp_path)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["id", "name"])
    ws.append(["1", "Alice"])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = client.post(
        "/api/v1/imports/profile",
        params={"repo": str(repo), "dataset_id": "customers"},
        files={
            "file": (
                "customers.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "customers"
    assert data["format"] == "xlsx"
    assert data["profile"]["sheet_names"] == ["Sheet1"]


def test_api_v1_import_profile_rejects_unknown_format(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    response = client.post(
        "/api/v1/imports/profile",
        params={"repo": str(repo)},
        files={"file": ("customers.txt", BytesIO(b"id\n1\n"), "text/plain")},
    )
    assert response.status_code == 400


def test_api_v1_import_preview_xlsx(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    repo = _build_repo(tmp_path)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attribute"
    ws.append(["id", "type", "status", "name", "domain"])
    ws.append(["ATTR-NEW", "Attribute", "draft", "New Attribute", "DOMAIN-TEST"])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = client.post(
        "/api/v1/imports/preview",
        params={"repo": str(repo)},
        files={
            "file": (
                "edits.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    proposal = data["proposal"]
    assert proposal["type"] == "PatchProposal"
    assert proposal["id"].startswith("PP-IMPORT-")
    assert any(op["object_id"] == "ATTR-NEW" for op in proposal["operations"])

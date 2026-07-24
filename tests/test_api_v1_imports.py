"""Tests for the versioned import profile and preview endpoints."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from modelops_core.api.app import app
from modelops_core.api.workspace import clear_workspace, configure_workspace

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


def test_api_v1_import_inspect_interprets_workbook_without_model_mutation(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    repo = _build_repo(tmp_path)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BP mapping"
    ws.append(["Legacy field", "S/4 target", "Rule"])
    ws.append(["BUT000.PARTNER", "KNA1.KUNNR", '=CONCAT(A2, "-BP")'])
    ws.merge_cells("A4:C4")
    ws["A2"].comment = openpyxl.comments.Comment("Confirm with data steward", "reviewer")
    hidden = wb.create_sheet("Reference values")
    hidden.sheet_state = "hidden"
    hidden.append(["Code"])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    before = sorted(path.relative_to(repo).as_posix() for path in (repo / "model").rglob("*"))
    response = client.post(
        "/api/v1/imports/inspect",
        params={"repo": str(repo)},
        files={
            "file": (
                "bp-mapping.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    inspection = response.json()["inspection"]
    assert inspection["status"] == "warning"
    assert inspection["formula_count"] == 1
    assert inspection["comment_count"] == 1
    assert inspection["hidden_sheets"] == ["Reference values"]
    assert inspection["merged_ranges"] == {"BP mapping": ["A4:C4"]}
    assert inspection["sheets"][1]["included"] is False
    assert inspection["sheets"][1]["exclusion_reason"]
    assert any("never executed" in item for item in inspection["assumptions"])
    after = sorted(path.relative_to(repo).as_posix() for path in (repo / "model").rglob("*"))
    assert after == before


def test_api_v1_evidence_import_paths_work_when_canonical_mutations_are_disabled(
    tmp_path: Path,
) -> None:
    """The Workbench may inspect/profile evidence in its default read-only mode."""
    repo = _build_repo(tmp_path)
    configure_workspace(repo)
    try:
        response = client.post(
            "/api/v1/imports/profile",
            files={"file": ("customers.csv", BytesIO(b"id,name\n1,Alice\n"), "text/csv")},
        )
    finally:
        clear_workspace()

    assert response.status_code == 200
    assert response.json()["profile"]["row_count"] == 1


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


def _xlsx_buffer(rows: list[list[str]], sheet_title: str = "Attribute") -> BytesIO:
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title
    for row in rows:
        ws.append(row)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def test_api_v1_import_validate_valid_review_workbook(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    buffer = _xlsx_buffer(
        [
            ["id", "type", "status", "name", "domain"],
            ["ATTR-TEST", "Attribute", "draft", "Renamed Attribute", "DOMAIN-TEST"],
        ]
    )

    response = client.post(
        "/api/v1/imports/validate",
        params={"repo": str(repo)},
        files={
            "file": (
                "review.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["workbook_object_count"] == 1
    assert data["overlap_count"] == 1
    assert not data["errors"]


def test_api_v1_import_validate_rejects_unrelated_workbook(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    buffer = _xlsx_buffer(
        [
            ["id", "type", "status", "name", "domain"],
            ["ATTR-OTHER", "Attribute", "draft", "Other Attribute", "DOMAIN-TEST"],
        ]
    )

    response = client.post(
        "/api/v1/imports/validate",
        params={"repo": str(repo)},
        files={
            "file": (
                "review.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["overlap_count"] == 0
    assert any("does not match" in err for err in data["errors"])


def test_api_v1_import_validate_rejects_workbook_missing_ids(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    buffer = _xlsx_buffer(
        [
            ["id", "type", "status", "name", "domain"],
            ["", "Attribute", "draft", "Missing ID", "DOMAIN-TEST"],
        ]
    )

    response = client.post(
        "/api/v1/imports/validate",
        params={"repo": str(repo)},
        files={
            "file": (
                "review.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("missing stable" in err.lower() for err in data["errors"])


def test_api_v1_import_propose_creates_patch_proposal(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    buffer = _xlsx_buffer(
        [
            ["id", "type", "status", "name", "domain"],
            ["ATTR-TEST", "Attribute", "draft", "Renamed Attribute", "DOMAIN-TEST"],
        ]
    )

    response = client.post(
        "/api/v1/imports/propose",
        params={"repo": str(repo)},
        files={
            "file": (
                "review.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["proposal_id"].startswith("PP-IMPORT-")
    assert data["operations_count"] == 1
    proposal_path = repo / "model" / "patch-proposals" / f"{data['proposal_id']}.md"
    assert proposal_path.is_file()


def test_api_v1_import_propose_rejects_invalid_workbook(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    buffer = _xlsx_buffer(
        [
            ["id", "type", "status", "name", "domain"],
            ["ATTR-OTHER", "Attribute", "draft", "Other Attribute", "DOMAIN-TEST"],
        ]
    )

    response = client.post(
        "/api/v1/imports/propose",
        params={"repo": str(repo)},
        files={
            "file": (
                "review.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 400

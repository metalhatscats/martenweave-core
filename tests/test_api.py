"""Tests for the local API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from modelops_core.api.app import app
from modelops_core.cli import app as cli_app

client = TestClient(app)
runner = CliRunner()


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
    response = client.get("/objects", params={"repo": str(sample_repo), "type": "MasterDataDomain"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "MasterDataDomain"


def test_api_get_object(sample_repo: Path) -> None:
    response = client.get("/objects/DOMAIN-CUSTOMER-BP", params={"repo": str(sample_repo)})
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


def test_api_impact_success(sample_repo: Path) -> None:
    response = client.get("/impact/DOMAIN-CUSTOMER-BP", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["object_id"] == "DOMAIN-CUSTOMER-BP"
    assert "root_object_type" in data
    assert "upstream" in data
    assert "downstream" in data
    assert "total_affected" in data
    assert isinstance(data["upstream"], list)
    assert isinstance(data["downstream"], list)


def test_api_impact_missing_index(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.get("/impact/DOMAIN-TEST", params={"repo": repo})
    assert response.status_code == 400
    assert "Index not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# trace
# ---------------------------------------------------------------------------


def test_api_trace_success(sample_repo: Path) -> None:
    response = client.get("/trace/FEP-S4-KNVV-KDGRP", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["root_object_id"] == "FEP-S4-KNVV-KDGRP"
    assert "root_object_type" in data
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)


def test_api_trace_missing_index(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.get("/trace/DOMAIN-TEST", params={"repo": repo})
    assert response.status_code == 400
    assert "Index not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# impact after explicit index build
# ---------------------------------------------------------------------------


def test_api_impact_success_after_build(sample_repo: Path) -> None:
    # Ensure a fresh index is built before testing impact
    db_path = sample_repo / "generated" / "modelops.db"
    if db_path.exists():
        db_path.unlink()
    result = runner.invoke(cli_app, ["build-index", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert db_path.exists()

    response = client.get("/impact/DOMAIN-CUSTOMER-BP", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["object_id"] == "DOMAIN-CUSTOMER-BP"
    assert "root_object_type" in data
    assert isinstance(data["upstream"], list)
    assert isinstance(data["downstream"], list)
    assert "total_affected" in data


# ---------------------------------------------------------------------------
# proposal validation
# ---------------------------------------------------------------------------


def _create_test_proposal(model_path: Path, proposal_id: str, status: str) -> Path:
    proposals_dir = model_path / "patch-proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    proposal_path = proposals_dir / f"{proposal_id}.md"
    proposal_path.write_text(
        f"---\n"
        f"id: {proposal_id}\n"
        f"type: PatchProposal\n"
        f"status: {status}\n"
        f"name: Test Proposal\n"
        f"operations:\n"
        f"  - op: update_object\n"
        f"    object_id: DOMAIN-TEST\n"
        f"    target_path: name\n"
        f"    after: Updated Name\n"
        f"---\n\n# Test Proposal\n",
        encoding="utf-8",
    )
    return proposal_path


def test_api_validate_proposal_success(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    _create_test_proposal(temp_model_dir, "PP-TEST-001", "pending_review")
    response = client.post("/proposals/PP-TEST-001/validate", params={"repo": repo})
    assert response.status_code == 200
    data = response.json()
    assert data["proposal_id"] == "PP-TEST-001"
    assert "valid" in data
    assert "errors" in data
    assert "warnings" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_api_validate_proposal_not_found(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.post("/proposals/PP-MISSING/validate", params={"repo": repo})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# proposal dry-run
# ---------------------------------------------------------------------------


def test_api_dry_run_proposal_not_found(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.post("/proposals/PP-MISSING/dry-run", params={"repo": repo})
    assert response.status_code == 200
    data = response.json()
    assert data["proposal_id"] == "PP-MISSING"
    assert data["would_change"] is False
    assert data["error"] is not None
    assert "not found" in data["error"].lower()


def test_api_dry_run_proposal_not_accepted(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    _create_test_proposal(temp_model_dir, "PP-TEST-002", "pending_review")
    response = client.post("/proposals/PP-TEST-002/dry-run", params={"repo": repo})
    assert response.status_code == 200
    data = response.json()
    assert data["proposal_id"] == "PP-TEST-002"
    assert data["would_change"] is False
    assert data["error"] is not None
    assert "accepted" in data["error"].lower()


# ---------------------------------------------------------------------------
# proposal apply
# ---------------------------------------------------------------------------


def test_api_apply_proposal_not_found(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.post("/proposals/PP-MISSING/apply", params={"repo": repo})
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_api_apply_proposal_not_accepted(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    _create_test_proposal(temp_model_dir, "PP-TEST-003", "pending_review")
    response = client.post("/proposals/PP-TEST-003/apply", params={"repo": repo})
    assert response.status_code == 400
    assert "accepted" in response.json()["detail"].lower()


def test_api_apply_proposal_already_applied(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    _create_test_proposal(temp_model_dir, "PP-TEST-004", "accepted")
    # Mark as already applied
    proposal_path = temp_model_dir / "patch-proposals" / "PP-TEST-004.md"
    content = proposal_path.read_text(encoding="utf-8")
    content = content.replace(
        "status: accepted", "status: accepted\napplied_at: 2024-01-01T00:00:00Z"
    )
    proposal_path.write_text(content, encoding="utf-8")
    response = client.post("/proposals/PP-TEST-004/apply", params={"repo": repo})
    assert response.status_code == 400
    assert "already been applied" in response.json()["detail"].lower()

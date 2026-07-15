"""Tests for the report generation API endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from modelops_core.api.app import app

client = TestClient(app)


def test_generate_gap_report(sample_repo: Path) -> None:
    response = client.post(
        "/api/v1/reports/generate",
        params={"repo": str(sample_repo)},
        json={"report_type": "gap_report"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["artifact_id"].startswith("reports/")
    assert data["format"] == "json"
    assert data["name"].startswith("gap-report-")
    assert data["created_at"]

    artifact_path = sample_repo / "generated" / data["artifact_id"]
    assert artifact_path.exists()
    assert artifact_path.suffix == ".json"


def test_generate_model_summary(sample_repo: Path) -> None:
    response = client.post(
        "/api/v1/reports/generate",
        params={"repo": str(sample_repo)},
        json={"report_type": "model_summary"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["artifact_id"].startswith("reports/")
    assert data["format"] == "md"
    assert data["name"].startswith("model-summary-")
    assert data["created_at"]

    artifact_path = sample_repo / "generated" / data["artifact_id"]
    assert artifact_path.exists()
    assert artifact_path.suffix == ".md"
    content = artifact_path.read_text(encoding="utf-8")
    assert "# Model Summary" in content


def test_generate_unsupported_report_type(sample_repo: Path) -> None:
    response = client.post(
        "/api/v1/reports/generate",
        params={"repo": str(sample_repo)},
        json={"report_type": "not_a_real_report"},
    )
    assert response.status_code == 400
    assert "Unsupported report_type" in response.json()["detail"]

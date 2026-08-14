"""Tests for the persisted start-run result API (issue #626)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from modelops_core.api.app import app as api_app
from modelops_core.cli import app as cli_app

client = TestClient(api_app)
runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _start_workspace(tmp_path: Path, fixture: str = "customer_sample.csv") -> tuple[dict, Path]:
    workspace = tmp_path / "workspace"
    result = runner.invoke(
        cli_app,
        ["start", str(FIXTURES_DIR / fixture), "--out", str(workspace), "--no-open", "--json"],
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output), workspace


def test_start_result_unavailable_for_plain_workspace(sample_repo: Path) -> None:
    """A workspace not created by `martenweave start` reports available=False."""
    response = client.get("/api/v1/start-result", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False
    assert data["total_findings"] == 0
    assert data["findings"] == []


def test_start_result_matches_manifest_verdict_and_count(tmp_path: Path) -> None:
    """The API returns the same verdict and finding count as the persisted manifest."""
    manifest, workspace = _start_workspace(tmp_path)

    response = client.get("/api/v1/start-result", params={"repo": str(workspace)})

    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["verdict"] == manifest["readiness"]["verdict"] == "blocked"
    assert data["total_findings"] == manifest["readiness"]["total_findings"]
    assert data["total_findings"] > 0
    assert len(data["findings"]) == data["total_findings"]


def test_start_result_findings_have_stable_ids_evidence_and_actions(tmp_path: Path) -> None:
    _, workspace = _start_workspace(tmp_path)

    data = client.get("/api/v1/start-result", params={"repo": str(workspace)}).json()

    for finding in data["findings"]:
        assert finding["id"].startswith("GAP-")
        assert finding["evidence_refs"]
        assert finding["recommended_action"]
        assert finding["provenance"]["assessment_run_id"]
    assert data["recommended_next_action"]


def test_start_result_evidence_artifacts_are_generated_relative_and_safe(tmp_path: Path) -> None:
    """Evidence links resolve through the reports download API; no absolute paths leak."""
    manifest, workspace = _start_workspace(tmp_path)

    data = client.get("/api/v1/start-result", params={"repo": str(workspace)}).json()

    evidence = data["evidence"]
    assert evidence["readiness_json"] == "readiness/readiness.json"
    assert evidence["readiness_markdown"] == "readiness/readiness.md"
    assert evidence["profile"] == "dataset_profiles/customer_sample.json"
    assert evidence["draft_proposal"] == manifest["generated_outputs"]["draft_proposal"]

    for key in ("readiness_json", "readiness_markdown", "profile"):
        download = client.get(
            f"/api/v1/reports/{evidence[key]}", params={"repo": str(workspace)}
        )
        assert download.status_code == 200, key

    serialized = json.dumps(data)
    assert str(workspace) not in serialized
    assert manifest["input"]["path"] not in serialized


def test_start_result_provenance_identifies_input_without_absolute_path(tmp_path: Path) -> None:
    manifest, workspace = _start_workspace(tmp_path)

    data = client.get("/api/v1/start-result", params={"repo": str(workspace)}).json()

    provenance = data["provenance"]
    assert provenance["input_name"] == "customer_sample.csv"
    assert provenance["input_format"] == "csv"
    assert provenance["input_sha256"] == manifest["input"]["sha256"]
    assert provenance["created_at"] == manifest["created_at"]


def test_start_result_corrupt_artifacts_report_unavailable(tmp_path: Path) -> None:
    _, workspace = _start_workspace(tmp_path)
    (workspace / "generated" / "readiness" / "readiness.json").write_text(
        "not json", encoding="utf-8"
    )

    data = client.get("/api/v1/start-result", params={"repo": str(workspace)}).json()

    assert data["available"] is False


def test_capabilities_advertise_start_result(sample_repo: Path) -> None:
    data = client.get("/api/v1/capabilities", params={"repo": str(sample_repo)}).json()
    names = {entry["name"] for entry in data["read"]}
    assert "start_result" in names

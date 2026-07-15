"""Tests for the local API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from modelops_core.api.app import app
from modelops_core.api.workspace import clear_workspace, configure_workspace
from modelops_core.cli import app as cli_app
from modelops_core.reports.audit_service import AuditEventService, create_audit_event

client = TestClient(app)
runner = CliRunner()


def test_api_health(sample_repo: Path) -> None:
    response = client.get("/health", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "no_index")
    assert data["repository"] == str(sample_repo)


def test_bound_api_rejects_workspace_switch_and_hides_path(
    sample_repo: Path, tmp_path: Path
) -> None:
    configure_workspace(sample_repo)
    try:
        rejected = client.get("/health", params={"repo": str(tmp_path)})
        assert rejected.status_code == 403
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["repository"] == "."
        mutation = client.post("/export")
        assert mutation.status_code == 403
    finally:
        clear_workspace()


def test_bound_api_requires_token_for_mutation(temp_model_dir: Path) -> None:
    configure_workspace(temp_model_dir.parent, mutation_token="local-secret")
    try:
        denied = client.post("/export")
        assert denied.status_code == 401
        allowed = client.post("/export", headers={"X-Martenweave-Token": "local-secret"})
        assert allowed.status_code == 200
    finally:
        clear_workspace()


def test_bound_api_rejects_external_and_symlinked_dataset(
    sample_repo: Path, tmp_path: Path
) -> None:
    outside = tmp_path / "outside.csv"
    outside.write_text("id\n1\n")
    linked = sample_repo / "data" / "outside-link.csv"
    linked.symlink_to(outside)
    configure_workspace(sample_repo, mutation_token="local-secret")
    try:
        for dataset in (outside, linked):
            response = client.post(
                "/gaps",
                params={"dataset": str(dataset)},
                headers={"X-Martenweave-Token": "local-secret"},
            )
            assert response.status_code == 403
    finally:
        clear_workspace()


def test_api_list_objects(sample_repo: Path) -> None:
    response = client.get("/objects", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    ids = [obj["id"] for obj in data]
    assert "DOMAIN-CUSTOMER-BP" in ids


def test_api_activity_distinguishes_canonical_and_generated_events(sample_repo: Path) -> None:
    audit = AuditEventService(sample_repo)
    generated = create_audit_event(event_type="index_rebuilt")
    generated.timestamp = "2026-07-15T09:00:00Z"
    audit.emit(generated)
    applied = create_audit_event(
        event_type="proposal_applied",
        proposal_id="PP-001",
        changed_object_ids=["DOMAIN-CUSTOMER-BP"],
    )
    applied.timestamp = "2026-07-15T10:00:00Z"
    audit.emit(applied)
    response = client.get("/api/v1/activity", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 2
    event_by_type = {event["event_type"]: event for event in data["events"]}
    assert event_by_type["proposal_applied"]["canonical_change"] is True
    assert event_by_type["proposal_applied"]["source_state"] == "canonical"
    assert event_by_type["index_rebuilt"]["canonical_change"] is False
    assert event_by_type["index_rebuilt"]["source_state"] == "generated"


def test_api_activity_is_empty_without_audit_log(temp_model_dir: Path) -> None:
    response = client.get("/api/v1/activity", params={"repo": str(temp_model_dir.parent)})
    assert response.status_code == 200
    assert response.json() == {"total_count": 0, "events": []}


def test_api_lists_and_downloads_generated_reports_without_exposing_paths(
    sample_repo: Path,
) -> None:
    generated = sample_repo / "generated" / "assessment"
    generated.mkdir(parents=True, exist_ok=True)
    report = generated / "review.md"
    report.write_text("# Review pack\n", encoding="utf-8")

    response = client.get("/api/v1/reports", params={"repo": str(sample_repo)})

    assert response.status_code == 200
    artifact = next(
        item
        for item in response.json()["artifacts"]
        if item["artifact_id"] == "assessment/review.md"
    )
    assert artifact["name"] == "review.md"
    assert artifact["format"] == "MD"
    assert artifact["source_state"] == "generated"
    assert artifact["safety_classification"] == "local_only"
    assert str(sample_repo) not in str(artifact)

    download = client.get("/api/v1/reports/assessment/review.md", params={"repo": str(sample_repo)})
    assert download.status_code == 200
    assert download.text == "# Review pack\n"

    traversal = client.get(
        "/api/v1/reports/../../modelops.config.yaml", params={"repo": str(sample_repo)}
    )
    assert traversal.status_code in {400, 404}


def test_api_lists_typed_assessment_findings_with_separate_review_state(sample_repo: Path) -> None:
    from modelops_core.assessment.finding_contract import AssessmentFinding

    assessment = sample_repo / "generated" / "assessment-run"
    assessment.mkdir(parents=True)
    finding = AssessmentFinding(
        id="FINDING-TEST",
        category="missing_mapping",
        severity="high",
        message="Customer Group is missing a target mapping.",
        provenance={
            "assessment_run_id": "ASSESSMENT-TEST",
            "source_kind": "mapping_profile",
            "location": {"sheet": "Mapping", "row": 2},
        },
    )
    (assessment / "findings.json").write_text(
        json.dumps({"findings": [finding.model_dump(mode="json")]}), encoding="utf-8"
    )
    (assessment / "finding-reviews.json").write_text(
        json.dumps({"reviews": {"FINDING-TEST": {"disposition": "confirmed"}}}),
        encoding="utf-8",
    )

    response = client.get("/api/v1/findings", params={"repo": str(sample_repo)})

    assert response.status_code == 200
    item = response.json()["findings"][0]
    assert item["assessment_id"] == "assessment-run"
    assert item["finding"]["id"] == "FINDING-TEST"
    assert item["finding"]["provenance"]["source_kind"] == "mapping_profile"
    assert item["review"] == {"disposition": "confirmed"}


def test_api_compares_typed_assessments_inside_workspace(sample_repo: Path) -> None:
    from modelops_core.assessment.finding_contract import AssessmentFinding

    def write_run(name: str, run_id: str, severity: str) -> Path:
        run_dir = sample_repo / "generated" / name
        run_dir.mkdir(parents=True)
        manifest = {
            "run_id": run_id,
            "input_fingerprint": run_id,
            "input_checksums": {"mapping": run_id},
            "martenweave_version": "0.6.0",
        }
        finding = AssessmentFinding(
            id="FINDING-TEST",
            category="missing_mapping",
            severity=severity,
            message="Missing mapping",
            provenance={
                "assessment_run_id": run_id,
                "source_kind": "mapping_profile",
                "location": {"sheet": "Mappings", "row": 2},
            },
        )
        (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (run_dir / "findings.json").write_text(
            json.dumps({"findings": [finding.model_dump(mode="json")]}), encoding="utf-8"
        )
        return run_dir / "manifest.json"

    base = write_run("assessment-base", "ASSESSMENT-BASE", "low")
    head = write_run("assessment-head", "ASSESSMENT-HEAD", "high")
    response = client.get(
        "/api/v1/assessment-comparisons",
        params={
            "repo": str(sample_repo),
            "base_manifest": str(base),
            "head_manifest": str(head),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["counts"] == {"severity_changed": 1}
    assert data["findings"][0]["finding_id"] == "FINDING-TEST"


def test_bound_api_rejects_external_assessment_manifest(sample_repo: Path, tmp_path: Path) -> None:
    outside = tmp_path / "manifest.json"
    outside.write_text("{}", encoding="utf-8")
    configure_workspace(sample_repo)
    try:
        response = client.get(
            "/api/v1/assessment-comparisons",
            params={"base_manifest": str(outside), "head_manifest": str(outside)},
        )
        assert response.status_code == 403
    finally:
        clear_workspace()


def test_api_lists_safe_typed_assessment_manifests(sample_repo: Path) -> None:
    package = sample_repo / "generated" / "assessment-run"
    package.mkdir(parents=True)
    (package / "manifest.json").write_text(
        json.dumps({"run_id": "ASSESSMENT-TEST", "created_at": "2026-07-15T12:00:00Z"}),
        encoding="utf-8",
    )
    (package / "findings.json").write_text(
        json.dumps({"findings": [{"id": "FINDING-1"}]}), encoding="utf-8"
    )
    (sample_repo / "generated" / "broken" / "manifest.json").parent.mkdir(parents=True)
    (sample_repo / "generated" / "broken" / "manifest.json").write_text("{}", encoding="utf-8")

    response = client.get("/api/v1/assessment-manifests", params={"repo": str(sample_repo)})

    assert response.status_code == 200
    assert response.json() == {
        "total_count": 1,
        "manifests": [
            {
                "manifest_id": "assessment-run/manifest.json",
                "run_id": "ASSESSMENT-TEST",
                "created_at": "2026-07-15T12:00:00Z",
                "finding_count": 1,
            }
        ],
    }


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


def test_api_impact_not_found(sample_repo: Path) -> None:
    """Unknown object IDs must yield a clear 404, not an empty 200 report."""
    response = client.get("/impact/DOES-NOT-EXIST", params={"repo": str(sample_repo)})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_impact_missing_index(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.get("/impact/DOMAIN-TEST", params={"repo": repo})
    assert response.status_code == 400
    assert "Index not found" in response.json()["detail"]
    assert response.json()["error"] == {
        "code": "INDEX_MISSING",
        "message": "Index not found. Run build-index first.",
        "recovery": {
            "code": "BUILD_INDEX",
            "label": "Build the disposable local index",
            "command": "martenweave build-index --repo .",
            "requires_confirmation": False,
        },
    }


def test_api_recovery_errors_preserve_workspace_safety(sample_repo: Path, tmp_path: Path) -> None:
    configure_workspace(sample_repo)
    try:
        response = client.get("/health", params={"repo": str(tmp_path)})
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "WORKSPACE_CONFLICT"
        assert response.json()["error"]["recovery"]["code"] == "INSPECT_READ_ONLY"
    finally:
        clear_workspace()


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


def test_api_trace_not_found(sample_repo: Path) -> None:
    """Unknown object IDs on the trace endpoint must yield a clear 404."""
    response = client.get("/trace/DOES-NOT-EXIST", params={"repo": str(sample_repo)})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


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
    assert response.status_code == 404
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


# ---------------------------------------------------------------------------
# proposal apply risk / CR gates (issue #437)
# ---------------------------------------------------------------------------


def test_api_apply_high_risk_blocked_without_cr(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "MAP-001.md").write_text(
        "---\nid: MAP-001\ntype: Mapping\nstatus: active\nname: Test Mapping\n---\n",
        encoding="utf-8",
    )
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-API-HIGH-001.md").write_text(
        "---\n"
        "id: PP-API-HIGH-001\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: MAP-001\n"
        "    target_path: name\n"
        "    after: New\n"
        "---\n",
        encoding="utf-8",
    )

    response = client.post("/proposals/PP-API-HIGH-001/apply", params={"repo": str(repo_root)})
    assert response.status_code == 400
    data = response.json()
    assert "requires an approved ChangeRequest" in data["detail"]


def test_api_apply_high_risk_allowed_with_cr(tmp_path: Path) -> None:
    from modelops_core.change_request.service import (
        approve_change_request,
        create_change_request,
    )

    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "MAP-001.md").write_text(
        "---\nid: MAP-001\ntype: Mapping\nstatus: active\nname: Test Mapping\n---\n",
        encoding="utf-8",
    )
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-API-HIGH-002.md").write_text(
        "---\n"
        "id: PP-API-HIGH-002\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: MAP-001\n"
        "    target_path: name\n"
        "    after: New\n"
        "---\n",
        encoding="utf-8",
    )

    create_change_request(
        model_path=model_dir,
        cr_id="CR-API-002",
        title="Approve PP-API-HIGH-002",
        status="pending",
        linked_proposals=["PP-API-HIGH-002"],
        affected_objects=["MAP-001"],
    )
    with pytest.raises(ValueError, match="requires 2 distinct approvers"):
        approve_change_request(model_dir, "CR-API-002", "alice")
    approve_change_request(model_dir, "CR-API-002", "bob")

    response = client.post("/proposals/PP-API-HIGH-002/apply", params={"repo": str(repo_root)})
    assert response.status_code == 200
    data = response.json()
    assert data["proposal_id"] == "PP-API-HIGH-002"
    assert len(data["changed_files"]) > 0


def test_api_apply_high_risk_skip_still_requires_cr(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "MAP-001.md").write_text(
        "---\nid: MAP-001\ntype: Mapping\nstatus: active\nname: Test Mapping\n---\n",
        encoding="utf-8",
    )
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-API-HIGH-003.md").write_text(
        "---\n"
        "id: PP-API-HIGH-003\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: MAP-001\n"
        "    target_path: name\n"
        "    after: New\n"
        "---\n",
        encoding="utf-8",
    )

    response = client.post(
        "/proposals/PP-API-HIGH-003/apply",
        params={"repo": str(repo_root), "skip_risk_check": "true"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "requires an approved ChangeRequest" in data["detail"]


def test_api_apply_medium_risk_blocked_without_cr(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "ATTR-001.md").write_text(
        "---\nid: ATTR-001\ntype: Attribute\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-API-MED-001.md").write_text(
        "---\n"
        "id: PP-API-MED-001\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: ATTR-001\n"
        "    target_path: name\n"
        "    after: New\n"
        "---\n",
        encoding="utf-8",
    )

    response = client.post("/proposals/PP-API-MED-001/apply", params={"repo": str(repo_root)})
    assert response.status_code == 400
    data = response.json()
    assert "approval required" in data["detail"].lower()


# ---------------------------------------------------------------------------
# dataset gaps and readiness
# ---------------------------------------------------------------------------


def _write_csv(path: Path, columns: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(row))
    path.write_text("\n".join(lines), encoding="utf-8")


def _build_repo_with_endpoint(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    (repo / "generated").mkdir(parents=True)

    (repo / "modelops.config.yaml").write_text(
        'schema_version: "1.0"\nworkspace_name: API Test Repo\n',
        encoding="utf-8",
    )
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
    (model_dir / "FEP-TEST.md").write_text(
        "---\n"
        "id: FEP-TEST\n"
        "type: FieldEndpoint\n"
        "status: draft\n"
        "name: Test Field\n"
        "domain: DOMAIN-TEST\n"
        "attribute: ATTR-TEST\n"
        "column_name: CUSTOMER_GROUP\n"
        "---\n",
        encoding="utf-8",
    )
    return repo


def test_api_gaps_success(tmp_path: Path) -> None:
    repo = _build_repo_with_endpoint(tmp_path)
    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["CUSTOMER_GROUP", "UNKNOWN"], [["A", "1"]])

    response = client.post("/gaps", params={"repo": str(repo), "dataset": str(dataset)})
    assert response.status_code == 200
    data = response.json()
    assert data["coverage"]["total_columns"] == 2
    assert data["coverage"]["matched_columns"] == 1
    assert data["coverage"]["unmatched_columns"] == 1
    assert any(g["gap_code"] == "UNMODELED_DATASET_COLUMN" for g in data["dataset_gaps"])
    finding = data["dataset_gaps"][0]["finding"]
    assert finding["lifecycle_state"] == "open"
    assert finding["provenance"]["source_kind"] == "dataset_readiness"


def test_api_gaps_missing_dataset(tmp_path: Path) -> None:
    repo = _build_repo_with_endpoint(tmp_path)
    response = client.post(
        "/gaps", params={"repo": str(repo), "dataset": str(tmp_path / "missing.csv")}
    )
    assert response.status_code == 404
    assert "Dataset not found" in response.json()["detail"]


def test_api_dataset_readiness_success(tmp_path: Path) -> None:
    repo = _build_repo_with_endpoint(tmp_path)
    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["CUSTOMER_GROUP", "UNKNOWN"], [["A", "1"]])

    response = client.post(
        "/dataset-readiness", params={"repo": str(repo), "dataset": str(dataset)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "ready_with_warnings"
    assert data["validation"]["error_count"] == 0
    assert data["coverage"]["matched_columns"] == 1


def test_api_dataset_readiness_unsupported_format(tmp_path: Path) -> None:
    repo = _build_repo_with_endpoint(tmp_path)
    dataset = tmp_path / "customers.txt"
    dataset.write_text("CUSTOMER_GROUP\nA\n", encoding="utf-8")

    response = client.post(
        "/dataset-readiness", params={"repo": str(repo), "dataset": str(dataset)}
    )
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


# ---------------------------------------------------------------------------
# source-state classification (issue #517)
# ---------------------------------------------------------------------------


def test_api_objects_include_source_state(sample_repo: Path) -> None:
    response = client.get("/objects", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data
    for obj in data:
        if obj["type"] == "Evidence":
            assert obj["source_state"] == "evidence"
        else:
            assert obj["source_state"] == "canonical"


def test_api_get_object_includes_source_state(sample_repo: Path) -> None:
    response = client.get("/objects/DOMAIN-CUSTOMER-BP", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    assert response.json()["source_state"] == "canonical"


def test_api_validate_results_are_findings(sample_repo: Path) -> None:
    response = client.get("/validate", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    for result in data["results"]:
        assert result["source_state"] == "finding"


def test_api_gaps_are_findings_and_profile_is_evidence(tmp_path: Path) -> None:
    repo = _build_repo_with_endpoint(tmp_path)
    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["CUSTOMER_GROUP", "UNKNOWN"], [["A", "1"]])

    response = client.post("/gaps", params={"repo": str(repo), "dataset": str(dataset)})
    assert response.status_code == 200
    data = response.json()
    for gap in data["dataset_gaps"]:
        assert gap["source_state"] == "finding"
    for gap in data["model_gaps"]:
        assert gap["source_state"] == "finding"


def test_api_dataset_readiness_source_states(tmp_path: Path) -> None:
    repo = _build_repo_with_endpoint(tmp_path)
    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["CUSTOMER_GROUP", "UNKNOWN"], [["A", "1"]])

    response = client.post(
        "/dataset-readiness", params={"repo": str(repo), "dataset": str(dataset)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_profile"]["source_state"] == "evidence"
    for gap in data["dataset_gaps"]:
        assert gap["source_state"] == "finding"

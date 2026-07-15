"""Tests for the versioned finding-review endpoint."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from modelops_core.api.app import app
from modelops_core.assessment.finding_contract import AssessmentFinding

client = TestClient(app)


def _build_assessment(repo: Path) -> Path:
    assessment = repo / "generated" / "assessment-run"
    assessment.mkdir(parents=True)
    finding = AssessmentFinding(
        id="FINDING-TEST",
        category="missing_mapping",
        severity="high",
        message="Customer Group is missing a target mapping.",
        status="open",
        lifecycle_state="open",
        provenance={
            "assessment_run_id": "ASSESSMENT-TEST",
            "source_kind": "mapping_profile",
            "detection_mode": "deterministic",
            "location": {"sheet": "Mapping", "row": 2},
            "rule_id": "mapping_profile:missing_mapping",
            "evidence_refs": ["mapping_profile.json"],
            "affected_objects": ["Customer Group"],
        },
        rule_id="mapping_profile:missing_mapping",
        evidence_refs=["mapping_profile.json"],
        affected_objects=["Customer Group"],
        recommended_action="Add the target mapping and link it to a canonical attribute.",
        readiness_impact="blocking",
    )
    (assessment / "findings.json").write_text(
        json.dumps({"findings": [finding.model_dump(mode="json")]}), encoding="utf-8"
    )
    return assessment


def test_api_v1_review_finding_persists_review(sample_repo: Path) -> None:
    _build_assessment(sample_repo)

    response = client.post(
        "/api/v1/findings/review",
        params={"repo": str(sample_repo)},
        json={
            "assessment": "assessment-run",
            "finding_id": "FINDING-TEST",
            "disposition": "confirmed",
            "reviewer": "alice",
            "note": "Confirmed after inspection",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["finding_id"] == "FINDING-TEST"
    assert data["disposition"] == "confirmed"
    assert data["reviewer"] == "alice"
    assert data["note"] == "Confirmed after inspection"
    assert data["reviewed_at"] is not None

    reviews_path = sample_repo / "generated" / "assessment-run" / "finding-reviews.json"
    reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
    assert reviews["reviews"]["FINDING-TEST"]["disposition"] == "confirmed"


def test_api_v1_review_finding_invalid_disposition(sample_repo: Path) -> None:
    _build_assessment(sample_repo)

    response = client.post(
        "/api/v1/findings/review",
        params={"repo": str(sample_repo)},
        json={
            "assessment": "assessment-run",
            "finding_id": "FINDING-TEST",
            "disposition": "banana",
        },
    )
    assert response.status_code == 400
    assert "Invalid disposition" in response.json()["detail"]


def test_api_v1_review_finding_missing_assessment(sample_repo: Path) -> None:
    response = client.post(
        "/api/v1/findings/review",
        params={"repo": str(sample_repo)},
        json={
            "assessment": "missing-run",
            "finding_id": "FINDING-TEST",
            "disposition": "confirmed",
        },
    )
    assert response.status_code == 404


def test_api_v1_review_finding_rejects_path_traversal(sample_repo: Path) -> None:
    response = client.post(
        "/api/v1/findings/review",
        params={"repo": str(sample_repo)},
        json={
            "assessment": "../../model",
            "finding_id": "FINDING-TEST",
            "disposition": "confirmed",
        },
    )
    assert response.status_code == 400


def test_api_v1_promote_confirmed_finding(sample_repo: Path) -> None:
    _build_assessment(sample_repo)

    client.post(
        "/api/v1/findings/review",
        params={"repo": str(sample_repo)},
        json={
            "assessment": "assessment-run",
            "finding_id": "FINDING-TEST",
            "disposition": "confirmed",
            "reviewer": "alice",
        },
    )

    response = client.post(
        "/api/v1/findings/promote",
        params={"repo": str(sample_repo)},
        json={
            "assessment": "assessment-run",
            "finding_id": "FINDING-TEST",
            "created_by": "workbench",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["finding_id"] == "FINDING-TEST"
    assert data["proposal_id"].startswith("AR-")
    assert data["proposal_path"].startswith("model/patch-proposals/")

    proposal_path = sample_repo / data["proposal_path"]
    assert proposal_path.exists()


def test_api_v1_promote_unconfirmed_finding_is_rejected(sample_repo: Path) -> None:
    _build_assessment(sample_repo)

    response = client.post(
        "/api/v1/findings/promote",
        params={"repo": str(sample_repo)},
        json={
            "assessment": "assessment-run",
            "finding_id": "FINDING-TEST",
        },
    )
    assert response.status_code == 400
    assert "must be reviewed as 'confirmed'" in response.json()["detail"]

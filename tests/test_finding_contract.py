"""Tests for the typed assessment finding contract and provenance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modelops_core.assessment.assessment_service import generate_assessment_package
from modelops_core.assessment.finding_contract import AssessmentFinding, FindingProvenance
from modelops_core.run.dataset_readiness import generate_dataset_readiness_report
from modelops_core.run.migration_assessment import (
    MappingWorkbookProfile,
    _build_findings,
)


def _minimal_mapping_profile() -> MappingWorkbookProfile:
    return MappingWorkbookProfile(
        file_path="/tmp/mapping.xlsx",
        file_hash="abc123",
        missing_owner_rows=[
            {
                "sheet": "Customer_Mappings",
                "row": 3,
                "key_columns": {"target_table": "KNVV", "target_field": "KDGRP"},
            }
        ],
    )


def test_deterministic_finding_accepts_provenance_and_evidence() -> None:
    finding = AssessmentFinding(
        id="FINDING-1",
        category="missing_owner",
        severity="medium",
        message="Missing owner.",
        status="open",
        lifecycle_state="open",
        provenance=FindingProvenance(
            assessment_run_id="ASSESSMENT-1",
            source_kind="mapping_profile",
            detection_mode="deterministic",
            rule_id="mapping_profile:missing_owner",
            location={"sheet": "Mappings", "row": 2},
            evidence_refs=["mapping_profile.json"],
            affected_objects=["KNVV", "KDGRP"],
        ),
        rule_id="mapping_profile:missing_owner",
        evidence_refs=["mapping_profile.json"],
        affected_objects=["KNVV", "KDGRP"],
        recommended_action="Assign an owner.",
        readiness_impact="ready_with_warnings",
    )
    assert finding.provenance.detection_mode == "deterministic"
    assert finding.rule_id == "mapping_profile:missing_owner"
    assert finding.evidence_refs == ["mapping_profile.json"]
    assert finding.affected_objects == ["KNVV", "KDGRP"]
    assert finding.readiness_impact == "ready_with_warnings"


def test_deterministic_finding_rejects_confidence() -> None:
    with pytest.raises(ValueError, match="Deterministic findings"):
        AssessmentFinding(
            id="FINDING-1",
            category="missing_owner",
            severity="medium",
            message="Missing owner.",
            provenance=FindingProvenance(
                assessment_run_id="ASSESSMENT-1",
                source_kind="mapping_profile",
                detection_mode="deterministic",
            ),
            confidence=0.9,
        )


def test_inferred_finding_allows_confidence() -> None:
    finding = AssessmentFinding(
        id="FINDING-1",
        category="missing_mapping",
        severity="high",
        message="Possibly missing mapping.",
        provenance=FindingProvenance(
            assessment_run_id="ASSESSMENT-1",
            source_kind="ai_suggestion",
            detection_mode="inferred",
        ),
        confidence=0.85,
    )
    assert finding.confidence == 0.85


def test_mapping_profile_findings_include_detection_mode_and_evidence() -> None:
    profile = _minimal_mapping_profile()
    findings = _build_findings(profile, "ASSESSMENT-TEST")
    assert findings
    finding = findings[0]
    assert finding["provenance"]["detection_mode"] == "deterministic"
    assert finding["provenance"]["rule_id"] == "mapping_profile:missing_owner"
    assert "mapping_profile.json" in finding["provenance"]["evidence_refs"]
    assert finding["rule_id"] == "mapping_profile:missing_owner"
    assert finding["readiness_impact"] == "ready_with_warnings"


def test_dataset_readiness_finding_includes_detection_mode_and_rule(
    sample_repo: Path, tmp_path: Path
) -> None:
    dataset = sample_repo / "data" / "samples" / "customer_messy.csv"
    report = generate_dataset_readiness_report(
        repo_root=sample_repo,
        dataset_path=dataset,
        check_model=True,
        dry_run=True,
    )
    assert report.dataset_gaps or report.model_gaps
    all_gaps = report.dataset_gaps + report.model_gaps
    finding = all_gaps[0]["finding"]
    assert finding["provenance"]["detection_mode"] == "deterministic"
    assert finding["provenance"]["rule_id"].startswith("gap:")
    assert finding["provenance"]["evidence_refs"]
    assert finding["readiness_impact"] in ("blocking", "ready_with_warnings", "informational")


def test_assessment_package_writes_model_findings(sample_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "assessment"
    generate_assessment_package(sample_repo, out_dir)

    findings_path = out_dir / "findings.json"
    assert findings_path.exists()
    payload = json.loads(findings_path.read_text(encoding="utf-8"))
    assert "findings" in payload
    assert payload["finding_count"] == len(payload["findings"])
    if payload["findings"]:
        finding = payload["findings"][0]
        assert finding["provenance"]["detection_mode"] == "deterministic"
        assert finding["rule_id"]
        assert finding["readiness_impact"]

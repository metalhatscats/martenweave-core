"""Tests for the assessment finding provenance and run-identity contract.

Covers:
- typed finding schema (#511)
- reproducible assessment run identities and input fingerprints (#512)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modelops_core.assessment.finding_contract import (
    AffectedObject,
    FindingDetectionMode,
    FindingEvidence,
    FindingProvenance,
    FindingSeverity,
    FindingStatus,
    ReadinessFinding,
    ReadinessImpact,
)
from modelops_core.run.migration_assessment import (
    _build_findings,
    _hash_json_object,
    _normalized_workbook_fingerprint,
    _profile_mapping_workbook,
    generate_migration_assessment,
)


def _write_mapping_workbook(path: Path, rows: list[list[str]]) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover
        raise pytest.skip("openpyxl not installed") from exc

    wb = Workbook()
    ws = wb.active
    if ws is None:  # pragma: no cover
        raise RuntimeError("openpyxl did not create an active worksheet")
    ws.title = "Customer_Mappings"
    ws.append(
        [
            "source_field",
            "source_system",
            "target_table",
            "target_field",
            "owner",
            "status",
        ]
    )
    for row in rows:
        ws.append(row)
    wb.save(path)
    wb.close()


def test_readiness_finding_serializes_with_provenance() -> None:
    finding = ReadinessFinding(
        id="mapping:missing_owner:customer_mappings:3",
        category="missing_owner",
        severity=FindingSeverity.MEDIUM,
        status=FindingStatus.OPEN,
        source="mapping_profile",
        message="Missing owner in 'Customer_Mappings' row 3.",
        recommended_action="Assign an owner to the mapping row.",
        readiness_impact=ReadinessImpact.AT_RISK,
        location={"sheet": "Customer_Mappings", "row": 3},
        affected_objects=[
            AffectedObject(object_id="customer_group", object_type="FieldEndpoint", role="source")
        ],
        evidence_refs=[
            FindingEvidence(
                source_type="mapping_workbook",
                source_id="abcd1234",
                location={"sheet": "Customer_Mappings", "row": 3},
                fingerprint="abcd1234",
            )
        ],
        provenance=FindingProvenance(
            detection_mode=FindingDetectionMode.DETERMINISTIC,
            rule_id="mapping_workbook_missing_owner",
            rule_version="0.4.1",
            source_module="modelops_core.run.migration_assessment",
        ),
    )
    data = finding.to_dict()
    assert data["id"] == "mapping:missing_owner:customer_mappings:3"
    assert data["category"] == "missing_owner"
    assert data["severity"] == "medium"
    assert data["readiness_impact"] == "at_risk"
    assert data["provenance"]["detection_mode"] == "deterministic"
    assert data["provenance"]["rule_id"] == "mapping_workbook_missing_owner"
    assert data["evidence_refs"][0]["fingerprint"] == "abcd1234"
    assert data["affected_objects"][0]["role"] == "source"


def test_build_findings_uses_contract(sample_repo: Path, tmp_path: Path) -> None:
    mapping = tmp_path / "mapping.xlsx"
    _write_mapping_workbook(
        mapping,
        [
            ["customer_group", "Legacy CRM", "KNVV", "KDGRP", "sales_team", "active"],
            ["customer_group", "Legacy CRM", "KNVV", "KDGRP", "", "active"],
        ],
    )

    profile = _profile_mapping_workbook(mapping)
    findings = _build_findings(profile)

    assert findings
    missing_owner = next(
        (f for f in findings if f["category"] == "missing_owner"), None
    )
    assert missing_owner is not None
    finding = missing_owner
    assert finding["id"]
    assert finding["severity"] == "medium"
    assert finding["readiness_impact"] == "at_risk"
    assert finding["recommended_action"]
    assert finding["provenance"]["detection_mode"] == "deterministic"
    assert "mapping_workbook_missing_owner" in finding["provenance"]["rule_id"]
    assert finding["evidence_refs"][0]["source_type"] == "mapping_workbook"
    assert finding["affected_objects"]


def test_assessment_manifest_includes_run_id_and_fingerprints(
    sample_repo: Path, tmp_path: Path
) -> None:
    mapping = tmp_path / "mapping.xlsx"
    _write_mapping_workbook(
        mapping,
        [
            ["customer_group", "Legacy CRM", "KNVV", "KDGRP", "sales_team", "active"],
            ["customer_group", "Legacy CRM", "KNVV", "KDGRP", "", "active"],
        ],
    )
    out = tmp_path / "assessment"

    manifest = generate_migration_assessment(
        repo_root=sample_repo,
        mapping_path=mapping,
        dataset_path=None,
        evidence_paths=[],
        out_dir=out,
    )

    assert manifest.run_id
    assert manifest.fingerprints.mapping
    assert manifest.fingerprints.mapping["logical_fingerprint"]
    assert manifest.fingerprints.repo_state["fingerprint"]
    assert manifest.fingerprints.config["fingerprint"] is not None
    assert manifest.run_identity.core_version
    assert manifest.run_identity.schema_version
    assert manifest.run_identity.command.startswith("modelops run migration-assessment")

    manifest_data = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_data["run_id"] == manifest.run_id
    assert manifest_data["fingerprints"]["mapping"]["logical_fingerprint"]
    assert manifest_data["run_identity"]["core_version"]
    assert manifest_data["run_identity"]["schema_version"]

    findings = json.loads((out / "findings.json").read_text(encoding="utf-8"))
    assert findings["findings"]
    first = findings["findings"][0]
    assert "provenance" in first
    assert "evidence_refs" in first
    assert "readiness_impact" in first


def test_assessment_run_id_is_reproducible_for_same_inputs(
    sample_repo: Path, tmp_path: Path
) -> None:
    mapping = tmp_path / "mapping.xlsx"
    _write_mapping_workbook(
        mapping,
        [
            ["customer_group", "Legacy CRM", "KNVV", "KDGRP", "sales_team", "active"],
        ],
    )

    out_a = tmp_path / "assessment_a"
    manifest_a = generate_migration_assessment(
        repo_root=sample_repo,
        mapping_path=mapping,
        dataset_path=None,
        evidence_paths=[],
        out_dir=out_a,
    )

    out_b = tmp_path / "assessment_b"
    manifest_b = generate_migration_assessment(
        repo_root=sample_repo,
        mapping_path=mapping,
        dataset_path=None,
        evidence_paths=[],
        out_dir=out_b,
    )

    assert manifest_a.run_id == manifest_b.run_id
    assert (
        manifest_a.fingerprints.mapping["logical_fingerprint"]
        == manifest_b.fingerprints.mapping["logical_fingerprint"]
    )


def test_workbook_logical_fingerprint_changes_with_content(
    sample_repo: Path, tmp_path: Path
) -> None:
    mapping_a = tmp_path / "mapping_a.xlsx"
    _write_mapping_workbook(
        mapping_a,
        [
            ["customer_group", "Legacy CRM", "KNVV", "KDGRP", "sales_team", "active"],
        ],
    )
    mapping_b = tmp_path / "mapping_b.xlsx"
    _write_mapping_workbook(
        mapping_b,
        [
            ["customer_group", "Legacy CRM", "KNVV", "KDGRP", "sales_team", "active"],
            ["payment_terms", "Legacy CRM", "KNVV", "ZTERM", "finance_team", "active"],
        ],
    )

    profile_a = _profile_mapping_workbook(mapping_a)
    profile_b = _profile_mapping_workbook(mapping_b)

    fp_a = _normalized_workbook_fingerprint(mapping_a, profile_a)
    fp_b = _normalized_workbook_fingerprint(mapping_b, profile_b)

    assert fp_a["logical_fingerprint"] != fp_b["logical_fingerprint"]


def test_deterministic_run_id_from_explicit_inputs() -> None:
    inputs = {
        "core_version": "0.4.1",
        "schema_version": "1.0",
        "domain_packs": ["sap"],
        "fingerprints": {
            "mapping": "map-hash",
            "dataset": "dataset-hash",
            "evidence": ["evidence-hash"],
            "repo_state": "repo-hash",
            "config": "config-hash",
        },
    }
    run_id_1 = _hash_json_object(inputs)
    run_id_2 = _hash_json_object(inputs)
    assert run_id_1 == run_id_2
    assert len(run_id_1) == 64

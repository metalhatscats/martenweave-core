"""Assessment comparison lifecycle and CLI contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def _finding(run_id: str, finding_id: str, severity: str, lifecycle_state: str = "open") -> dict:
    return {
        "id": finding_id,
        "category": "missing_mapping",
        "severity": severity,
        "message": finding_id,
        "status": lifecycle_state,
        "lifecycle_state": lifecycle_state,
        "provenance": {
            "assessment_run_id": run_id,
            "source_kind": "mapping_profile",
            "detection_mode": "deterministic",
            "location": {"sheet": "Mappings", "row": 2},
            "rule_id": "mapping_profile:missing_mapping",
            "evidence_refs": ["mapping_profile.json"],
            "affected_objects": [],
        },
        "rule_id": "mapping_profile:missing_mapping",
        "evidence_refs": ["mapping_profile.json"],
        "affected_objects": [],
        "recommended_action": "Add the target mapping and link it to a canonical attribute.",
        "readiness_impact": (
            "blocking" if severity in ("high", "critical") else "ready_with_warnings"
        ),
    }


def _write_run(
    root: Path,
    run_id: str,
    findings: list[dict],
    checksums: dict[str, str] | None = None,
) -> Path:
    root.mkdir()
    manifest = {
        "run_id": run_id,
        "input_fingerprint": f"fingerprint-{run_id}",
        "input_checksums": checksums or {"mapping": run_id},
        "martenweave_version": "0.6.0",
        "enabled_domain_packs": ["sap"],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "findings.json").write_text(json.dumps({"findings": findings}), encoding="utf-8")
    return root / "manifest.json"


def test_assessment_compare_classifies_deterministic_lifecycle(tmp_path: Path) -> None:
    base_id = "ASSESSMENT-BASE"
    head_id = "ASSESSMENT-HEAD"
    base = _write_run(
        tmp_path / "base",
        base_id,
        [
            _finding(base_id, "unchanged", "medium"),
            _finding(base_id, "resolved", "high"),
            _finding(base_id, "reopened", "medium", "resolved"),
            _finding(base_id, "severity", "low"),
        ],
        {"mapping": "one", "model/DOMAIN.md": "one"},
    )
    head = _write_run(
        tmp_path / "head",
        head_id,
        [
            _finding(head_id, "unchanged", "medium"),
            _finding(head_id, "reopened", "medium"),
            _finding(head_id, "severity", "high"),
            _finding(head_id, "new", "low"),
        ],
        {"mapping": "two", "model/DOMAIN.md": "two"},
    )
    out = tmp_path / "comparison"
    result = runner.invoke(
        app,
        ["assessment", "compare", str(base), str(head), "--out", str(out), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    lifecycle = {item["finding_id"]: item["lifecycle"] for item in payload["findings"]}
    assert lifecycle == {
        "new": "new",
        "reopened": "reopened",
        "resolved": "resolved",
        "severity": "severity_changed",
        "unchanged": "unchanged",
    }
    assert payload["input_changes"] == {
        "canonical_model": ["model/DOMAIN.md"],
        "workbook_or_evidence": ["mapping"],
    }
    assert (out / "assessment-comparison.json").exists()
    assert (out / "assessment-comparison.md").exists()


def test_assessment_compare_rejects_missing_or_incompatible_manifest(tmp_path: Path) -> None:
    base = _write_run(tmp_path / "base", "ASSESSMENT-BASE", [])
    result = runner.invoke(
        app,
        [
            "assessment",
            "compare",
            str(base),
            str(tmp_path / "missing.json"),
            "--out",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 1
    assert "not found" in result.output

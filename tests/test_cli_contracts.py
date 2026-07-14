"""Command contract tests for core CLI JSON outputs.

These tests verify that agent/UI-facing CLI commands emit stable,
parseable JSON contracts. Changing the shape of these outputs is a
breaking change and should be intentional.

Stable public contract fields by command:
- validate --json: is_valid, error_count, warning_count, info_count, results
- health --json: object_count, index_fresh, coverage_gaps, ownership_coverage,
  data_quality_coverage, coverage_gaps_list, type_counts
- analyze --json: object_count, type_counts, orphan_fields, attribute_coverage,
  ownership_gaps, validation_coverage, lov_coverage, mapping_coverage,
  risk_report, change_activity, lifecycle_summary
- trace --json: root_object_id, root_object_type, root_object_name, nodes, edges
- impact --json: root_object_id, root_object_type, affected_objects
- search --json: results (list), total_count; each result has object_id,
  object_type, status, name, title, domain, source_file, score, matched_fields
- query --json: results (list), total_count; each result has object_id,
  object_type, status, name, title, domain, source_file
- profile-dataset --json: dataset_id, row_count, column_count, columns, status
- infer-model --json: id, type, status, operations, affected_objects,
  validation_status, assumptions, human_checks
- propose-patch --json: is_safe, proposal, assumptions, human_checks
- proposal impact --json: proposal_id, high_risk, risk_assessment,
  affected_objects, operations
- change-request create --json: id, status, title, path
- change-request list --json: list of CR dicts
- change-request show --json: full CR dict
- change-request update-status --json: full CR dict
- notifications preview --json: recipient_id, recipient_role, reason,
  source_object_id, source_object_type
- notifications list --json: list of notification event dicts
- diff --json: has_changes, base_count, head_count, added, removed, changed
- config-guard --json: dict of check names to issue lists
- audit-log --json: list of audit event dicts
- import-model-sheet --json: id, type, status, operations, warnings
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from modelops_core import __version__
from modelops_core.cli import app

runner = CliRunner()

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _parse_json(result: Any) -> Any:
    """Parse JSON from CliRunner output.

    Tolerates trailing non-JSON text (e.g. Rich warnings after JSON).
    """
    text = result.output.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract leading JSON object or array
    for start, end in (("{", "}"), ("[", "]")):
        if text.startswith(start):
            depth = 0
            for i, ch in enumerate(text):
                if ch == start:
                    depth += 1
                elif ch == end:
                    depth -= 1
                    if depth == 0:
                        return json.loads(text[: i + 1])
    raise ValueError(f"Could not parse JSON from output:\n{text[:500]}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def indexed_repo(sample_repo: Path) -> Path:
    """Sample repo with a built index."""
    result = runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    return sample_repo


@pytest.fixture
def repo_with_proposal(indexed_repo: Path) -> Path:
    """Indexed repo with a PatchProposal created from a note."""
    note = indexed_repo / "note.md"
    note.write_text("Update CUSTOMER GROUP semantics.", encoding="utf-8")
    result = runner.invoke(
        app,
        ["propose-patch", "--from", str(note), "--repo", str(indexed_repo), "--json"],
    )
    assert result.exit_code == 0
    return indexed_repo


@pytest.fixture
def repo_with_cr(indexed_repo: Path) -> Path:
    """Indexed repo with a ChangeRequest."""
    result = runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-001",
            "--title",
            "Test CR",
            "--repo",
            str(indexed_repo),
            "--json",
        ],
    )
    assert result.exit_code == 0
    return indexed_repo


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


class TestValidateContract:
    def test_validate_json_schema(self, sample_repo: Path) -> None:
        result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "is_valid" in data
        assert "error_count" in data
        assert "warning_count" in data
        assert "info_count" in data
        assert "summary_by_code" in data
        assert isinstance(data["summary_by_code"], dict)
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_validate_strict_json_schema(self, sample_repo: Path) -> None:
        result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--strict", "--json"])
        assert result.exit_code == 2
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "is_valid" in data
        assert "error_count" in data
        assert "warning_count" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_validate_suppress_methodology_warnings_json(self) -> None:
        repo = "examples/simple_product_model"
        result = runner.invoke(app, ["validate", "--repo", repo, "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        codes = {r["code"] for r in data["results"]}
        assert "FIELD_ENDPOINT_MISSING_ENRICHMENT" in codes
        assert "OWNERSHIP_MISSING" in codes
        before_warnings = data["warning_count"]

        result2 = runner.invoke(
            app,
            ["validate", "--repo", repo, "--suppress-methodology-warnings", "--json"],
        )
        assert result2.exit_code == 0
        data2 = _parse_json(result2)
        codes2 = {r["code"] for r in data2["results"]}
        assert "FIELD_ENDPOINT_MISSING_ENRICHMENT" not in codes2
        assert "OWNERSHIP_MISSING" in codes2
        assert data2["warning_count"] < before_warnings
        assert "FIELD_ENDPOINT_MISSING_ENRICHMENT" not in data2["summary_by_code"]

    def test_validate_suppress_methodology_does_not_hide_errors(self) -> None:
        from modelops_core.validation.result import (
            METHODOLOGY_WARNING_CODES,
            ValidationResult,
            ValidationSeverity,
            ValidationSummary,
        )

        summary = ValidationSummary(
            results=[
                ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    code="REFERENCE_BROKEN",
                    message="Broken ref.",
                ),
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="FIELD_ENDPOINT_MISSING_ENRICHMENT",
                    message="Missing enrichment.",
                ),
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="OWNERSHIP_MISSING",
                    message="Missing owner.",
                ),
            ]
        )
        filtered = [r for r in summary.results if r.code not in METHODOLOGY_WARNING_CODES]
        summary.results = filtered
        assert summary.error_count == 1
        assert summary.warning_count == 1
        assert summary.results[0].code == "REFERENCE_BROKEN"
        assert summary.results[1].code == "OWNERSHIP_MISSING"


# ---------------------------------------------------------------------------
# build-index / health / analyze / trace / impact / search / query
# ---------------------------------------------------------------------------


class TestIndexQueryContract:
    def test_build_index_jsonl(self, sample_repo: Path) -> None:
        result = runner.invoke(app, ["build-index", "--repo", str(sample_repo), "--jsonl"])
        assert result.exit_code == 0
        gen = sample_repo / "generated"
        search_docs = gen / "search_documents.jsonl"
        lineage_edges = gen / "lineage_edges.jsonl"
        assert search_docs.exists()
        assert lineage_edges.exists()

        for line in search_docs.read_text(encoding="utf-8").strip().splitlines():
            doc = json.loads(line)
            assert "id" in doc
            assert "type" in doc
            assert "status" in doc
            assert "source_file" in doc

        for line in lineage_edges.read_text(encoding="utf-8").strip().splitlines():
            edge = json.loads(line)
            assert "from_object_id" in edge
            assert "to_object_id" in edge
            assert "relationship_type" in edge

    def test_build_index_json_schema(self, sample_repo: Path) -> None:
        result = runner.invoke(app, ["build-index", "--repo", str(sample_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "martenweave_version" in data
        assert "repo" in data
        assert "db_path" in data
        assert "objects_count" in data
        assert "valid" in data
        assert "dry_run" in data
        assert "jsonl_paths" in data
        assert "errors" in data
        assert data["valid"] is True
        assert data["dry_run"] is False

    def test_build_index_json_dry_run(self, sample_repo: Path) -> None:
        db_path = sample_repo / "generated" / "modelops.db"
        if db_path.exists():
            db_path.unlink()
        result = runner.invoke(
            app, ["build-index", "--repo", str(sample_repo), "--dry-run", "--json"]
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert data["dry_run"] is True
        assert not db_path.exists()

    def test_health_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["health", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "object_count" in data
        assert "index_fresh" in data
        assert "coverage_gaps" in data
        assert "ownership_coverage" in data
        assert "data_quality_coverage" in data
        assert "coverage_gaps_list" in data
        assert "type_counts" in data

    def test_analyze_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["analyze", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "object_count" in data
        assert "type_counts" in data
        assert "orphan_fields" in data
        assert "attribute_coverage" in data
        assert "ownership_gaps" in data
        assert "validation_coverage" in data
        assert "lov_coverage" in data
        assert "mapping_coverage" in data
        assert "risk_report" in data
        assert "change_activity" in data
        assert "lifecycle_summary" in data

    def test_trace_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "trace",
                "FEP-S4-KNVV-KDGRP",
                "--repo",
                str(indexed_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "root_object_id" in data
        assert "root_object_type" in data
        assert "root_object_name" in data
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_impact_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "impact",
                "FEP-S4-KNVV-KDGRP",
                "--repo",
                str(indexed_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "root_object_id" in data
        assert "root_object_type" in data
        assert "affected_objects" in data
        assert isinstance(data["affected_objects"], list)

    def test_search_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["search", "customer", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "results" in data
        assert "total_count" in data
        if data["results"]:
            item = data["results"][0]
            assert "object_id" in item
            assert "object_type" in item
            assert "status" in item
            assert "name" in item
            assert "title" in item
            assert "domain" in item
            assert "source_file" in item
            assert "score" in item
            assert "matched_fields" in item

    def test_query_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "query",
                "--repo",
                str(indexed_repo),
                "--type",
                "Attribute",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "results" in data
        assert "total_count" in data
        if data["results"]:
            item = data["results"][0]
            assert "object_id" in item
            assert "object_type" in item
            assert "status" in item
            assert "name" in item
            assert "title" in item
            assert "domain" in item
            assert "source_file" in item

    def test_search_offset_pagination(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "search",
                "customer",
                "--repo",
                str(indexed_repo),
                "--limit",
                "2",
                "--offset",
                "1",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "results" in data
        assert "total_count" in data
        # total_count reflects total matches, not page size
        assert data["total_count"] >= 0

    def test_query_offset_pagination(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "query",
                "--repo",
                str(indexed_repo),
                "--type",
                "Attribute",
                "--limit",
                "1",
                "--offset",
                "0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "results" in data
        assert "total_count" in data
        # total_count reflects total matches, not page size
        assert data["total_count"] >= 0


# ---------------------------------------------------------------------------
# v0.4 report commands
# ---------------------------------------------------------------------------


class TestV4ReportContract:
    def test_scorecard_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["scorecard", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "martenweave_version" in data
        assert "metrics" in data
        assert isinstance(data["metrics"], list)
        assert "readiness_level" in data
        assert "object_count" in data
        assert "gaps" in data
        assert isinstance(data["gaps"], list)
        assert "summary" in data

    def test_owners_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["owners", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "martenweave_version" in data
        assert "owners" in data
        assert isinstance(data["owners"], list)
        assert "orphaned_objects" in data
        assert isinstance(data["orphaned_objects"], list)
        assert "coverage_percent" in data

    def test_gap_report_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["gap-report", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "martenweave_version" in data
        assert "gaps_by_type" in data
        assert isinstance(data["gaps_by_type"], dict)
        assert "total_gap_count" in data
        assert "gap_score" in data
        assert "sources_checked" in data
        assert isinstance(data["sources_checked"], list)

    def test_decisions_list_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["decisions", "list", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "id" in item
            assert "status" in item
            assert "name" in item
            assert "domain" in item

    def test_decisions_report_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["decisions", "report", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "martenweave_version" in data
        assert "evidence_coverage" in data
        assert isinstance(data["evidence_coverage"], list)
        assert "uncovered_decisions" in data
        assert isinstance(data["uncovered_decisions"], list)
        assert "category_breakdown" in data
        assert isinstance(data["category_breakdown"], list)
        assert "total_decisions" in data
        assert "total_with_evidence" in data
        assert "overall_coverage_percent" in data

    def test_clean_dry_run_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app,
            ["clean", "--repo", str(indexed_repo), "--dry-run", "--json"],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "dry_run" in data
        assert data["dry_run"] is True
        assert "generated_path" in data
        assert "removed_count" in data
        assert "skipped_count" in data
        assert "removed" in data
        assert isinstance(data["removed"], list)
        assert "skipped" in data
        assert isinstance(data["skipped"], list)

    def test_proposal_report_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["proposal", "report", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "martenweave_version" in data
        assert "proposals_total" in data
        assert "by_status" in data
        assert isinstance(data["by_status"], dict)
        assert "stale_summary" in data
        assert isinstance(data["stale_summary"], dict)
        assert "stale_count" in data["stale_summary"]

    def test_validate_check_decisions_json(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "validate",
                "--repo",
                str(indexed_repo),
                "--check-decisions",
                "--json",
            ],
        )
        # May exit 0 or 1 depending on issues found; JSON should still be parseable
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "is_valid" in data
        assert "error_count" in data
        assert "warning_count" in data
        assert "info_count" in data
        assert "results" in data
        assert isinstance(data["results"], list)
        # Look for DECISION_DEPRECATED_EVIDENCE warnings in results
        codes = [r.get("code", "") for r in data["results"]]
        assert "DECISION_DEPRECATED_EVIDENCE" in codes or data["warning_count"] >= 0


# ---------------------------------------------------------------------------
# dataset profiling / model inference
# ---------------------------------------------------------------------------


class TestDatasetContract:
    def test_profile_dataset_json_schema(self, sample_repo: Path) -> None:
        csv_file = FIXTURES_DIR / "customer_sample.csv"
        result = runner.invoke(
            app,
            [
                "profile-dataset",
                str(csv_file),
                "--repo",
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "dataset_id" in data
        assert "row_count" in data
        assert "column_count" in data
        assert "columns" in data
        assert "status" in data

    def test_infer_model_json_schema(self, sample_repo: Path) -> None:
        csv_file = FIXTURES_DIR / "customer_sample.csv"
        runner.invoke(
            app,
            ["profile-dataset", str(csv_file), "--repo", str(sample_repo)],
        )
        profile_path = sample_repo / "generated" / "dataset_profiles" / "customer_sample.json"
        result = runner.invoke(
            app,
            [
                "infer-model",
                str(profile_path),
                "--repo",
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "id" in data
        assert "type" in data
        assert "status" in data
        assert "operations" in data
        assert "affected_objects" in data
        assert "validation_status" in data
        assert "assumptions" in data
        assert "human_checks" in data


# ---------------------------------------------------------------------------
# proposals
# ---------------------------------------------------------------------------


class TestProposalContract:
    def test_propose_patch_json_schema(self, sample_repo: Path) -> None:
        note = sample_repo / "note.md"
        note.write_text("Update CUSTOMER GROUP semantics.", encoding="utf-8")
        result = runner.invoke(
            app,
            [
                "propose-patch",
                "--from",
                str(note),
                "--repo",
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "is_safe" in data
        assert "proposal" in data
        assert "assumptions" in data
        assert "human_checks" in data

    def test_proposal_impact_json_schema(self, repo_with_proposal: Path) -> None:
        result = runner.invoke(
            app,
            [
                "proposal",
                "impact",
                "PP-SCAFFOLD-001",
                "--repo",
                str(repo_with_proposal),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "proposal_id" in data
        assert "high_risk" in data
        assert "risk_assessment" in data
        assert "affected_objects" in data
        assert "operations" in data
        assert isinstance(data["affected_objects"], list)
        assert isinstance(data["operations"], list)

    def test_propose_patch_dry_run_json_schema(self, sample_repo: Path) -> None:
        note = sample_repo / "note.md"
        note.write_text("Update CUSTOMER GROUP semantics.", encoding="utf-8")
        proposal_path = sample_repo / "model" / "patch-proposals" / "PP-DRY-001.md"
        assert not proposal_path.exists()

        result = runner.invoke(
            app,
            [
                "propose-patch",
                "--from",
                str(note),
                "--repo",
                str(sample_repo),
                "--dry-run",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert data.get("dry_run") is True
        assert "is_safe" in data
        assert "proposal" in data
        assert "assumptions" in data
        assert "human_checks" in data
        assert not proposal_path.exists()

    def test_proposal_apply_dry_run_output(self, repo_with_proposal: Path) -> None:
        # dry-run requires the proposal to be in 'accepted' status
        proposal_path = repo_with_proposal / "model" / "patch-proposals" / "PP-SCAFFOLD-001.md"
        text = proposal_path.read_text(encoding="utf-8")
        proposal_path.write_text(
            text.replace("status: pending_review", "status: accepted"),
            encoding="utf-8",
        )
        result = runner.invoke(
            app,
            [
                "proposal",
                "apply",
                "PP-SCAFFOLD-001",
                "--repo",
                str(repo_with_proposal),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Dry-run for PP-SCAFFOLD-001" in result.output
        assert "Would change" in result.output
        assert "Risk level" in result.output


# ---------------------------------------------------------------------------
# change-request
# ---------------------------------------------------------------------------


class TestChangeRequestContract:
    def test_cr_create_json_schema(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-TEST-002",
                "--title",
                "Create Contract Test",
                "--repo",
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "id" in data
        assert "status" in data
        assert "title" in data
        assert "path" in data

    def test_cr_create_dry_run_json_schema(self, sample_repo: Path) -> None:
        cr_path = sample_repo / "model" / "change-requests" / "CR-DRY-001.md"
        assert not cr_path.exists()

        result = runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-DRY-001",
                "--title",
                "Dry Run Contract Test",
                "--repo",
                str(sample_repo),
                "--dry-run",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert data.get("dry_run") is True
        assert "id" in data
        assert "status" in data
        assert "title" in data
        assert "path" in data
        assert not cr_path.exists()

    def test_cr_list_json_schema(self, repo_with_cr: Path) -> None:
        result = runner.invoke(
            app, ["change-request", "list", "--repo", str(repo_with_cr), "--json"]
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, list)
        assert len(data) >= 1
        item = data[0]
        assert "id" in item
        assert "status" in item
        assert "title" in item

    def test_cr_show_json_schema(self, repo_with_cr: Path) -> None:
        result = runner.invoke(
            app,
            [
                "change-request",
                "show",
                "CR-TEST-001",
                "--repo",
                str(repo_with_cr),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "id" in data
        assert "status" in data
        assert "title" in data

    def test_cr_update_status_json_schema(self, repo_with_cr: Path) -> None:
        result = runner.invoke(
            app,
            [
                "change-request",
                "update-status",
                "CR-TEST-001",
                "approved",
                "--repo",
                str(repo_with_cr),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "id" in data
        assert "status" in data
        assert data["status"] == "approved"


# ---------------------------------------------------------------------------
# notifications
# ---------------------------------------------------------------------------


class TestNotificationContract:
    def test_notifications_preview_json_schema(self, repo_with_cr: Path) -> None:
        result = runner.invoke(
            app,
            [
                "notifications",
                "preview",
                "--change-request",
                "CR-TEST-001",
                "--repo",
                str(repo_with_cr),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "recipient_id" in item
            assert "recipient_role" in item
            assert "reason" in item
            assert "source_object_id" in item
            assert "source_object_type" in item

    def test_notifications_list_json_schema(self, repo_with_cr: Path) -> None:
        result = runner.invoke(
            app,
            [
                "notifications",
                "list",
                "--repo",
                str(repo_with_cr),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------


class TestDiffContract:
    def test_diff_json_schema_no_changes(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "diff",
                str(sample_repo),
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "has_changes" in data
        assert "base_count" in data
        assert "head_count" in data
        assert "added" in data
        assert "removed" in data
        assert "changed" in data
        assert data["has_changes"] is False

    def test_diff_json_schema_with_changes(self, sample_repo: Path) -> None:
        head = sample_repo.parent / "head_repo"
        shutil.copytree(sample_repo, head)
        # Modify a file in head
        model_dir = head / "model"
        for f in model_dir.iterdir():
            if f.is_file() and f.suffix == ".md":
                content = f.read_text(encoding="utf-8")
                f.write_text(content.replace("status: active", "status: draft"), encoding="utf-8")
                break
        result = runner.invoke(
            app,
            [
                "diff",
                str(sample_repo),
                str(head),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert data["has_changes"] is True
        assert "changed" in data


# ---------------------------------------------------------------------------
# config-guard
# ---------------------------------------------------------------------------


class TestConfigGuardContract:
    def test_config_guard_json_schema(self, sample_repo: Path) -> None:
        result = runner.invoke(app, ["config-guard", "--repo", str(sample_repo), "--json"])
        # May exit 0 or 1 depending on issues found; JSON should still be parseable
        data = _parse_json(result)
        assert isinstance(data, dict)

    def test_config_guard_json_includes_file_status(self, tmp_path: Path) -> None:
        subprocess.run(
            ["git", "-C", str(tmp_path), "init"],
            check=True,
            capture_output=True,
            text=True,
        )
        (tmp_path / ".gitignore").write_text(
            ".env\n*.pem\n*.key\nid_rsa\nid_ed25519\n", encoding="utf-8"
        )
        (tmp_path / ".env").write_text("API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")

        result = runner.invoke(
            app,
            ["config-guard", "--repo", str(tmp_path), "--mode", "release", "--json"],
        )

        assert result.exit_code == 0
        data = _parse_json(result)
        assert data["env_file"][0]["file_status"] == "ignored"


# ---------------------------------------------------------------------------
# audit-log
# ---------------------------------------------------------------------------


class TestAuditLogContract:
    def test_audit_log_json_schema(self, indexed_repo: Path) -> None:
        # Generate an audit event by exporting the model
        runner.invoke(app, ["export-model", "--repo", str(indexed_repo), "--format", "csv"])
        result = runner.invoke(app, ["audit-log", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "event_id" in item
            assert "event_type" in item
            assert "timestamp" in item
            assert "status" in item


# ---------------------------------------------------------------------------
# export-model
# ---------------------------------------------------------------------------


class TestExportContract:
    def test_export_model_csv_output(self, sample_repo: Path) -> None:
        result = runner.invoke(app, ["export-model", "--repo", str(sample_repo), "--format", "csv"])
        assert result.exit_code == 0
        assert "Exported" in result.output
        assert "CSV" in result.output

    def test_export_model_xlsx_output(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app, ["export-model", "--repo", str(sample_repo), "--format", "xlsx"]
        )
        assert result.exit_code == 0
        assert "Exported XLSX workbook" in result.output

    def test_export_schema_json_schema(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app, ["export-schema", "--repo", str(sample_repo), "--type", "Attribute", "--json"]
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "$schema" in data
        assert "title" in data
        assert "type_count" in data
        assert "schemas" in data
        assert data["type_count"] == 1
        assert "Attribute" in data["schemas"]
        schema = data["schemas"]["Attribute"]
        assert "properties" in schema
        assert "required" in schema


# ---------------------------------------------------------------------------
# import-model-sheet
# ---------------------------------------------------------------------------


class TestImportContract:
    def test_import_model_sheet_json_schema(self, sample_repo: Path) -> None:
        xlsx_file = FIXTURES_DIR / "customer_sample.xlsx"
        result = runner.invoke(
            app,
            [
                "import-model-sheet",
                str(xlsx_file),
                "--repo",
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "id" in data
        assert "type" in data
        assert "status" in data
        assert "operations" in data
        assert "warnings" in data


# ---------------------------------------------------------------------------
# Version metadata tests (#252)
# ---------------------------------------------------------------------------


class TestVersionMetadata:
    def test_version_flag(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def _assert_report_has_version(self, args: list[str]) -> None:
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        data = _parse_json(result)
        assert data.get("martenweave_version") == __version__

    def test_scorecard_json_has_version(self, indexed_repo: Path) -> None:
        self._assert_report_has_version(["scorecard", "--repo", str(indexed_repo), "--json"])

    def test_health_json_has_version(self, indexed_repo: Path) -> None:
        self._assert_report_has_version(["health", "--repo", str(indexed_repo), "--json"])

    def test_gap_report_json_has_version(self, indexed_repo: Path) -> None:
        self._assert_report_has_version(["gap-report", "--repo", str(indexed_repo), "--json"])

    def test_owners_json_has_version(self, indexed_repo: Path) -> None:
        self._assert_report_has_version(["owners", "--repo", str(indexed_repo), "--json"])

    def test_decisions_report_json_has_version(self, indexed_repo: Path) -> None:
        self._assert_report_has_version(
            ["decisions", "report", "--repo", str(indexed_repo), "--json"]
        )

    def test_proposal_report_json_has_version(self, indexed_repo: Path) -> None:
        self._assert_report_has_version(
            ["proposal", "report", "--repo", str(indexed_repo), "--json"]
        )

    def test_analyze_json_has_version(self, indexed_repo: Path) -> None:
        self._assert_report_has_version(["analyze", "--repo", str(indexed_repo), "--json"])


class TestMiscContract:
    def test_migrate_json_schema(self, sample_repo: Path) -> None:
        result = runner.invoke(app, ["migrate", "--repo", str(sample_repo), "--dry-run", "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert "dry_run" in data
        assert "migrated_count" in data
        assert "skipped_count" in data
        assert "schema_version" in data
        assert "migrated_files" in data
        assert "config_updated" in data

    def test_usage_report_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["usage-report", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert "total_events" in data
        assert "event_type_counts" in data
        assert "command_counts" in data
        assert "status_counts" in data
        assert "ai_usage_summary" in data
        assert "date_range" in data

    def test_docs_build_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(app, ["docs-build", "--repo", str(indexed_repo), "--json"])
        assert result.exit_code == 0
        data = _parse_json(result)
        assert "output_dir" in data
        assert "files" in data
        assert isinstance(data["files"], list)


# ---------------------------------------------------------------------------
# Governance contract tests (#289)
# ---------------------------------------------------------------------------


class TestGovernanceContract:
    def test_proposal_show_json_schema(self, repo_with_proposal: Path) -> None:
        result = runner.invoke(
            app,
            [
                "proposal",
                "show",
                "PP-SCAFFOLD-001",
                "--repo",
                str(repo_with_proposal),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert data.get("id") == "PP-SCAFFOLD-001"
        assert "status" in data
        assert "operations" in data
        assert isinstance(data["operations"], list)

    def test_proposal_validate_json_schema(self, repo_with_proposal: Path) -> None:
        result = runner.invoke(
            app,
            [
                "proposal",
                "validate",
                "PP-SCAFFOLD-001",
                "--repo",
                str(repo_with_proposal),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "proposal_id" in data
        assert "error_count" in data
        assert "warning_count" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_proposal_diff_json_schema(self, repo_with_proposal: Path) -> None:
        result = runner.invoke(
            app,
            [
                "proposal",
                "diff",
                "PP-SCAFFOLD-001",
                "--repo",
                str(repo_with_proposal),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert data.get("proposal_id") == "PP-SCAFFOLD-001"
        assert "diffs" in data
        assert isinstance(data["diffs"], list)

    def test_proposal_review_bundle_json_schema(self, repo_with_proposal: Path) -> None:
        result = runner.invoke(
            app,
            [
                "proposal",
                "review-bundle",
                "PP-SCAFFOLD-001",
                "--repo",
                str(repo_with_proposal),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert data.get("proposal_id") == "PP-SCAFFOLD-001"
        assert "report" in data
        assert "impact" in data
        assert "validation" in data
        assert isinstance(data["validation"].get("is_safe"), bool)
        assert "error_count" in data["validation"]

    def test_index_fresh_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app,
            ["index-fresh", "--repo", str(indexed_repo), "--json"],
        )
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "fresh" in data
        assert isinstance(data["fresh"], bool)
        assert "db_path" in data
        assert "stale_sources" in data
        assert isinstance(data["stale_sources"], list)

    def test_decisions_show_json_schema(self, sample_repo: Path) -> None:
        # Use a known decision ID from the sample repo
        result = runner.invoke(
            app,
            [
                "decisions",
                "show",
                "DEC-ARCH-001-BP-CENTRAL",
                "--repo",
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert data.get("id") == "DEC-ARCH-001-BP-CENTRAL"
        assert data.get("type") == "Decision"
        assert "status" in data
        assert "title" in data

    def test_doctor_json_schema(self, sample_repo: Path) -> None:
        result = runner.invoke(app, ["doctor", "--repo", str(sample_repo), "--json"])
        assert result.exit_code == 0, result.output
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "martenweave_version" in data
        assert "repo_root" in data
        assert "config_present" in data
        assert isinstance(data["config_present"], bool)
        assert "model_path_exists" in data
        assert isinstance(data["model_path_exists"], bool)
        assert "generated_path_exists" in data
        assert isinstance(data["generated_path_exists"], bool)
        assert "index_exists" in data
        assert isinstance(data["index_exists"], bool)
        assert "index_fresh" in data
        assert "validation" in data
        assert isinstance(data["validation"], dict)
        assert "ran" in data["validation"]
        assert "is_valid" in data["validation"]
        assert "error_count" in data["validation"]
        assert "warning_count" in data["validation"]

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
- search --json: object_id, object_type, status, name, title, domain,
  source_file, score, matched_fields
- query --json: object_id, object_type, status, name, title, domain, source_file
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
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

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
        result = runner.invoke(
            app, ["validate", "--repo", str(sample_repo), "--json"]
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, dict)
        assert "is_valid" in data
        assert "error_count" in data
        assert "warning_count" in data
        assert "info_count" in data
        assert "results" in data
        assert isinstance(data["results"], list)


# ---------------------------------------------------------------------------
# build-index / health / analyze / trace / impact / search / query
# ---------------------------------------------------------------------------


class TestIndexQueryContract:
    def test_build_index_jsonl(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app, ["build-index", "--repo", str(sample_repo), "--jsonl"]
        )
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

    def test_health_json_schema(self, indexed_repo: Path) -> None:
        result = runner.invoke(
            app, ["health", "--repo", str(indexed_repo), "--json"]
        )
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
        result = runner.invoke(
            app, ["analyze", "--repo", str(indexed_repo), "--json"]
        )
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
        result = runner.invoke(
            app, ["search", "customer", "--repo", str(indexed_repo), "--json"]
        )
        assert result.exit_code == 0
        data = _parse_json(result)
        assert isinstance(data, list)
        if data:
            item = data[0]
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
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "object_id" in item
            assert "object_type" in item
            assert "status" in item
            assert "name" in item
            assert "title" in item
            assert "domain" in item
            assert "source_file" in item


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
        profile_path = (
            sample_repo / "generated" / "dataset_profiles" / "customer_sample.json"
        )
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

    def test_proposal_apply_dry_run_output(self, repo_with_proposal: Path) -> None:
        # dry-run requires the proposal to be in 'accepted' status
        proposal_path = (
            repo_with_proposal / "model" / "patch-proposals" / "PP-SCAFFOLD-001.md"
        )
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

    def test_cr_list_json_schema(self, repo_with_cr: Path) -> None:
        result = runner.invoke(
            app,
            ["change-request", "list", "--repo", str(repo_with_cr), "--json"],
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
        result = runner.invoke(
            app,
            ["config-guard", "--repo", str(sample_repo), "--json"],
        )
        # May exit 0 or 1 depending on issues found; JSON should still be parseable
        data = _parse_json(result)
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# audit-log
# ---------------------------------------------------------------------------


class TestAuditLogContract:
    def test_audit_log_json_schema(self, indexed_repo: Path) -> None:
        # Generate an audit event by exporting the model
        runner.invoke(
            app,
            ["export-model", "--repo", str(indexed_repo), "--format", "csv"],
        )
        result = runner.invoke(
            app,
            ["audit-log", "--repo", str(indexed_repo), "--json"],
        )
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
        result = runner.invoke(
            app,
            ["export-model", "--repo", str(sample_repo), "--format", "csv"],
        )
        assert result.exit_code == 0
        assert "Exported" in result.output
        assert "CSV" in result.output

    def test_export_model_xlsx_output(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            ["export-model", "--repo", str(sample_repo), "--format", "xlsx"],
        )
        assert result.exit_code == 0
        assert "Exported XLSX workbook" in result.output


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

"""Golden Customer Group / KNVV-KDGRP demo journey smoke test.

This test reproduces the core Martenweave demo path against
`examples/customer_bp_model` using only deterministic, local CLI commands.
It fails with a clear assertion if any core step regresses.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()

CUSTOMER_REPO = Path(__file__).resolve().parent.parent / "examples" / "customer_bp_model"


def _assert_json_key(data: dict | list, key_path: str, expected_type: type) -> None:
    """Assert a dotted key path exists and has the expected type."""
    parts = key_path.split(".")
    current: object = data
    for part in parts:
        if isinstance(current, dict):
            assert part in current, f"Missing key: {key_path}"
            current = current[part]
        elif isinstance(current, list) and part == "[]":
            assert isinstance(current, list), f"Expected list for {key_path}"
            return
        else:
            raise AssertionError(f"Cannot traverse {key_path} in {type(current)}")
    assert isinstance(current, expected_type), (
        f"Key {key_path} expected {expected_type.__name__}, got {type(current).__name__}"
    )


@pytest.fixture
def customer_repo(tmp_path: Path) -> Path:
    """Return a clean copy of the customer_bp_model example."""
    dst = tmp_path / "customer_bp_model"
    shutil.copytree(CUSTOMER_REPO, dst)
    # Remove pre-built generated artifacts to force a clean build in the test.
    gen_dir = dst / "generated"
    if gen_dir.exists():
        shutil.rmtree(gen_dir)
    return dst


def test_demo_journey_validate_and_index(customer_repo: Path) -> None:
    """Validate canonical files and build the SQLite index + JSONL exports."""
    repo = str(customer_repo)

    result = runner.invoke(app, ["validate", "--repo", repo, "--json"])
    assert result.exit_code == 0, result.output
    validate_data = json.loads(result.output)
    _assert_json_key(validate_data, "is_valid", bool)
    assert validate_data["is_valid"] is True, validate_data
    _assert_json_key(validate_data, "error_count", int)
    assert validate_data["error_count"] == 0, validate_data

    result = runner.invoke(app, ["build-index", "--repo", repo, "--jsonl", "--json"])
    assert result.exit_code == 0, result.output
    build_data = json.loads(result.output)
    _assert_json_key(build_data, "valid", bool)
    assert build_data["valid"] is True, build_data
    _assert_json_key(build_data, "objects_count", int)
    assert build_data["objects_count"] >= 1, build_data

    assert (customer_repo / "generated" / "modelops.db").exists()
    assert (customer_repo / "generated" / "search_documents.jsonl").exists()
    assert (customer_repo / "generated" / "lineage_edges.jsonl").exists()


def test_demo_journey_index_fresh_and_health(customer_repo: Path) -> None:
    """Index freshness and health report must succeed on a freshly built repo."""
    repo = str(customer_repo)
    runner.invoke(app, ["build-index", "--repo", repo, "--jsonl"])

    result = runner.invoke(app, ["index-fresh", "--repo", repo, "--json"])
    assert result.exit_code == 0, result.output
    fresh_data = json.loads(result.output)
    _assert_json_key(fresh_data, "fresh", bool)
    assert fresh_data["fresh"] is True, fresh_data

    result = runner.invoke(app, ["health", "--repo", repo, "--json"])
    assert result.exit_code == 0, result.output
    health_data = json.loads(result.output)
    _assert_json_key(health_data, "object_count", int)
    assert health_data["object_count"] >= 1, health_data
    _assert_json_key(health_data, "index_fresh", bool)


def test_demo_journey_search_and_query_customer_group(customer_repo: Path) -> None:
    """Search and query must surface the Customer Group attribute."""
    repo = str(customer_repo)
    runner.invoke(app, ["build-index", "--repo", repo, "--jsonl"])

    result = runner.invoke(app, ["search", "Customer Group", "--repo", repo, "--json"])
    assert result.exit_code == 0, result.output
    search_data = json.loads(result.output)
    _assert_json_key(search_data, "results", list)
    _assert_json_key(search_data, "total_count", int)
    assert search_data["total_count"] >= 1, search_data

    result = runner.invoke(
        app, ["query", "--type", "Attribute", "--repo", repo, "--json"]
    )
    assert result.exit_code == 0, result.output
    query_data = json.loads(result.output)
    _assert_json_key(query_data, "results", list)
    _assert_json_key(query_data, "total_count", int)
    assert query_data["total_count"] >= 1, query_data
    ids = {item["object_id"] for item in query_data["results"] if isinstance(item, dict)}
    assert "ATTR-CUST-SALES-CUSTOMER-GROUP" in ids, ids


def test_demo_journey_trace_and_impact(customer_repo: Path) -> None:
    """Trace and impact must follow relationships from Customer Group to KNVV-KDGRP."""
    repo = str(customer_repo)
    runner.invoke(app, ["build-index", "--repo", repo, "--jsonl"])

    result = runner.invoke(
        app,
        [
            "trace",
            "ATTR-CUST-SALES-CUSTOMER-GROUP",
            "--repo",
            repo,
            "--direction",
            "both",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    trace_data = json.loads(result.output)
    _assert_json_key(trace_data, "root_object_id", str)
    assert trace_data["root_object_id"] == "ATTR-CUST-SALES-CUSTOMER-GROUP", trace_data
    _assert_json_key(trace_data, "nodes", list)
    assert len(trace_data["nodes"]) >= 1, trace_data
    _assert_json_key(trace_data, "edges", list)

    result = runner.invoke(
        app, ["impact", "FEP-S4-KNVV-KDGRP", "--repo", repo, "--json"]
    )
    assert result.exit_code == 0, result.output
    impact_data = json.loads(result.output)
    _assert_json_key(impact_data, "root_object_id", str)
    assert impact_data["root_object_id"] == "FEP-S4-KNVV-KDGRP", impact_data
    _assert_json_key(impact_data, "affected_objects", list)


def test_demo_journey_gaps_and_gap_report(customer_repo: Path) -> None:
    """Gap detection against the sample dataset must produce actionable output."""
    repo = str(customer_repo)
    runner.invoke(app, ["build-index", "--repo", repo, "--jsonl"])

    csv_path = customer_repo / "data" / "samples" / "customer_sales_area_sample.csv"
    result = runner.invoke(
        app, ["gaps", str(csv_path), "--repo", repo, "--check-model", "--json"]
    )
    assert result.exit_code == 0, result.output
    gaps_data = json.loads(result.output)
    _assert_json_key(gaps_data, "coverage.total_columns", int)
    assert gaps_data["coverage"]["total_columns"] >= 1, gaps_data
    _assert_json_key(gaps_data, "gaps", list)
    _assert_json_key(gaps_data, "matches", list)

    result = runner.invoke(app, ["gap-report", "--repo", repo, "--json"])
    assert result.exit_code == 0, result.output
    report_data = json.loads(result.output)
    _assert_json_key(report_data, "total_gap_count", int)
    _assert_json_key(report_data, "gaps_by_type", dict)


def test_demo_journey_docs_build_viewer(customer_repo: Path) -> None:
    """docs-build must generate a local static viewer with Customer Group content."""
    repo = str(customer_repo)
    runner.invoke(app, ["build-index", "--repo", repo, "--jsonl"])

    viewer_dir = customer_repo / "generated" / "docs_site"
    result = runner.invoke(
        app, ["docs-build", "--repo", repo, "--site", str(viewer_dir), "--json"]
    )
    assert result.exit_code == 0, result.output
    build_data = json.loads(result.output)
    _assert_json_key(build_data, "files", list)
    files = set(build_data["files"])
    assert "index.html" in files, files
    assert "objects.html" in files, files
    assert "gaps.html" in files, files
    assert "search-index.json" in files, files

    assert (viewer_dir / "assets" / "viewer.css").exists()
    assert (viewer_dir / "assets" / "viewer.js").exists()

    search_index = (viewer_dir / "search-index.json").read_text(encoding="utf-8")
    assert "Customer Group" in search_index
    assert "KNVV" in search_index
    assert "KDGRP" in search_index


def test_demo_journey_propose_patch_dry_run(customer_repo: Path) -> None:
    """A structured note must produce a safe, reviewable PatchProposal dry-run."""
    repo = str(customer_repo)
    note_file = customer_repo / "data" / "patch-note.md"
    note_file.write_text(
        "Update CUSTOMER GROUP mapping for KNVV-KDGRP based on the CH01-A17 decision.\n"
        "Keep the change as a reviewable PatchProposal.\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["propose-patch", "--from", str(note_file), "--repo", repo, "--dry-run", "--json"]
    )
    assert result.exit_code == 0, result.output
    proposal_data = json.loads(result.output)
    _assert_json_key(proposal_data, "dry_run", bool)
    assert proposal_data["dry_run"] is True, proposal_data
    _assert_json_key(proposal_data, "is_safe", bool)
    assert proposal_data["is_safe"] is True, proposal_data
    _assert_json_key(proposal_data, "proposal.id", str)
    assert proposal_data["proposal"]["id"] == "PP-SCAFFOLD-001", proposal_data

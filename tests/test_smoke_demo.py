"""Stable smoke demo with JSON contract assertions.

Runs full CLI workflow on a temp repo and asserts specific JSON keys
and types for every command. Fails if output contracts change.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


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


def test_smoke_demo_full_workflow(tmp_path: Path) -> None:
    """End-to-end smoke test with strict JSON assertions."""
    repo = tmp_path / "smoke-repo"

    # 1. init
    result = runner.invoke(app, ["init", str(repo)])
    assert result.exit_code == 0
    assert (repo / "modelops.config.yaml").exists()

    # 2. validate --json
    result = runner.invoke(app, ["validate", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    validate_data = json.loads(result.output)
    _assert_json_key(validate_data, "is_valid", bool)
    _assert_json_key(validate_data, "error_count", int)
    _assert_json_key(validate_data, "warning_count", int)
    _assert_json_key(validate_data, "info_count", int)
    _assert_json_key(validate_data, "results", list)

    # 3. build-index --jsonl
    result = runner.invoke(app, ["build-index", "--repo", str(repo), "--jsonl"])
    assert result.exit_code == 0
    assert (repo / "generated" / "modelops.db").exists()
    assert (repo / "generated" / "search_documents.jsonl").exists()
    assert (repo / "generated" / "lineage_edges.jsonl").exists()

    # 4. health --json
    result = runner.invoke(app, ["health", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    health_data = json.loads(result.output)
    _assert_json_key(health_data, "object_count", int)
    _assert_json_key(health_data, "index_fresh", bool)
    _assert_json_key(health_data, "coverage_gaps", dict)
    _assert_json_key(health_data, "ownership_coverage", dict)
    _assert_json_key(health_data, "data_quality_coverage", dict)

    # 5. scorecard --json
    result = runner.invoke(app, ["scorecard", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    scorecard_data = json.loads(result.output)
    _assert_json_key(scorecard_data, "repo_name", str)
    _assert_json_key(scorecard_data, "readiness_level", str)
    _assert_json_key(scorecard_data, "object_count", int)
    _assert_json_key(scorecard_data, "metrics", list)
    _assert_json_key(scorecard_data, "summary", str)

    # 6. analyze --json
    result = runner.invoke(app, ["analyze", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    analyze_data = json.loads(result.output)
    _assert_json_key(analyze_data, "object_count", int)
    _assert_json_key(analyze_data, "type_counts", dict)
    _assert_json_key(analyze_data, "orphan_fields", dict)
    _assert_json_key(analyze_data, "attribute_coverage", dict)
    _assert_json_key(analyze_data, "lifecycle_summary", dict)

    # 7. trace --json
    result = runner.invoke(
        app, ["trace", "DOMAIN-EXAMPLE", "--repo", str(repo), "--json"]
    )
    assert result.exit_code == 0
    trace_data = json.loads(result.output)
    _assert_json_key(trace_data, "root_object_id", str)
    _assert_json_key(trace_data, "root_object_type", str)
    _assert_json_key(trace_data, "nodes", list)
    _assert_json_key(trace_data, "edges", list)

    # 8. impact --json
    result = runner.invoke(
        app, ["impact", "DOMAIN-EXAMPLE", "--repo", str(repo), "--json"]
    )
    assert result.exit_code == 0
    impact_data = json.loads(result.output)
    _assert_json_key(impact_data, "root_object_id", str)
    _assert_json_key(impact_data, "affected_objects", list)

    # 9. audit-log --json
    result = runner.invoke(app, ["audit-log", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    audit_data = json.loads(result.output)
    assert isinstance(audit_data, list)

    # 10. clean --dry-run --json
    result = runner.invoke(
        app, ["clean", "--repo", str(repo), "--dry-run", "--json"]
    )
    assert result.exit_code == 0
    clean_data = json.loads(result.output)
    _assert_json_key(clean_data, "dry_run", bool)
    _assert_json_key(clean_data, "generated_path", str)
    _assert_json_key(clean_data, "skipped_count", int)


def test_smoke_demo_build_index_dry_run_no_db(tmp_path: Path) -> None:
    """build-index --dry-run must not create a database."""
    repo = tmp_path / "dry-repo"
    runner.invoke(app, ["init", str(repo)])
    db_path = repo / "generated" / "modelops.db"

    result = runner.invoke(
        app, ["build-index", "--repo", str(repo), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Dry-run" in result.output
    assert not db_path.exists()


def test_smoke_simple_product_model(tmp_path: Path) -> None:
    """End-to-end smoke test using the generic simple product example."""
    src = Path(__file__).parent.parent / "examples" / "simple_product_model"
    repo = tmp_path / "simple-product"
    import shutil

    shutil.copytree(src, repo)
    # Remove any pre-built generated artifacts to ensure clean build
    gen_dir = repo / "generated"
    if gen_dir.exists():
        shutil.rmtree(gen_dir)

    # 1. validate --json
    result = runner.invoke(app, ["validate", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    validate_data = json.loads(result.output)
    _assert_json_key(validate_data, "is_valid", bool)
    _assert_json_key(validate_data, "error_count", int)
    _assert_json_key(validate_data, "warning_count", int)

    # 2. build-index --jsonl
    result = runner.invoke(app, ["build-index", "--repo", str(repo), "--jsonl"])
    assert result.exit_code == 0
    assert (repo / "generated" / "modelops.db").exists()
    assert (repo / "generated" / "search_documents.jsonl").exists()
    assert (repo / "generated" / "lineage_edges.jsonl").exists()

    # 3. health --json
    result = runner.invoke(app, ["health", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    health_data = json.loads(result.output)
    _assert_json_key(health_data, "object_count", int)
    _assert_json_key(health_data, "index_fresh", bool)

    # 4. search --json
    result = runner.invoke(
        app, ["search", "product", "--repo", str(repo), "--json"]
    )
    assert result.exit_code == 0
    search_data = json.loads(result.output)
    _assert_json_key(search_data, "results", list)
    _assert_json_key(search_data, "total_count", int)
    assert search_data["total_count"] > 0

    # 5. query --json
    result = runner.invoke(
        app, ["query", "--repo", str(repo), "--type", "Attribute", "--json"]
    )
    assert result.exit_code == 0
    query_data = json.loads(result.output)
    _assert_json_key(query_data, "results", list)
    _assert_json_key(query_data, "total_count", int)
    assert query_data["total_count"] > 0

    # 6. trace --json
    result = runner.invoke(
        app, ["trace", "DOMAIN-PRODUCT", "--repo", str(repo), "--json"]
    )
    assert result.exit_code == 0
    trace_data = json.loads(result.output)
    _assert_json_key(trace_data, "root_object_id", str)
    _assert_json_key(trace_data, "nodes", list)
    _assert_json_key(trace_data, "edges", list)

    # 7. impact --json
    result = runner.invoke(
        app, ["impact", "DOMAIN-PRODUCT", "--repo", str(repo), "--json"]
    )
    assert result.exit_code == 0
    impact_data = json.loads(result.output)
    _assert_json_key(impact_data, "root_object_id", str)
    _assert_json_key(impact_data, "affected_objects", list)

    # 8. profile-dataset --json
    csv_path = repo / "data" / "samples" / "product_sample.csv"
    result = runner.invoke(
        app, ["profile-dataset", str(csv_path), "--repo", str(repo), "--json"]
    )
    assert result.exit_code == 0
    profile_data = json.loads(result.output)
    _assert_json_key(profile_data, "dataset_id", str)
    _assert_json_key(profile_data, "row_count", int)
    _assert_json_key(profile_data, "column_count", int)

    # 9. export --json
    result = runner.invoke(
        app, ["export-model", "--repo", str(repo), "--format", "csv"]
    )
    assert result.exit_code == 0
    assert "Exported" in result.output

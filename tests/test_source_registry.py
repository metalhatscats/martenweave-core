"""Tests for source registry service and CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.reports.source_registry_service import (
    SourceRegistryService,
    register_dataset_source,
    register_import_source,
)
from modelops_core.schemas.source_registry import SourceEntry

runner = CliRunner()


def test_register_and_read_entries(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    entry = SourceEntry(
        source_id="SRC-001",
        source_type="dataset_profile",
        file_path="/tmp/data.csv",
        file_hash="abc123",
        registered_at="2026-01-01T00:00:00Z",
    )
    service.register(entry)

    entries = service.read_entries()
    assert len(entries) == 1
    assert entries[0].source_id == "SRC-001"
    assert entries[0].file_hash == "abc123"


def test_list_sources_deduplicates_latest(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    service.register(
        SourceEntry(
            source_id="SRC-001",
            source_type="dataset_profile",
            registered_at="2026-01-01T00:00:00Z",
        )
    )
    service.register(
        SourceEntry(
            source_id="SRC-001",
            source_type="model_sheet_import",
            registered_at="2026-01-02T00:00:00Z",
        )
    )

    sources = service.list_sources()
    assert len(sources) == 1
    assert sources[0]["source_type"] == "model_sheet_import"


def test_get_latest_by_id(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    service.register(
        SourceEntry(
            source_id="SRC-001",
            source_type="dataset_profile",
            registered_at="2026-01-01T00:00:00Z",
            status="old",
        )
    )
    service.register(
        SourceEntry(
            source_id="SRC-001",
            source_type="dataset_profile",
            registered_at="2026-01-02T00:00:00Z",
            status="current",
        )
    )

    latest = service.get_latest_by_id("SRC-001")
    assert latest is not None
    assert latest.status == "current"


def test_get_latest_by_id_missing(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    assert service.get_latest_by_id("MISSING") is None


def test_register_dataset_source_helper(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    sid = register_dataset_source(
        service,
        dataset_id="DS-001",
        file_path=Path("/tmp/data.csv"),
        file_hash="hash123",
        row_count=100,
        column_count=5,
    )
    assert sid == "DS-001"
    latest = service.get_latest_by_id("DS-001")
    assert latest is not None
    assert latest.source_type == "dataset_profile"
    assert latest.metadata["row_count"] == 100


def test_register_import_source_helper(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    sid = register_import_source(
        service,
        proposal_id="PP-001",
        source_path=Path("/tmp/model.xlsx"),
        operations_count=3,
        warnings_count=1,
    )
    assert sid == "PP-001"
    latest = service.get_latest_by_id("PP-001")
    assert latest is not None
    assert latest.source_type == "model_sheet_import"
    assert latest.status == "warning"


def test_source_entry_roundtrip() -> None:
    entry = SourceEntry(
        source_id="SRC-001",
        source_type="test",
        display_name="Test Source",
        file_path="/tmp/test.csv",
        file_hash="abc",
        registered_at="2026-01-01T00:00:00Z",
        last_seen_at="2026-01-02T00:00:00Z",
        status="ok",
        metadata={"key": "value"},
    )
    data = entry.to_dict()
    restored = SourceEntry.from_dict(data)
    assert restored.source_id == entry.source_id
    assert restored.metadata == entry.metadata


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_sources_list_empty(tmp_path: Path) -> None:
    result = runner.invoke(app, ["sources", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "No sources registered" in result.output


def test_cli_sources_list_with_entries(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    register_dataset_source(
        service,
        dataset_id="DS-001",
        file_path=Path("/tmp/data.csv"),
        file_hash="hash",
        row_count=10,
        column_count=2,
    )
    result = runner.invoke(app, ["sources", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "DS-001" in result.output


def test_cli_sources_list_json(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    register_dataset_source(
        service,
        dataset_id="DS-001",
        file_path=Path("/tmp/data.csv"),
        file_hash="hash",
        row_count=10,
        column_count=2,
    )
    result = runner.invoke(app, ["sources", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["source_id"] == "DS-001"


def test_cli_source_show(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    register_dataset_source(
        service,
        dataset_id="DS-001",
        file_path=Path("/tmp/data.csv"),
        file_hash="hash",
        row_count=10,
        column_count=2,
    )
    result = runner.invoke(app, ["source-show", "DS-001", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "DS-001" in result.output
    assert "dataset_profile" in result.output


def test_cli_source_show_json(tmp_path: Path) -> None:
    service = SourceRegistryService(tmp_path)
    register_dataset_source(
        service,
        dataset_id="DS-001",
        file_path=Path("/tmp/data.csv"),
        file_hash="hash",
        row_count=10,
        column_count=2,
    )
    result = runner.invoke(
        app, ["source-show", "DS-001", "--repo", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["source_id"] == "DS-001"


def test_cli_source_show_missing(tmp_path: Path) -> None:
    result = runner.invoke(app, ["source-show", "MISSING", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "Source not found" in result.output

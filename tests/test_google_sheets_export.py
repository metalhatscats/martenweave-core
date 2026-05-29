"""Tests for Google Sheets connector and export service.

All external API calls are mocked. No live Google services are contacted.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modelops_core.connectors.adapter import ConnectorError
from modelops_core.connectors.google_sheets import GoogleSheetsConnector
from modelops_core.exports.google_sheets_export import (
    GoogleSheetsExportResult,
    export_to_google_sheets,
)
from modelops_core.schemas.source_registry import SourceEntry


def _make_mock_service() -> MagicMock:
    """Return a MagicMock that mimics the googleapiclient service shape."""
    return MagicMock()


# ---------------------------------------------------------------------------
# GoogleSheetsConnector tests
# ---------------------------------------------------------------------------


def test_connector_missing_dependency() -> None:
    """Connector raises a clear error when google-api-python-client is missing."""
    with patch(
        "modelops_core.connectors.google_sheets._check_dependencies",
        side_effect=ConnectorError(
            "missing package",
            connector_type="google_sheets",
            action="import",
        ),
    ):
        conn = GoogleSheetsConnector()
        with pytest.raises(ConnectorError) as exc_info:
            conn._get_service()
        assert exc_info.value.connector_type == "google_sheets"


def test_connector_fetch_metadata() -> None:
    """fetch_metadata returns ConnectorSourceInfo for a spreadsheet."""
    mock_service = _make_mock_service()
    mock_get = MagicMock()
    mock_get.execute.return_value = {
        "spreadsheetId": "test-id-123",
        "properties": {
            "title": "Test Spreadsheet",
            "locale": "en_US",
            "timeZone": "America/New_York",
        },
    }
    mock_service.spreadsheets().get.return_value = mock_get

    with patch("modelops_core.connectors.google_sheets._check_dependencies") as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleSheetsConnector(credentials=MagicMock())
        conn._service = mock_service

        meta = conn.fetch_metadata("test-id-123")

    assert meta.source_id == "test-id-123"
    assert meta.source_type == "google_sheet"
    assert meta.display_name == "Test Spreadsheet"
    assert "docs.google.com/spreadsheets/d/test-id-123" in meta.external_reference


def test_connector_fetch_content() -> None:
    """fetch_content returns JSON bytes of cell values."""
    mock_service = _make_mock_service()
    mock_get = MagicMock()
    mock_get.execute.return_value = {
        "values": [["header1", "header2"], ["val1", "val2"]],
    }
    mock_service.spreadsheets().values().get.return_value = mock_get

    with patch("modelops_core.connectors.google_sheets._check_dependencies") as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleSheetsConnector(credentials=MagicMock())
        conn._service = mock_service

        content = conn.fetch_content("test-id-123")

    data = json.loads(content.decode("utf-8"))
    assert data["values"][0] == ["header1", "header2"]


def test_connector_write_content() -> None:
    """write_content writes JSON-encoded sheets to a spreadsheet."""
    mock_service = _make_mock_service()
    mock_update = MagicMock()
    mock_service.spreadsheets().values().update.return_value = mock_update

    with patch("modelops_core.connectors.google_sheets._check_dependencies") as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleSheetsConnector(credentials=MagicMock())
        conn._service = mock_service

        # Patch _ensure_sheet_exists to avoid extra mock setup
        conn._ensure_sheet_exists = MagicMock()  # type: ignore[method-assign]

        payload = json.dumps(
            {
                "sheets": {
                    "Attributes": [["id", "name"], ["ATTR-1", "Name 1"]],
                },
                "metadata": {"exported_at": "2026-01-01T00:00:00Z"},
            }
        ).encode("utf-8")

        ok = conn.write_content("test-id-123", payload)
        assert ok is True


def test_connector_write_sheet_values() -> None:
    """write_sheet_values writes tabular data to a specific sheet tab."""
    mock_service = _make_mock_service()
    mock_update = MagicMock()
    mock_service.spreadsheets().values().update.return_value = mock_update

    with patch("modelops_core.connectors.google_sheets._check_dependencies") as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleSheetsConnector(credentials=MagicMock())
        conn._service = mock_service
        conn._ensure_sheet_exists = MagicMock()  # type: ignore[method-assign]

        conn.write_sheet_values(
            "test-id-123",
            "Attributes",
            [["id", "name"], ["ATTR-1", "Name 1"]],
        )

        mock_service.spreadsheets().values().update.assert_called_once()
        call_kwargs = mock_service.spreadsheets().values().update.call_args.kwargs
        assert call_kwargs["spreadsheetId"] == "test-id-123"
        assert call_kwargs["range"] == "Attributes!A1"
        assert call_kwargs["valueInputOption"] == "RAW"


def test_connector_to_source_entry() -> None:
    """to_source_entry produces a valid SourceEntry."""
    mock_service = _make_mock_service()
    mock_get = MagicMock()
    mock_get.execute.return_value = {
        "spreadsheetId": "test-id-123",
        "properties": {
            "title": "Test Spreadsheet",
            "locale": "en_US",
            "timeZone": "America/New_York",
        },
    }
    mock_service.spreadsheets().get.return_value = mock_get

    with patch("modelops_core.connectors.google_sheets._check_dependencies") as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleSheetsConnector(credentials=MagicMock())
        conn._service = mock_service

        entry = conn.to_source_entry("test-id-123")

    assert isinstance(entry, SourceEntry)
    assert entry.source_id == "test-id-123"
    assert entry.source_type == "google_sheets"
    assert entry.display_name == "Test Spreadsheet"


def test_connector_ensure_sheet_exists_creates_new() -> None:
    """_ensure_sheet_exists creates a new tab when it does not exist."""
    mock_service = _make_mock_service()
    mock_get = MagicMock()
    mock_get.execute.return_value = {
        "sheets": [{"properties": {"title": "Existing"}}],
    }
    mock_batch = MagicMock()
    mock_service.spreadsheets().get.return_value = mock_get
    mock_service.spreadsheets().batchUpdate.return_value = mock_batch

    with patch("modelops_core.connectors.google_sheets._check_dependencies") as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleSheetsConnector(credentials=MagicMock())
        conn._service = mock_service

        conn._ensure_sheet_exists("test-id-123", "NewTab")

        mock_batch.execute.assert_called_once()


def test_connector_ensure_sheet_exists_skips_existing() -> None:
    """_ensure_sheet_exists is a no-op when the tab already exists."""
    mock_service = _make_mock_service()
    mock_get = MagicMock()
    mock_get.execute.return_value = {
        "sheets": [{"properties": {"title": "Existing"}}],
    }
    mock_batch = MagicMock()
    mock_service.spreadsheets().get.return_value = mock_get
    mock_service.spreadsheets().batchUpdate.return_value = mock_batch

    with patch("modelops_core.connectors.google_sheets._check_dependencies") as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleSheetsConnector(credentials=MagicMock())
        conn._service = mock_service

        conn._ensure_sheet_exists("test-id-123", "Existing")

        mock_batch.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Export service tests
# ---------------------------------------------------------------------------


def test_export_to_google_sheets(tmp_path: Path) -> None:
    """export_to_google_sheets writes model data to Sheets and registers the source."""
    # Create a minimal model repository
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: draft\n"
        "name: Test Domain\n"
        "---\n\n"
        "# Test Domain\n"
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n\n"
        "# Test Attribute\n"
    )

    mock_connector = MagicMock()

    with patch(
        "modelops_core.exports.google_sheets_export.GoogleSheetsConnector",
        return_value=mock_connector,
    ):
        result = export_to_google_sheets(
            repo_root=tmp_path,
            spreadsheet_id="test-sheet-123",
        )

    assert isinstance(result, GoogleSheetsExportResult)
    assert result.spreadsheet_id == "test-sheet-123"
    assert "test-sheet-123" in result.spreadsheet_url
    assert "__metadata__" in result.sheet_names

    # Verify connector was called for each object type + metadata
    assert mock_connector.write_sheet_values.call_count >= 2

    # Verify source registry was written
    registry_path = tmp_path / "generated" / "source_registry.jsonl"
    assert registry_path.exists()
    lines = registry_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["source_id"] == "test-sheet-123"
    assert entry["source_type"] == "google_sheet_export"


def test_export_to_google_sheets_max_objects_limit(tmp_path: Path) -> None:
    """export_to_google_sheets respects the max_objects limit."""
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)

    for i in range(5):
        (model_dir / f"ATTR-{i}.md").write_text(
            f"---\nid: ATTR-{i}\ntype: Attribute\nstatus: draft\nname: Attribute {i}\n---\n"
        )

    from modelops_core.errors import ResourceLimitExceeded

    with pytest.raises(ResourceLimitExceeded):
        export_to_google_sheets(
            repo_root=tmp_path,
            spreadsheet_id="test-sheet-123",
            max_objects=2,
        )


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_export_sheets_command_exists() -> None:
    """The export-sheets CLI command is registered."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["export-sheets", "--help"])
    assert result.exit_code == 0
    assert "spreadsheet" in result.output.lower()


def test_cli_export_sheets_success(tmp_path: Path) -> None:
    """export-sheets CLI succeeds with mocked service."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n"
    )

    runner = CliRunner()

    with patch("modelops_core.exports.google_sheets_export.GoogleSheetsConnector") as mock_conn_cls:
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        result = runner.invoke(
            app,
            ["export-sheets", "test-sheet-123", "--repo", str(tmp_path)],
        )

    assert result.exit_code == 0
    assert "Exported to Google Sheets" in result.output
    assert "test-sheet-123" in result.output


def test_cli_export_sheets_missing_dependency(tmp_path: Path) -> None:
    """export-sheets CLI shows a clear error when dependencies are missing."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n"
    )

    runner = CliRunner()

    with patch(
        "modelops_core.exports.google_sheets_export.GoogleSheetsConnector",
        side_effect=RuntimeError("openpyxl is required"),
    ):
        result = runner.invoke(
            app,
            ["export-sheets", "test-sheet-123", "--repo", str(tmp_path)],
        )

    assert result.exit_code == 1

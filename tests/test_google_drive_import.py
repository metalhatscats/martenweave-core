"""Tests for Google Drive connector and import service.

All external API calls are mocked. No live Google services are contacted.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modelops_core.connectors.adapter import ConnectorError
from modelops_core.connectors.google_drive import GoogleDriveConnector
from modelops_core.schemas.source_registry import SourceEntry


def _make_mock_service() -> MagicMock:
    """Return a MagicMock that mimics the googleapiclient service shape."""
    return MagicMock()


# ---------------------------------------------------------------------------
# GoogleDriveConnector tests
# ---------------------------------------------------------------------------


def test_connector_missing_dependency() -> None:
    """Connector raises a clear error when google-api-python-client is missing."""
    with patch(
        "modelops_core.connectors.google_drive._check_dependencies",
        side_effect=ConnectorError(
            "missing package",
            connector_type="google_drive",
            action="import",
        ),
    ):
        conn = GoogleDriveConnector()
        with pytest.raises(ConnectorError) as exc_info:
            conn._get_service()
        assert exc_info.value.connector_type == "google_drive"


def test_connector_fetch_metadata() -> None:
    """fetch_metadata returns ConnectorSourceInfo for a Drive file."""
    mock_service = _make_mock_service()
    mock_get = MagicMock()
    mock_get.execute.return_value = {
        "id": "test-file-123",
        "name": "sales_data.csv",
        "mimeType": "text/csv",
        "size": "1024",
        "modifiedTime": "2026-05-20T10:00:00Z",
        "md5Checksum": "abc123def456",
    }
    mock_service.files().get.return_value = mock_get

    with patch(
        "modelops_core.connectors.google_drive._check_dependencies"
    ) as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleDriveConnector(credentials=MagicMock())
        conn._service = mock_service

        meta = conn.fetch_metadata("test-file-123")

    assert meta.source_id == "test-file-123"
    assert meta.source_type == "google_drive_file"
    assert meta.display_name == "sales_data.csv"
    assert meta.size_bytes == 1024
    assert meta.checksum == "abc123def456"
    assert meta.mime_type == "text/csv"


def test_connector_fetch_content() -> None:
    """fetch_content downloads a Drive file as bytes."""
    import sys

    mock_service = _make_mock_service()

    # Mock MediaIoBaseDownload and the chunk loop
    mock_downloader = MagicMock()
    mock_downloader.next_chunk.side_effect = [
        (MagicMock(), False),
        (MagicMock(), True),
    ]

    # Inject a fake googleapiclient module since it is not installed
    fake_googleapiclient = MagicMock()
    # MediaIoBaseDownload is used as a class constructor; make it return an
    # instance whose next_chunk method yields the expected sequence.
    mock_instance = MagicMock()
    mock_instance.next_chunk.side_effect = [
        (MagicMock(), False),
        (MagicMock(), True),
    ]
    fake_googleapiclient.http.MediaIoBaseDownload.return_value = mock_instance
    sys.modules["googleapiclient"] = fake_googleapiclient
    sys.modules["googleapiclient.http"] = fake_googleapiclient.http

    try:
        with patch(
            "modelops_core.connectors.google_drive._check_dependencies"
        ) as mock_check:
            mock_check.return_value = (MagicMock(), MagicMock())
            conn = GoogleDriveConnector(credentials=MagicMock())
            conn._service = mock_service

            content = conn.fetch_content("test-file-123")

        assert content == b""
        mock_service.files().get_media.assert_called_once_with(fileId="test-file-123")
    finally:
        # Clean up injected modules
        sys.modules.pop("googleapiclient.http", None)
        sys.modules.pop("googleapiclient", None)


def test_connector_write_content_not_supported() -> None:
    """write_content raises an error in read-only mode."""
    with patch(
        "modelops_core.connectors.google_drive._check_dependencies"
    ) as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleDriveConnector(credentials=MagicMock())

        with pytest.raises(ConnectorError) as exc_info:
            conn.write_content("test-file-123", b"data")
        assert exc_info.value.connector_type == "google_drive"
        assert exc_info.value.action == "write_content"


def test_connector_to_source_entry() -> None:
    """to_source_entry produces a valid SourceEntry."""
    mock_service = _make_mock_service()
    mock_get = MagicMock()
    mock_get.execute.return_value = {
        "id": "test-file-123",
        "name": "sales_data.csv",
        "mimeType": "text/csv",
        "size": "1024",
        "modifiedTime": "2026-05-20T10:00:00Z",
        "md5Checksum": "abc123def456",
    }
    mock_service.files().get.return_value = mock_get

    with patch(
        "modelops_core.connectors.google_drive._check_dependencies"
    ) as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleDriveConnector(credentials=MagicMock())
        conn._service = mock_service

        entry = conn.to_source_entry("test-file-123")

    assert isinstance(entry, SourceEntry)
    assert entry.source_id == "test-file-123"
    assert entry.source_type == "google_drive"
    assert entry.display_name == "sales_data.csv"
    assert entry.file_hash == "abc123def456"


def test_connector_list_sources() -> None:
    """list_sources returns files from Drive."""
    mock_service = _make_mock_service()
    mock_list = MagicMock()
    mock_list.execute.return_value = {
        "files": [
            {
                "id": "file-1",
                "name": "data.csv",
                "mimeType": "text/csv",
                "size": "512",
                "modifiedTime": "2026-05-20T10:00:00Z",
            },
            {
                "id": "file-2",
                "name": "report.xlsx",
                "mimeType": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                "size": "2048",
                "modifiedTime": "2026-05-21T12:00:00Z",
            },
        ]
    }
    mock_service.files().list.return_value = mock_list

    with patch(
        "modelops_core.connectors.google_drive._check_dependencies"
    ) as mock_check:
        mock_check.return_value = (MagicMock(), MagicMock())
        conn = GoogleDriveConnector(credentials=MagicMock())
        conn._service = mock_service

        sources = conn.list_sources(prefix="data")

    assert len(sources) == 2
    assert sources[0].source_id == "file-1"
    assert sources[1].source_id == "file-2"
    mock_service.files().list.assert_called_once()
    call_kwargs = mock_service.files().list.call_args.kwargs
    assert "data" in call_kwargs["q"]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_import_drive_command_exists() -> None:
    """The import-drive CLI command is registered."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["import-drive", "--help"])
    assert result.exit_code == 0
    assert "google drive" in result.output.lower() or "drive" in result.output.lower()


def test_cli_import_drive_csv(tmp_path: Path) -> None:
    """import-drive CLI profiles a mocked CSV from Drive."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    # Create a minimal repo
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: draft\n"
        "name: Test Domain\n"
        "---\n"
    )

    runner = CliRunner()
    csv_content = b"id,name\n1,Alice\n2,Bob\n"

    mock_meta = MagicMock()
    mock_meta.display_name = "test_data.csv"
    mock_meta.mime_type = "text/csv"

    with patch(
        "modelops_core.cli.GoogleDriveConnector"
    ) as mock_conn_cls:
        mock_conn = MagicMock()
        mock_conn.fetch_metadata.return_value = mock_meta
        mock_conn.fetch_content.return_value = csv_content
        mock_conn.to_source_entry.return_value = SourceEntry(
            source_id="drive_file_123",
            source_type="google_drive",
            display_name="test_data.csv",
        )
        mock_conn_cls.return_value = mock_conn

        result = runner.invoke(
            app,
            ["import-drive", "drive_file_123", "--repo", str(tmp_path)],
        )

    assert result.exit_code == 0
    assert "Profile saved" in result.output

    # Verify source registry was written
    registry_path = tmp_path / "generated" / "source_registry.jsonl"
    assert registry_path.exists()
    lines = registry_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["source_type"] == "google_drive"


def test_cli_import_drive_xlsx(tmp_path: Path) -> None:
    """import-drive CLI profiles a mocked XLSX from Drive."""
    from typer.testing import CliRunner

    from modelops_core.cli import app
    from modelops_core.imports.dataset_profiler import (
        DatasetProfile,
        ProfilingStatus,
        WorkbookProfile,
    )

    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: draft\n"
        "name: Test Domain\n"
        "---\n"
    )

    runner = CliRunner()

    xlsx_content = b"PK\x03\x04fake_xlsx"

    mock_meta = MagicMock()
    mock_meta.display_name = "test_data.xlsx"
    mock_meta.mime_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    wb_profile = WorkbookProfile(
        dataset_id="drive_test_data",
        file_path=str(tmp_path / "test.xlsx"),
        file_hash="abc",
        sheet_names=["Sheet1"],
        sheets=[
            DatasetProfile(
                dataset_id="drive_test_data",
                file_path=str(tmp_path / "test.xlsx"),
                file_hash="abc",
                row_count=10,
                column_count=3,
                sheet_name="Sheet1",
                status=ProfilingStatus(success=True, sampled=False),
            )
        ],
        status=ProfilingStatus(success=True, sampled=False),
    )

    with patch(
        "modelops_core.cli.GoogleDriveConnector"
    ) as mock_conn_cls:
        mock_conn = MagicMock()
        mock_conn.fetch_metadata.return_value = mock_meta
        mock_conn.fetch_content.return_value = xlsx_content
        mock_conn.to_source_entry.return_value = SourceEntry(
            source_id="drive_file_456",
            source_type="google_drive",
            display_name="test_data.xlsx",
        )
        mock_conn_cls.return_value = mock_conn

        with patch("modelops_core.cli.profile_xlsx", return_value=wb_profile):
            result = runner.invoke(
                app,
                ["import-drive", "drive_file_456", "--repo", str(tmp_path)],
            )

    assert result.exit_code == 0
    assert "Profile saved" in result.output


def test_cli_import_drive_missing_dependency(tmp_path: Path) -> None:
    """import-drive CLI shows a clear error when dependencies are missing."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: draft\n"
        "name: Test Domain\n"
        "---\n"
    )

    runner = CliRunner()

    with patch(
        "modelops_core.cli.GoogleDriveConnector",
        side_effect=RuntimeError("google-api-python-client is required"),
    ):
        result = runner.invoke(
            app,
            ["import-drive", "drive_file_123", "--repo", str(tmp_path)],
        )

    assert result.exit_code == 1

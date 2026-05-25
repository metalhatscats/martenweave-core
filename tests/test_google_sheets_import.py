"""Tests for Google Sheets import service.

All external API calls are mocked. No live Google services are contacted.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from modelops_core.imports.google_sheets_import_service import (
    _read_google_sheet,
    import_google_sheet_as_proposal,
)

# ---------------------------------------------------------------------------
# _read_google_sheet tests
# ---------------------------------------------------------------------------


def test_read_google_sheet_skips_metadata_tabs() -> None:
    """__metadata__ and similar tabs are skipped."""
    mock_connector = MagicMock()
    mock_connector.fetch_metadata.return_value = MagicMock(
        metadata={"sheets": ["Attributes", "__metadata__", "FieldEndpoints"]}
    )
    mock_connector.read_sheet_values.side_effect = [
        [
            ["id", "name", "status"],
            ["ATTR-1", "Name 1", "draft"],
        ],
        [
            ["id", "name", "status"],
            ["FEP-1", "Field 1", "draft"],
        ],
    ]

    rows_by_type = _read_google_sheet(mock_connector, "test-sheet-123")

    assert "Attributes" in rows_by_type
    assert "FieldEndpoints" in rows_by_type
    assert "__metadata__" not in rows_by_type
    assert rows_by_type["Attributes"][0]["id"] == "ATTR-1"


def test_read_google_sheet_empty_sheet_skipped() -> None:
    """Empty or header-only sheets are skipped."""
    mock_connector = MagicMock()
    mock_connector.fetch_metadata.return_value = MagicMock(
        metadata={"sheets": ["EmptySheet", "DataSheet"]}
    )
    mock_connector.read_sheet_values.side_effect = [
        [["id", "name"]],  # Header only
        [["id", "name"], ["DATA-1", "Data"]],  # Has data
    ]

    rows_by_type = _read_google_sheet(mock_connector, "test-sheet-123")

    assert "EmptySheet" not in rows_by_type
    assert "DataSheet" in rows_by_type


def test_read_google_sheet_fallback_sheet_names() -> None:
    """When metadata has no sheets list, fetch from API."""
    mock_connector = MagicMock()
    mock_connector.fetch_metadata.return_value = MagicMock(metadata={})

    mock_service = MagicMock()
    mock_service.spreadsheets().get().execute.return_value = {
        "sheets": [
            {"properties": {"title": "Attributes"}},
            {"properties": {"title": "__metadata__"}},
        ]
    }
    mock_connector._get_service.return_value = mock_service
    mock_connector.read_sheet_values.return_value = [
        ["id", "name"],
        ["ATTR-1", "Name 1"],
    ]

    rows_by_type = _read_google_sheet(mock_connector, "test-sheet-123")

    assert "Attributes" in rows_by_type
    assert "__metadata__" not in rows_by_type


# ---------------------------------------------------------------------------
# import_google_sheet_as_proposal tests
# ---------------------------------------------------------------------------


def test_import_google_sheet_as_proposal(tmp_path: Path) -> None:
    """Import a Google Sheet and produce a PatchProposal."""
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
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Old Name\n"
        "domain: DOMAIN-TEST\n"
        "---\n"
    )

    mock_connector = MagicMock()
    mock_connector.fetch_metadata.return_value = MagicMock(
        display_name="Model Review",
        metadata={"sheets": ["Attributes"]},
    )
    mock_connector.read_sheet_values.return_value = [
        ["id", "type", "status", "name", "domain"],
        ["ATTR-TEST", "Attribute", "draft", "New Name", "DOMAIN-TEST"],
    ]

    with patch(
        "modelops_core.imports.google_sheets_import_service.GoogleSheetsConnector",
        return_value=mock_connector,
    ):
        proposal = import_google_sheet_as_proposal(
            repo_root=tmp_path,
            spreadsheet_id="test-sheet-123",
        )

    assert proposal["type"] == "PatchProposal"
    assert proposal["id"] == "PP-IMPORT-GOOGLE_SHEETS:TEST-SHEET-123"
    assert len(proposal["operations"]) == 1
    assert proposal["operations"][0]["op"] == "update_object"
    assert proposal["operations"][0]["object_id"] == "ATTR-TEST"
    assert proposal["affected_objects"] == ["ATTR-TEST"]

    # Verify source registry
    registry_path = tmp_path / "generated" / "source_registry.jsonl"
    assert registry_path.exists()
    lines = registry_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["source_type"] == "google_sheet_import"
    assert entry["source_id"] == "test-sheet-123"


def test_import_google_sheet_as_proposal_new_object(tmp_path: Path) -> None:
    """Import creates a new object when ID does not exist."""
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

    mock_connector = MagicMock()
    mock_connector.fetch_metadata.return_value = MagicMock(
        display_name="Model Review",
        metadata={"sheets": ["Attributes"]},
    )
    mock_connector.read_sheet_values.return_value = [
        ["id", "type", "status", "name", "domain"],
        ["ATTR-NEW", "Attribute", "draft", "New Attribute", "DOMAIN-TEST"],
    ]

    with patch(
        "modelops_core.imports.google_sheets_import_service.GoogleSheetsConnector",
        return_value=mock_connector,
    ):
        proposal = import_google_sheet_as_proposal(
            repo_root=tmp_path,
            spreadsheet_id="test-sheet-123",
        )

    assert len(proposal["operations"]) == 1
    assert proposal["operations"][0]["op"] == "create_object"
    assert proposal["operations"][0]["object_id"] == "ATTR-NEW"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_import_sheet_command_exists() -> None:
    """The import-sheet CLI command is registered."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["import-sheet", "--help"])
    assert result.exit_code == 0
    assert "spreadsheet" in result.output.lower()


def test_cli_import_sheet_success(tmp_path: Path) -> None:
    """import-sheet CLI succeeds with mocked service."""
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
        "modelops_core.cli.import_google_sheet_as_proposal"
    ) as mock_import:
        mock_import.return_value = {
            "id": "PP-IMPORT-TEST",
            "type": "PatchProposal",
            "operations": [
                {
                    "op": "update_object",
                    "object_id": "ATTR-1",
                    "object_type": "Attribute",
                    "target_path": "name",
                }
            ],
            "affected_objects": ["ATTR-1"],
            "warnings": [],
        }
        result = runner.invoke(
            app,
            ["import-sheet", "test-sheet-123", "--repo", str(tmp_path)],
        )

    assert result.exit_code == 0
    assert "PatchProposal: PP-IMPORT-TEST" in result.output
    assert "Operations: 1" in result.output


def test_cli_import_sheet_missing_dependency(tmp_path: Path) -> None:
    """import-sheet CLI shows a clear error when dependencies are missing."""
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
        "modelops_core.cli.import_google_sheet_as_proposal",
        side_effect=RuntimeError("google-api-python-client is required"),
    ):
        result = runner.invoke(
            app,
            ["import-sheet", "test-sheet-123", "--repo", str(tmp_path)],
        )

    assert result.exit_code == 1

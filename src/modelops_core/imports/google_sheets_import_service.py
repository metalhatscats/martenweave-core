"""Import Google Sheets as PatchProposals or dataset profiles."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.config import resolve_model_path
from modelops_core.connectors.google_sheets import GoogleSheetsConnector
from modelops_core.imports.model_sheet_import_service import (
    _build_proposal,
    _load_existing_objects,
)
from modelops_core.reports.source_registry_service import SourceRegistryService
from modelops_core.schemas.source_registry import SourceEntry


def _read_google_sheet(
    connector: GoogleSheetsConnector,
    spreadsheet_id: str,
) -> dict[str, list[dict[str, str]]]:
    """Read all tabs from a Google Sheet and convert to rows_by_type format.

    Skips the __metadata__ tab. Each other tab is treated as an object type.
    """
    meta = connector.fetch_metadata(spreadsheet_id)
    sheet_titles = []
    if meta.metadata and "sheets" in meta.metadata:
        sheet_titles = meta.metadata["sheets"]
    else:
        # Fallback: read the spreadsheet to get sheet names
        service = connector._get_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_titles = [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]

    rows_by_type: dict[str, list[dict[str, str]]] = {}
    for title in sheet_titles:
        if title.startswith("__") and title.endswith("__"):
            continue  # Skip metadata tabs

        values = connector.read_sheet_values(spreadsheet_id, title)
        if not values or len(values) < 2:
            continue  # Empty or header-only sheet

        headers = [str(h) if h is not None else "" for h in values[0]]
        rows: list[dict[str, str]] = []
        for row in values[1:]:
            row_dict = {
                h: str(v) if v is not None else "" for h, v in zip(headers, row, strict=False)
            }
            if row_dict.get("id"):
                rows.append(row_dict)

        obj_type = title.replace("_", " ")
        rows_by_type[obj_type] = rows

    return rows_by_type


def import_google_sheet_as_proposal(
    repo_root: Path,
    spreadsheet_id: str,
    credentials: Any | None = None,
) -> dict[str, Any]:
    """Import a Google Sheet as a PatchProposal.

    Reads all non-metadata tabs from the spreadsheet, compares against
    existing canonical objects, and generates a PatchProposal.

    Args:
        repo_root: Path to the model repository root.
        spreadsheet_id: The Google Sheets spreadsheet ID.
        credentials: Optional Google credentials object.

    Returns:
        A PatchProposal dict capturing detected changes.
    """
    model_path = resolve_model_path(repo_root)
    connector = GoogleSheetsConnector(credentials=credentials)

    rows_by_type = _read_google_sheet(connector, spreadsheet_id)
    existing = _load_existing_objects(model_path)

    proposal = _build_proposal(
        rows_by_type,
        existing,
        source=f"google_sheets:{spreadsheet_id}",
    )

    # Register source
    registry = SourceRegistryService(repo_root)
    meta = connector.fetch_metadata(spreadsheet_id)
    registry.register(
        SourceEntry(
            source_id=spreadsheet_id,
            source_type="google_sheet_import",
            display_name=f"Sheet import: {meta.display_name or spreadsheet_id}",
            file_path=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
            registered_at=datetime.now(UTC).isoformat(),
            last_seen_at=datetime.now(UTC).isoformat(),
            status="ok",
            metadata={
                "sheet_count": len(rows_by_type),
                "object_types": list(rows_by_type.keys()),
                "proposal_id": proposal.get("id"),
                "operations_count": len(proposal.get("operations", [])),
            },
        )
    )

    return proposal

"""Export canonical model objects to Google Sheets."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.config import resolve_model_path
from modelops_core.connectors.google_sheets import GoogleSheetsConnector
from modelops_core.exports.export_service import (
    _build_columns,
    _collect_objects,
    _flatten_value,
)
from modelops_core.reports.source_registry_service import SourceRegistryService


class GoogleSheetsExportResult:
    """Result of a Google Sheets export operation."""

    def __init__(
        self,
        spreadsheet_id: str,
        spreadsheet_url: str,
        sheet_names: list[str],
        object_counts: dict[str, int],
        metadata: dict[str, Any],
    ) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet_url = spreadsheet_url
        self.sheet_names = sheet_names
        self.object_counts = object_counts
        self.metadata = metadata


def export_to_google_sheets(
    repo_root: Path,
    spreadsheet_id: str,
    credentials: Any | None = None,
    max_objects: int | None = None,
) -> GoogleSheetsExportResult:
    """Export canonical model objects to a Google Sheet.

    Each object type becomes its own sheet tab. A ``__metadata__`` tab
    is added with export timestamp and a warning that the Sheet is a
    generated review view, not canonical truth.

    Args:
        repo_root: Path to the model repository root.
        spreadsheet_id: The Google Sheets spreadsheet ID.
        credentials: Optional Google credentials object.
        max_objects: Maximum objects per sheet. If exceeded, raises
            ``ResourceLimitExceeded``.

    Returns:
        ``GoogleSheetsExportResult`` with sheet names and object counts.
    """
    model_path = resolve_model_path(repo_root)
    objects_by_type = _collect_objects(model_path)

    if max_objects is not None:
        from modelops_core.errors import ResourceLimitExceeded

        for obj_type, objects in objects_by_type.items():
            if len(objects) > max_objects:
                raise ResourceLimitExceeded(
                    resource="max_export_objects",
                    message=(
                        f"Type '{obj_type}' has {len(objects)} objects, "
                        f"exceeding max_export_objects limit of {max_objects}."
                    ),
                )

    connector = GoogleSheetsConnector(credentials=credentials)
    sheet_names: list[str] = []
    object_counts: dict[str, int] = {}

    # Write one tab per object type
    for obj_type, objects in objects_by_type.items():
        safe_name = obj_type.replace(" ", "_")[:100]  # Google Sheets tab name limit
        columns = _build_columns(objects)

        values: list[list[Any]] = [columns]
        for obj in objects:
            row = [_flatten_value(obj.get(col)) for col in columns]
            values.append(row)

        connector.write_sheet_values(spreadsheet_id, safe_name, values)
        sheet_names.append(safe_name)
        object_counts[safe_name] = len(objects)

    # Write __metadata__ tab
    metadata_values = [
        ["Key", "Value"],
        ["martenweave-export", "true"],
        ["generated_at", datetime.now(UTC).isoformat()],
        ["repository", str(repo_root.resolve())],
        ["warning", "This is a generated review view. Do not treat as canonical model truth."],
        ["sheet_count", str(len(sheet_names))],
        ["total_objects", str(sum(object_counts.values()))],
    ]
    connector.write_sheet_values(spreadsheet_id, "__metadata__", metadata_values)
    sheet_names.append("__metadata__")

    # Register in source registry
    from modelops_core.schemas.source_registry import SourceEntry

    registry = SourceRegistryService(repo_root)
    registry.register(
        SourceEntry(
            source_id=spreadsheet_id,
            source_type="google_sheet_export",
            display_name=f"Model Export {datetime.now(UTC).strftime('%Y-%m-%d')}",
            file_path=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
            registered_at=datetime.now(UTC).isoformat(),
            last_seen_at=datetime.now(UTC).isoformat(),
            status="ok",
            metadata={
                "sheet_names": sheet_names,
                "object_counts": object_counts,
                "exported_at": datetime.now(UTC).isoformat(),
            },
        )
    )

    return GoogleSheetsExportResult(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_url=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
        sheet_names=sheet_names,
        object_counts=object_counts,
        metadata={
            "sheet_count": len(sheet_names),
            "total_objects": sum(object_counts.values()),
            "generated_at": datetime.now(UTC).isoformat(),
        },
    )

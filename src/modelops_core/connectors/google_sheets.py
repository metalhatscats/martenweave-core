"""Google Sheets connector adapter.

This module requires ``google-api-python-client`` and ``google-auth``.
Install them with::

    pip install modelops_core[google]

or::

    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from modelops_core.connectors.adapter import (
    ConnectorError,
    ConnectorSourceInfo,
)
from modelops_core.schemas.source_registry import SourceEntry


@dataclass
class SheetTabInfo:
    """Metadata about a single tab in a Google Sheet."""

    title: str
    sheet_id: int
    row_count: int
    column_count: int


def _check_dependencies() -> Any:
    """Import Google API libraries or raise a clear error."""
    try:
        from googleapiclient.discovery import build  # type: ignore[import-untyped]
        from googleapiclient.errors import HttpError  # type: ignore[import-untyped]

        return build, HttpError
    except ImportError as exc:
        raise ConnectorError(
            "Google Sheets integration requires 'google-api-python-client'. "
            "Install with: pip install modelops_core[google]",
            connector_type="google_sheets",
            action="import",
            details={"missing_package": "google-api-python-client"},
        ) from exc


class GoogleSheetsConnector:
    """Connector adapter for Google Sheets.

    ``source_id`` is the spreadsheet ID (the long string in the Sheet URL).
    """

    def __init__(self, credentials: Any | None = None) -> None:
        self.credentials = credentials
        self._service: Any | None = None

    @property
    def connector_type(self) -> str:
        return "google_sheets"

    def _get_service(self) -> Any:
        """Return a cached Sheets API service object."""
        if self._service is not None:
            return self._service

        build, _HttpError = _check_dependencies()  # noqa: F841
        if self.credentials is None:
            # Attempt to load from environment / default credentials
            try:
                from google.auth import default  # type: ignore[import-untyped]

                creds, _ = default(scopes=["https://www.googleapis.com/auth/spreadsheets"])
                self.credentials = creds
            except Exception as exc:
                raise ConnectorError(
                    "No Google credentials provided and default authentication failed. "
                    "Set GOOGLE_APPLICATION_CREDENTIALS or pass credentials explicitly.",
                    connector_type=self.connector_type,
                    action="authenticate",
                ) from exc

        self._service = build("sheets", "v4", credentials=self.credentials, cache_discovery=False)
        return self._service

    # ------------------------------------------------------------------
    # ConnectorAdapter protocol methods
    # ------------------------------------------------------------------

    def list_sources(self, prefix: str = "") -> list[ConnectorSourceInfo]:
        """List Google Sheets accessible to the user.

        This is a best-effort listing via Drive API if available;
        otherwise returns an empty list.
        """
        # Drive listing requires a separate scope; skip for Sheets-only connector.
        return []

    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo:
        """Fetch spreadsheet metadata (title, locale, sheet count)."""
        service = self._get_service()
        try:
            result = (
                service.spreadsheets()
                .get(spreadsheetId=source_id, fields="properties,spreadsheetId")
                .execute()
            )
        except Exception as exc:
            raise ConnectorError(
                f"Failed to fetch metadata for spreadsheet {source_id}: {exc}",
                connector_type=self.connector_type,
                action="fetch_metadata",
                details={"spreadsheet_id": source_id},
            ) from exc

        props = result.get("properties", {})
        return ConnectorSourceInfo(
            source_id=source_id,
            source_type="google_sheet",
            display_name=props.get("title", ""),
            external_reference=f"https://docs.google.com/spreadsheets/d/{source_id}",
            modified_at=props.get("modifiedTime", ""),
            mime_type="application/vnd.google-apps.spreadsheet",
            metadata={
                "locale": props.get("locale", ""),
                "time_zone": props.get("timeZone", ""),
            },
        )

    def fetch_content(self, source_id: str) -> bytes:
        """Fetch all cell values from the first tab as JSON bytes."""
        service = self._get_service()
        try:
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=source_id, range="Sheet1")
                .execute()
            )
        except Exception as exc:
            raise ConnectorError(
                f"Failed to fetch content for spreadsheet {source_id}: {exc}",
                connector_type=self.connector_type,
                action="fetch_content",
                details={"spreadsheet_id": source_id},
            ) from exc

        values = result.get("values", [])
        return json.dumps({"values": values}).encode("utf-8")

    def write_content(self, source_id: str, content: bytes) -> bool:
        """Write JSON-encoded tabular data to a spreadsheet.

        Expected ``content`` format::

            {
                "sheets": {
                    "TabName": [
                        ["header1", "header2"],
                        ["value1", "value2"]
                    ]
                },
                "metadata": {"key": "value"}
            }

        Returns:
            True if all writes succeeded.
        """
        payload = json.loads(content.decode("utf-8"))
        sheets = payload.get("sheets", {})
        meta = payload.get("metadata", {})

        for sheet_name, values in sheets.items():
            self.write_sheet_values(source_id, sheet_name, values)

        if meta:
            meta_values = [[k, str(v)] for k, v in meta.items()]
            self.write_sheet_values(source_id, "__metadata__", meta_values)

        return True

    def to_source_entry(self, source_id: str) -> SourceEntry:
        """Produce a SourceEntry for the source registry."""
        meta = self.fetch_metadata(source_id)
        return SourceEntry(
            source_id=source_id,
            source_type=self.connector_type,
            display_name=meta.display_name,
            file_path=meta.external_reference,
            registered_at=datetime.now(UTC).isoformat(),
            last_seen_at=datetime.now(UTC).isoformat(),
            status="ok",
            metadata={
                "mime_type": meta.mime_type,
                "locale": meta.metadata.get("locale") if meta.metadata else None,
            },
        )

    # ------------------------------------------------------------------
    # Sheets-specific helpers
    # ------------------------------------------------------------------

    def read_sheet_values(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> list[list[Any]]:
        """Read all cell values from a specific sheet tab.

        Returns a list of rows, where each row is a list of cell values.
        Empty cells are returned as empty strings.
        """
        service = self._get_service()
        try:
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=sheet_name)
                .execute()
            )
        except Exception as exc:
            raise ConnectorError(
                f"Failed to read sheet {sheet_name}: {exc}",
                connector_type=self.connector_type,
                action="fetch_content",
                details={"spreadsheet_id": spreadsheet_id, "sheet_name": sheet_name},
            ) from exc

        return result.get("values", [])

    def write_sheet_values(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        values: list[list[Any]],
    ) -> None:
        """Write tabular values to a specific sheet tab.

        Creates the tab if it does not exist, then writes the values
        starting at cell A1.
        """
        service = self._get_service()
        self._ensure_sheet_exists(spreadsheet_id, sheet_name)

        range_name = f"{sheet_name}!A1"
        body = {"values": values}

        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body,
            ).execute()
        except Exception as exc:
            raise ConnectorError(
                f"Failed to write to sheet {sheet_name}: {exc}",
                connector_type=self.connector_type,
                action="write_content",
                details={"spreadsheet_id": spreadsheet_id, "sheet_name": sheet_name},
            ) from exc

    def _ensure_sheet_exists(self, spreadsheet_id: str, sheet_name: str) -> None:
        """Create the sheet tab if it does not already exist."""
        service = self._get_service()
        try:
            spreadsheet = (
                service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            )
        except Exception as exc:
            raise ConnectorError(
                f"Failed to get spreadsheet {spreadsheet_id}: {exc}",
                connector_type=self.connector_type,
                action="fetch_metadata",
            ) from exc

        existing = {
            s["properties"]["title"]
            for s in spreadsheet.get("sheets", [])
        }
        if sheet_name in existing:
            return

        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [
                        {
                            "addSheet": {
                                "properties": {"title": sheet_name}
                            }
                        }
                    ]
                },
            ).execute()
        except Exception as exc:
            raise ConnectorError(
                f"Failed to create sheet {sheet_name}: {exc}",
                connector_type=self.connector_type,
                action="write_content",
                details={"spreadsheet_id": spreadsheet_id, "sheet_name": sheet_name},
            ) from exc

    def clear_sheet_range(self, spreadsheet_id: str, range_name: str) -> None:
        """Clear a range of cells in a spreadsheet."""
        service = self._get_service()
        try:
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                body={},
            ).execute()
        except Exception as exc:
            raise ConnectorError(
                f"Failed to clear range {range_name}: {exc}",
                connector_type=self.connector_type,
                action="write_content",
                details={"spreadsheet_id": spreadsheet_id, "range": range_name},
            ) from exc

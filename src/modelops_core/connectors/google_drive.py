"""Google Drive connector adapter.

This module requires ``google-api-python-client`` and ``google-auth``.
Install them with::

    pip install modelops_core[google]

or::

    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from modelops_core.connectors.adapter import (
    ConnectorError,
    ConnectorSourceInfo,
)
from modelops_core.schemas.source_registry import SourceEntry


def _check_dependencies() -> Any:
    """Import Google API libraries or raise a clear error."""
    try:
        from googleapiclient.discovery import build  # type: ignore[import-untyped]
        from googleapiclient.errors import HttpError  # type: ignore[import-untyped]

        return build, HttpError
    except ImportError as exc:
        raise ConnectorError(
            "Google Drive integration requires 'google-api-python-client'. "
            "Install with: pip install modelops_core[google]",
            connector_type="google_drive",
            action="import",
            details={"missing_package": "google-api-python-client"},
        ) from exc


class GoogleDriveConnector:
    """Connector adapter for Google Drive.

    ``source_id`` is the Drive file ID (the string in the share link).
    """

    def __init__(self, credentials: Any | None = None) -> None:
        self.credentials = credentials
        self._service: Any | None = None

    @property
    def connector_type(self) -> str:
        return "google_drive"

    def _get_service(self) -> Any:
        """Return a cached Drive API service object."""
        if self._service is not None:
            return self._service

        build, _HttpError = _check_dependencies()  # noqa: F841
        if self.credentials is None:
            try:
                from google.auth import default  # type: ignore[import-untyped]

                creds, _ = default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
                self.credentials = creds
            except Exception as exc:
                raise ConnectorError(
                    "No Google credentials provided and default authentication failed. "
                    "Set GOOGLE_APPLICATION_CREDENTIALS or pass credentials explicitly.",
                    connector_type=self.connector_type,
                    action="authenticate",
                ) from exc

        self._service = build("drive", "v3", credentials=self.credentials, cache_discovery=False)
        return self._service

    # ------------------------------------------------------------------
    # ConnectorAdapter protocol methods
    # ------------------------------------------------------------------

    def list_sources(self, prefix: str = "") -> list[ConnectorSourceInfo]:
        """List Google Drive files matching an optional query prefix.

        ``prefix`` is treated as a name-contains filter, not a path prefix,
        because Drive does not have a traditional folder hierarchy.
        """
        service = self._get_service()
        try:
            query = "trashed = false"
            if prefix:
                query += f" and name contains '{prefix}'"

            results = (
                service.files()
                .list(
                    q=query,
                    pageSize=100,
                    fields="files(id, name, mimeType, size, modifiedTime)",
                )
                .execute()
            )
        except Exception as exc:
            raise ConnectorError(
                f"Failed to list Drive files: {exc}",
                connector_type=self.connector_type,
                action="list",
                details={"prefix": prefix},
            ) from exc

        items: list[ConnectorSourceInfo] = []
        for f in results.get("files", []):
            items.append(
                ConnectorSourceInfo(
                    source_id=f["id"],
                    source_type="google_drive_file",
                    display_name=f.get("name", ""),
                    external_reference=f"https://drive.google.com/file/d/{f['id']}",
                    size_bytes=int(f["size"]) if f.get("size") else None,
                    modified_at=f.get("modifiedTime", ""),
                    mime_type=f.get("mimeType", ""),
                )
            )
        return items

    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo:
        """Fetch Drive file metadata by file ID."""
        service = self._get_service()
        try:
            result = (
                service.files()
                .get(
                    fileId=source_id,
                    fields="id, name, mimeType, size, modifiedTime, md5Checksum",
                )
                .execute()
            )
        except Exception as exc:
            raise ConnectorError(
                f"Failed to fetch metadata for Drive file {source_id}: {exc}",
                connector_type=self.connector_type,
                action="fetch_metadata",
                details={"file_id": source_id},
            ) from exc

        return ConnectorSourceInfo(
            source_id=source_id,
            source_type="google_drive_file",
            display_name=result.get("name", ""),
            external_reference=f"https://drive.google.com/file/d/{source_id}",
            size_bytes=int(result["size"]) if result.get("size") else None,
            checksum=result.get("md5Checksum"),
            modified_at=result.get("modifiedTime", ""),
            mime_type=result.get("mimeType", ""),
        )

    def fetch_content(self, source_id: str) -> bytes:
        """Download a Drive file as bytes."""
        service = self._get_service()
        try:
            from googleapiclient.http import MediaIoBaseDownload  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ConnectorError(
                "Google Drive download requires 'google-api-python-client'.",
                connector_type=self.connector_type,
                action="fetch_content",
            ) from exc

        try:
            request = service.files().get_media(fileId=source_id)
            import io

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            return fh.getvalue()
        except Exception as exc:
            raise ConnectorError(
                f"Failed to download Drive file {source_id}: {exc}",
                connector_type=self.connector_type,
                action="fetch_content",
                details={"file_id": source_id},
            ) from exc

    def write_content(self, source_id: str, content: bytes) -> bool:
        """Write content to Google Drive.

        Not supported in read-only mode. Use a write-enabled connector
        configuration if upload is required.
        """
        raise ConnectorError(
            "Google Drive write is not supported by this connector. "
            "Use GoogleDriveConnector with write scope for uploads.",
            connector_type=self.connector_type,
            action="write_content",
        )

    def to_source_entry(self, source_id: str) -> SourceEntry:
        """Produce a SourceEntry for the source registry."""
        meta = self.fetch_metadata(source_id)
        return SourceEntry(
            source_id=source_id,
            source_type=self.connector_type,
            display_name=meta.display_name,
            file_path=meta.external_reference,
            file_hash=meta.checksum,
            registered_at=datetime.now(UTC).isoformat(),
            last_seen_at=datetime.now(UTC).isoformat(),
            status="ok",
            metadata={
                "mime_type": meta.mime_type,
                "size_bytes": meta.size_bytes,
                "modified_at": meta.modified_at,
            },
        )

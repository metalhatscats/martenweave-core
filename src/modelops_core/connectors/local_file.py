"""Local file system connector adapter."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from modelops_core.connectors.adapter import (
    ConnectorError,
    ConnectorSourceInfo,
)
from modelops_core.schemas.source_registry import SourceEntry


class LocalFileConnector:
    """Connector adapter for the local file system.

    ``source_id`` is the absolute or relative file path.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path.cwd()

    @property
    def connector_type(self) -> str:
        return "local_file"

    def _resolve(self, source_id: str) -> Path:
        """Resolve a source_id to an absolute Path."""
        p = Path(source_id)
        if not p.is_absolute():
            p = self.base_path / p
        return p.resolve()

    def list_sources(self, prefix: str = "") -> list[ConnectorSourceInfo]:
        """List files under ``base_path / prefix``."""
        search_dir = self.base_path / prefix if prefix else self.base_path
        if not search_dir.exists():
            return []

        results: list[ConnectorSourceInfo] = []
        for item in search_dir.rglob("*"):
            if item.is_file():
                rel = str(item.relative_to(self.base_path))
                results.append(self.fetch_metadata(rel))
        return results

    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo:
        """Return metadata for a local file."""
        path = self._resolve(source_id)
        if not path.exists():
            raise ConnectorError(
                f"File not found: {path}",
                connector_type=self.connector_type,
                action="fetch_metadata",
                details={"source_id": source_id, "resolved_path": str(path)},
            )

        stat = path.stat()
        checksum = ""
        if path.is_file():
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()[:16]

        return ConnectorSourceInfo(
            source_id=source_id,
            source_type="local_file",
            display_name=path.name,
            external_reference=str(path),
            size_bytes=stat.st_size,
            checksum=checksum,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
            mime_type="",
        )

    def fetch_content(self, source_id: str) -> bytes:
        """Read a local file as bytes."""
        path = self._resolve(source_id)
        if not path.exists():
            raise ConnectorError(
                f"File not found: {path}",
                connector_type=self.connector_type,
                action="fetch_content",
                details={"source_id": source_id},
            )
        try:
            return path.read_bytes()
        except OSError as exc:
            raise ConnectorError(
                f"Cannot read file: {exc}",
                connector_type=self.connector_type,
                action="fetch_content",
                details={"source_id": source_id},
            ) from exc

    def write_content(self, source_id: str, content: bytes) -> bool:
        """Write bytes to a local file."""
        path = self._resolve(source_id)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            return True
        except OSError as exc:
            raise ConnectorError(
                f"Cannot write file: {exc}",
                connector_type=self.connector_type,
                action="write_content",
                details={"source_id": source_id},
            ) from exc

    def to_source_entry(self, source_id: str) -> SourceEntry:
        """Produce a SourceEntry for the registry."""
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
                "size_bytes": meta.size_bytes,
                "modified_at": meta.modified_at,
            },
        )

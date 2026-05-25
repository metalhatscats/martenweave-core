"""Connector adapter protocol and shared types for external integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from modelops_core.schemas.source_registry import SourceEntry


class ConnectorError(Exception):
    """Normalized error raised by all connector adapters.

    Attributes:
        connector_type: The adapter that raised the error.
        action: The operation that failed (e.g. "list", "fetch").
        details: Human-readable details.
    """

    def __init__(
        self,
        message: str,
        connector_type: str = "unknown",
        action: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.connector_type = connector_type
        self.action = action
        self.details = details or {}


@dataclass
class ConnectorSourceInfo:
    """Minimal metadata about a source object from a connector."""

    source_id: str
    source_type: str
    display_name: str = ""
    external_reference: str = ""
    size_bytes: int | None = None
    checksum: str | None = None
    modified_at: str = ""
    mime_type: str = ""
    metadata: dict[str, Any] | None = None


class ConnectorAdapter(Protocol):
    """Protocol for external-source connectors.

    Implementations must be provider-specific (local file, Google Drive,
    GitHub, etc.) but expose a uniform interface so core services never
    depend on provider SDKs directly.
    """

    @property
    def connector_type(self) -> str:
        """Human-readable connector type identifier."""
        ...

    def list_sources(self, prefix: str = "") -> list[ConnectorSourceInfo]:
        """List available sources matching an optional prefix or path."""
        ...

    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo:
        """Fetch metadata for a single source without reading its content."""
        ...

    def fetch_content(self, source_id: str) -> bytes:
        """Fetch the raw content of a source.

        Raises:
            ConnectorError: If the source does not exist or is unreadable.
        """
        ...

    def write_content(self, source_id: str, content: bytes) -> bool:
        """Write content to a source, if the connector supports export.

        Returns:
            True if the write succeeded.

        Raises:
            ConnectorError: If the write failed or is unsupported.
        """
        ...

    def to_source_entry(self, source_id: str) -> SourceEntry:
        """Produce a ``SourceEntry`` for the source registry."""
        ...

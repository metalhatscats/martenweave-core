"""Source registry models for tracking external inputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceEntry:
    """A single record in the source registry.

    Tracks an external input that contributed to the model, such as a
    dataset profile, imported workbook, or future connector source.
    """

    source_id: str
    source_type: str
    display_name: str = ""
    file_path: str | None = None
    file_hash: str | None = None
    registered_at: str = ""
    last_seen_at: str = ""
    status: str = "ok"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "display_name": self.display_name or self.source_id,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "registered_at": self.registered_at,
            "last_seen_at": self.last_seen_at,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceEntry:
        """Deserialize from a plain dict."""
        return cls(
            source_id=data.get("source_id", ""),
            source_type=data.get("source_type", "unknown"),
            display_name=data.get("display_name", ""),
            file_path=data.get("file_path"),
            file_hash=data.get("file_hash"),
            registered_at=data.get("registered_at", ""),
            last_seen_at=data.get("last_seen_at", ""),
            status=data.get("status", "ok"),
            metadata=data.get("metadata", {}),
        )

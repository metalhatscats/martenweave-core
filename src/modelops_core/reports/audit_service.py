"""Append-only JSONL audit event service."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AuditEvent:
    """A single audit event."""

    event_id: str
    event_type: str
    timestamp: str
    actor: str
    status: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditEventService:
    """Append-only audit logger writing newline-delimited JSON."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.log_path = repo_root / "generated" / "audit_events.jsonl"

    def emit(self, event: dict[str, Any]) -> str:
        """Append an event dict to the audit log. Returns the event ID."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, default=str) + "\n")
        return event.get("event_id", "unknown")

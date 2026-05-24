"""Append-only notification event log service."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class NotificationEvent:
    """A single notification event."""

    event_id: str
    timestamp: str
    event_type: str
    source_type: str
    source_id: str
    recipient_id: str
    recipient_role: str
    reason: str
    affected_objects: list[str] = field(default_factory=list)
    message_summary: str | None = None
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "recipient_id": self.recipient_id,
            "recipient_role": self.recipient_role,
            "reason": self.reason,
            "affected_objects": self.affected_objects,
            "message_summary": self.message_summary,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationEvent:
        return cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            source_type=data["source_type"],
            source_id=data["source_id"],
            recipient_id=data["recipient_id"],
            recipient_role=data["recipient_role"],
            reason=data["reason"],
            affected_objects=data.get("affected_objects", []),
            message_summary=data.get("message_summary"),
            status=data.get("status", "pending"),
        )


def _events_path(repo_root: Path) -> Path:
    path = repo_root / "generated" / "notification_events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def emit_notification_event(
    repo_root: Path,
    event_type: str,
    source_type: str,
    source_id: str,
    recipient_id: str,
    recipient_role: str,
    reason: str,
    affected_objects: list[str] | None = None,
    message_summary: str | None = None,
    status: str = "pending",
) -> NotificationEvent:
    """Append a notification event to the JSONL log."""
    event = NotificationEvent(
        event_id=f"NE-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}",
        timestamp=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        event_type=event_type,
        source_type=source_type,
        source_id=source_id,
        recipient_id=recipient_id,
        recipient_role=recipient_role,
        reason=reason,
        affected_objects=affected_objects or [],
        message_summary=message_summary,
        status=status,
    )
    path = _events_path(repo_root)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event.to_dict(), default=str) + "\n")
    return event


def read_notification_events(repo_root: Path) -> list[NotificationEvent]:
    """Read all notification events from the JSONL log."""
    path = _events_path(repo_root)
    if not path.exists():
        return []

    events: list[NotificationEvent] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                events.append(NotificationEvent.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue
    return events


def filter_notification_events(
    events: list[NotificationEvent],
    recipient: str | None = None,
    source_id: str | None = None,
    event_type: str | None = None,
    status: str | None = None,
) -> list[NotificationEvent]:
    """Filter notification events by criteria."""
    result = events
    if recipient:
        result = [e for e in result if e.recipient_id == recipient]
    if source_id:
        result = [e for e in result if e.source_id == source_id]
    if event_type:
        result = [e for e in result if e.event_type == event_type]
    if status:
        result = [e for e in result if e.status == status]
    return result

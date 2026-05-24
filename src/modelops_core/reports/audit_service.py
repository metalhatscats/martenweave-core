"""Append-only JSONL audit event service with querying."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
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
    command: str | None = None
    proposal_id: str | None = None
    changed_object_ids: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    validation_status: str | None = None
    source_evidence_ids: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "status": self.status,
            "command": self.command,
            "proposal_id": self.proposal_id,
            "changed_object_ids": self.changed_object_ids,
            "changed_files": self.changed_files,
            "validation_status": self.validation_status,
            "source_evidence_ids": self.source_evidence_ids,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        return cls(
            event_id=data.get("event_id", ""),
            event_type=data.get("event_type", ""),
            timestamp=data.get("timestamp", ""),
            actor=data.get("actor", ""),
            status=data.get("status", ""),
            command=data.get("command"),
            proposal_id=data.get("proposal_id"),
            changed_object_ids=list(data.get("changed_object_ids", [])),
            changed_files=list(data.get("changed_files", [])),
            validation_status=data.get("validation_status"),
            source_evidence_ids=list(data.get("source_evidence_ids", [])),
            inputs=dict(data.get("inputs", {})),
            outputs=dict(data.get("outputs", {})),
            metadata=dict(data.get("metadata", {})),
        )


class AuditEventService:
    """Append-only audit logger writing newline-delimited JSON."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.log_path = repo_root / "generated" / "audit_events.jsonl"

    def emit(self, event: AuditEvent | dict[str, Any]) -> str:
        """Append an event to the audit log. Returns the event ID."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(event, AuditEvent):
            event_dict = event.to_dict()
        else:
            event_dict = event
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event_dict, default=str) + "\n")
        return event_dict.get("event_id", "unknown")

    def read_events(self) -> list[AuditEvent]:
        """Read all audit events from the log."""
        events: list[AuditEvent] = []
        if not self.log_path.exists():
            return events
        with self.log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    events.append(AuditEvent.from_dict(data))
                except Exception:
                    continue
        return events


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_event_id() -> str:
    return f"audit-{uuid.uuid4().hex[:12]}"


def create_audit_event(
    event_type: str,
    actor: str = "system",
    status: str = "success",
    command: str | None = None,
    proposal_id: str | None = None,
    changed_object_ids: list[str] | None = None,
    changed_files: list[str] | None = None,
    validation_status: str | None = None,
    source_evidence_ids: list[str] | None = None,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_id=_generate_event_id(),
        event_type=event_type,
        timestamp=_now_iso(),
        actor=actor,
        status=status,
        command=command,
        proposal_id=proposal_id,
        changed_object_ids=changed_object_ids or [],
        changed_files=changed_files or [],
        validation_status=validation_status,
        source_evidence_ids=source_evidence_ids or [],
        inputs=inputs or {},
        outputs=outputs or {},
        metadata=metadata or {},
    )


def filter_audit_events(
    events: list[AuditEvent],
    object_id: str | None = None,
    proposal_id: str | None = None,
    event_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[AuditEvent]:
    """Filter audit events by criteria."""
    results = events
    if object_id is not None:
        results = [e for e in results if object_id in e.changed_object_ids]
    if proposal_id is not None:
        results = [e for e in results if e.proposal_id == proposal_id]
    if event_type is not None:
        results = [e for e in results if e.event_type == event_type]
    if date_from is not None:
        results = [e for e in results if e.timestamp >= date_from]
    if date_to is not None:
        results = [e for e in results if e.timestamp <= date_to]
    return results

"""Local-first application usage telemetry.

Emits privacy-safe usage events to ``generated/usage_events.jsonl``.
Telemetry failure never breaks user workflows.
"""

from __future__ import annotations

import functools
import hashlib
import json
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# Thread-safe / async-safe context variable for the active telemetry session.
_active_session: ContextVar[_TelemetrySession | None] = ContextVar("_active_session", default=None)


@dataclass
class UsageEvent:
    """A single application usage event."""

    event_id: str
    timestamp: str
    command: str
    status: str
    duration_ms: int
    repo_hash: str | None = None
    error_type: str | None = None
    object_count: int | None = None
    proposal_count: int | None = None
    source_type: str | None = None
    export_format: str | None = None
    feature_flags: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "command": self.command,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "repo_hash": self.repo_hash,
            "error_type": self.error_type,
            "object_count": self.object_count,
            "proposal_count": self.proposal_count,
            "source_type": self.source_type,
            "export_format": self.export_format,
            "feature_flags": self.feature_flags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UsageEvent:
        return cls(
            event_id=data.get("event_id", ""),
            timestamp=data.get("timestamp", ""),
            command=data.get("command", ""),
            status=data.get("status", ""),
            duration_ms=int(data.get("duration_ms", 0)),
            repo_hash=data.get("repo_hash"),
            error_type=data.get("error_type"),
            object_count=data.get("object_count"),
            proposal_count=data.get("proposal_count"),
            source_type=data.get("source_type"),
            export_format=data.get("export_format"),
            feature_flags=dict(data.get("feature_flags", {})),
            metadata=dict(data.get("metadata", {})),
        )


class TelemetryService:
    """Append-only usage telemetry logger.

    Writes newline-delimited JSON to ``generated/usage_events.jsonl``.
    All write operations are wrapped in ``try/except`` so telemetry
    failures never propagate to callers.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root
        self.log_path: Path | None = None
        if repo_root is not None:
            self.log_path = repo_root / "generated" / "usage_events.jsonl"

    def emit(self, event: UsageEvent) -> str:
        """Append an event to the log. Returns the event ID."""
        if self.log_path is None:
            return event.event_id
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict(), default=str) + "\n")
            return event.event_id
        except Exception:
            return event.event_id

    def read_events(self) -> list[UsageEvent]:
        """Read all usage events from the log."""
        events: list[UsageEvent] = []
        if self.log_path is None or not self.log_path.exists():
            return events
        try:
            with self.log_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(UsageEvent.from_dict(json.loads(line)))
                    except Exception:
                        continue
        except Exception:
            pass
        return events


def _repo_hash(repo_root: Path | None) -> str | None:
    """Anonymised repo identifier (SHA-256 truncated)."""
    if repo_root is None:
        return None
    try:
        return hashlib.sha256(str(repo_root.resolve()).encode()).hexdigest()[:16]
    except Exception:
        return None


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_event_id() -> str:
    return f"usage-{uuid.uuid4().hex[:12]}"


class _TelemetrySession:
    """Mutable session state captured during a command execution."""

    def __init__(
        self,
        command: str,
        repo_root: Path | None,
        feature_flags: dict[str, Any] | None,
    ) -> None:
        self.command = command
        self.repo_root = repo_root
        self.feature_flags = feature_flags or {}
        self.service = TelemetryService(repo_root)
        self.start_time = datetime.now(UTC)
        self.object_count: int | None = None
        self.proposal_count: int | None = None
        self.source_type: str | None = None
        self.export_format: str | None = None

    def record_object_count(self, count: int) -> None:
        self.object_count = count

    def record_proposal_count(self, count: int) -> None:
        self.proposal_count = count

    def record_source_type(self, source_type: str) -> None:
        self.source_type = source_type

    def record_export_format(self, fmt: str) -> None:
        self.export_format = fmt

    def finalize(self, status: str, error: BaseException | None = None) -> None:
        duration_ms = int((datetime.now(UTC) - self.start_time).total_seconds() * 1000)
        error_type = type(error).__name__ if error else None
        event = UsageEvent(
            event_id=_generate_event_id(),
            timestamp=_now_iso(),
            command=self.command,
            status=status,
            duration_ms=duration_ms,
            repo_hash=_repo_hash(self.repo_root),
            error_type=error_type,
            object_count=self.object_count,
            proposal_count=self.proposal_count,
            source_type=self.source_type,
            export_format=self.export_format,
            feature_flags=self.feature_flags,
        )
        self.service.emit(event)


def record_object_count(count: int) -> None:
    """Record an object count in the active telemetry session, if any."""
    session = _active_session.get()
    if session is not None:
        session.record_object_count(count)


def record_proposal_count(count: int) -> None:
    """Record a proposal count in the active telemetry session, if any."""
    session = _active_session.get()
    if session is not None:
        session.record_proposal_count(count)


def record_source_type(source_type: str) -> None:
    """Record a source type in the active telemetry session, if any."""
    session = _active_session.get()
    if session is not None:
        session.record_source_type(source_type)


def record_export_format(fmt: str) -> None:
    """Record an export format in the active telemetry session, if any."""
    session = _active_session.get()
    if session is not None:
        session.record_export_format(fmt)


def with_telemetry(
    command: str | None = None,
    repo_arg: str = "repo",
) -> Callable[[F], F]:
    """Decorator that emits a usage event after the wrapped function runs.

    Usage::

        @app.command()
        @with_telemetry("validate")
        def validate(repo: str | None = None, ...) -> None:
            files = scan_repository(model_path)
            record_object_count(len(files))
            # ... do work ...

    Telemetry failure is silently swallowed so that the primary workflow
    is never interrupted.  The decorator must be placed **above**
    ``@app.command()`` so that Typer registers the original function
    signature while the wrapper handles execution.

    Parameters
    ----------
    command:
        Override the command name stored in the event.  Defaults to the
        wrapped function's ``__name__``.
    repo_arg:
        Name of the function argument that holds the repository path.
    """

    def decorator(func: F) -> F:
        cmd_name = command or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            repo_val = kwargs.get(repo_arg)
            repo_root: Path | None = None
            if repo_val is not None:
                repo_root = Path(repo_val).resolve() if isinstance(repo_val, str) else repo_val

            session = _TelemetrySession(cmd_name, repo_root, None)
            token = _active_session.set(session)
            try:
                result = func(*args, **kwargs)
                session.finalize(status="success", error=None)
                return result
            except BaseException as exc:
                session.finalize(status="error", error=exc)
                raise
            finally:
                _active_session.reset(token)

        return wrapper  # type: ignore[return-value]

    return decorator

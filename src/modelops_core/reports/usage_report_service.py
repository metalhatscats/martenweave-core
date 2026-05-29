"""Usage report service aggregating audit events into activity summaries."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.reports.audit_service import AuditEventService


@dataclass
class UsageReport:
    """Aggregated usage report from audit events."""

    total_events: int = 0
    event_type_counts: dict[str, int] = field(default_factory=dict)
    command_counts: dict[str, int] = field(default_factory=dict)
    status_counts: dict[str, int] = field(default_factory=dict)
    ai_usage_summary: dict[str, Any] = field(default_factory=dict)
    date_range: dict[str, str | None] = field(default_factory=lambda: {"from": None, "to": None})


def generate_usage_report(repo_root: Path) -> UsageReport:
    """Generate a usage report by aggregating audit events."""
    service = AuditEventService(repo_root)
    events = service.read_events()

    report = UsageReport(total_events=len(events))

    if not events:
        report.ai_usage_summary = {
            "ai_calls": 0,
            "total_tokens": 0,
            "note": "No AI usage recorded. Enable AI provider calls to capture usage.",
        }
        return report

    report.event_type_counts = dict(Counter(e.event_type for e in events))
    report.command_counts = dict(Counter(e.command for e in events if e.command))
    report.status_counts = dict(Counter(e.status for e in events))

    timestamps = [e.timestamp for e in events if e.timestamp]
    if timestamps:
        report.date_range = {
            "from": min(timestamps),
            "to": max(timestamps),
        }

    # AI usage placeholder: inspect metadata for token counts if present
    ai_events = [e for e in events if e.metadata and "tokens" in e.metadata]
    if ai_events:
        total_tokens = sum(int(e.metadata.get("tokens", 0) or 0) for e in ai_events)
        report.ai_usage_summary = {
            "ai_calls": len(ai_events),
            "total_tokens": total_tokens,
            "note": "AI telemetry is experimental; costs not yet estimated.",
        }
    else:
        report.ai_usage_summary = {
            "ai_calls": 0,
            "total_tokens": 0,
            "note": "No AI usage recorded. Enable AI provider calls to capture usage.",
        }

    return report

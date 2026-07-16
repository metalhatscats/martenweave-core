from __future__ import annotations

import json
import sqlite3
from typing import Any

import typer
from rich.table import Table

from modelops_core import __version__
from modelops_core.commands._common import _resolve_repo, console
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.notifications import (
    filter_notification_events,
    preview_notifications,
    read_notification_events,
)
from modelops_core.reports.decisions_report import generate_decisions_report
from modelops_core.telemetry import with_telemetry

notifications_app = typer.Typer(
    name="notifications",
    help="Preview notification recipients for workflow actions.",
)
@notifications_app.command("preview")
def notifications_preview(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    change_request: str | None = typer.Option(
        None, "--change-request", help="ChangeRequest ID to preview."
    ),
    proposal: str | None = typer.Option(None, "--proposal", help="PatchProposal ID to preview."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Preview who would be notified for a ChangeRequest or PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    try:
        entries = preview_notifications(
            model_path=model_path,
            cr_id=change_request,
            proposal_id=proposal,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        result = [
            {
                "recipient_id": e.recipient_id,
                "recipient_role": e.recipient_role,
                "reason": e.reason,
                "source_object_id": e.source_object_id,
                "source_object_type": e.source_object_type,
            }
            for e in entries
        ]
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    if not entries:
        console.print("[yellow]No notification recipients found.[/yellow]")
        raise typer.Exit()

    table = Table("Recipient", "Role", "Reason", "Source Object")
    for e in entries:
        table.add_row(
            e.recipient_id,
            e.recipient_role,
            e.reason,
            f"{e.source_object_id or '—'} ({e.source_object_type or '—'})",
        )
    console.print(table)


@notifications_app.command("list")
def notifications_list(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    recipient: str | None = typer.Option(None, "--recipient", help="Filter by recipient ID."),
    source_id: str | None = typer.Option(None, "--source-id", help="Filter by source object ID."),
    event_type: str | None = typer.Option(None, "--event-type", help="Filter by event type."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List notification events from the append-only log."""
    repo_root = _resolve_repo(repo)
    events = read_notification_events(repo_root)

    filtered = filter_notification_events(
        events,
        recipient=recipient,
        source_id=source_id,
        event_type=event_type,
        status=status,
    )

    if json_output:
        print(json.dumps([e.to_dict() for e in filtered], indent=2, default=str))
        raise typer.Exit()

    if not events:
        console.print("[yellow]No notification events found.[/yellow]")
        raise typer.Exit()

    console.print(f"[bold]Notification Events ({len(filtered)})[/bold]")
    if not filtered:
        console.print("  No events match the filters.")
        raise typer.Exit()

    table = Table("Event ID", "Type", "Timestamp", "Source", "Recipient", "Role", "Status")
    for e in filtered:
        table.add_row(
            e.event_id,
            e.event_type,
            e.timestamp,
            f"{e.source_id} ({e.source_type})",
            e.recipient_id,
            e.recipient_role,
            e.status,
        )
    console.print(table)


# ---------------------------------------------------------------------------
# Decision subcommands


decisions_app = typer.Typer(
    name="decisions",
    help="Browse and inspect Decision objects.",
)
@decisions_app.command("list")
def decisions_list(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List all Decision objects in the repository."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        if json_output:
            print(json.dumps([]))
            raise typer.Exit()
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, status, name, title, domain, source_file FROM objects WHERE type = ?",
            ("Decision",),
        ).fetchall()
    finally:
        conn.close()

    decisions = []
    for row in rows:
        decisions.append(
            {
                "id": row[0],
                "status": row[1],
                "name": row[2],
                "title": row[3],
                "domain": row[4],
                "source_file": row[5],
            }
        )

    if json_output:
        print(json.dumps(decisions, indent=2, default=str))
        raise typer.Exit()

    if not decisions:
        console.print("[yellow]No Decision objects found.[/yellow]")
        raise typer.Exit()

    table = Table("ID", "Status", "Name / Title", "Domain", "Source File")
    for d in decisions:
        display_name = d["name"] or d["title"] or "—"
        table.add_row(d["id"], d["status"], display_name, d["domain"] or "—", d["source_file"])
    console.print(table)


@decisions_app.command("show")
def decisions_show(
    decision_id: str = typer.Argument(..., help="Decision ID (e.g. DEC-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show details of a single Decision object."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT id, status, name, title, domain, description, source_file, frontmatter_json "
            "FROM objects WHERE id = ? AND type = ?",
            (decision_id, "Decision"),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        console.print(f"[red]Decision not found: {decision_id}[/red]")
        raise typer.Exit(code=1)

    obj_id, status, name, title, domain, description, source_file, frontmatter_json = row
    frontmatter: dict[str, Any] = {}
    if frontmatter_json:
        try:
            frontmatter = json.loads(frontmatter_json)
        except json.JSONDecodeError:
            pass

    if json_output:
        print(json.dumps(frontmatter, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Decision: {obj_id}[/bold]")
    console.print(f"  Status: {status}")
    if name:
        console.print(f"  Name: {name}")
    if title:
        console.print(f"  Title: {title}")
    if domain:
        console.print(f"  Domain: {domain}")
    if description:
        console.print(f"  Description: {description}")
    console.print(f"  Source: {source_file}")

    attribute = frontmatter.get("attribute")
    if attribute:
        console.print(f"  Attribute: {attribute}")

    evidence = frontmatter.get("evidence")
    if evidence:
        if isinstance(evidence, list):
            console.print(f"  Evidence: {', '.join(evidence)}")
        else:
            console.print(f"  Evidence: {evidence}")

    related_decisions = frontmatter.get("related_decisions")
    if related_decisions:
        if isinstance(related_decisions, list):
            console.print(f"  Related decisions: {', '.join(related_decisions)}")
        else:
            console.print(f"  Related decisions: {related_decisions}")

    related_issue = frontmatter.get("related_issue")
    if related_issue:
        console.print(f"  Related issue: {related_issue}")


@decisions_app.command("report")
@with_telemetry("decisions-report")
def decisions_report(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show Decision evidence coverage and category breakdown."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_decisions_report(db_path, repo_root)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "evidence_coverage": [
                {
                    "domain": d.domain,
                    "total_decisions": d.total_decisions,
                    "decisions_with_evidence": d.decisions_with_evidence,
                    "coverage_percent": d.coverage_percent,
                }
                for d in report.evidence_coverage
            ],
            "uncovered_decisions": [
                {
                    "object_id": d.object_id,
                    "object_name": d.object_name,
                    "status": d.status,
                    "domain": d.domain,
                }
                for d in report.uncovered_decisions
            ],
            "deprecated_evidence_decisions": [
                {
                    "object_id": d.object_id,
                    "object_name": d.object_name,
                    "status": d.status,
                    "domain": d.domain,
                }
                for d in report.deprecated_evidence_decisions
            ],
            "category_breakdown": [
                {"category": c.category, "count": c.count} for c in report.category_breakdown
            ],
            "total_decisions": report.total_decisions,
            "total_with_evidence": report.total_with_evidence,
            "overall_coverage_percent": report.overall_coverage_percent,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Decisions Report[/bold]")
    console.print(f"  Total decisions: {report.total_decisions}")
    console.print(f"  With evidence: {report.total_with_evidence}")
    console.print(f"  Overall coverage: {report.overall_coverage_percent}%")
    console.print("")

    if report.evidence_coverage:
        table = Table("Domain", "Decisions", "With Evidence", "Coverage %")
        for d in report.evidence_coverage:
            domain_label = d.domain or "(no domain)"
            table.add_row(
                domain_label,
                str(d.total_decisions),
                str(d.decisions_with_evidence),
                f"{d.coverage_percent}%",
            )
        console.print(table)
    else:
        console.print("[yellow]No Decision objects found.[/yellow]")

    if report.uncovered_decisions:
        console.print("")
        console.print("[bold]Decisions Without Evidence[/bold]")
        ut = Table("Object ID", "Name", "Status", "Domain")
        for d in report.uncovered_decisions:
            ut.add_row(
                d.object_id,
                d.object_name or "—",
                d.status,
                d.domain or "—",
            )
        console.print(ut)

    if report.deprecated_evidence_decisions:
        console.print("")
        console.print("[bold]Decisions With Deprecated Evidence[/bold]")
        dt = Table("Object ID", "Name", "Status", "Domain")
        for d in report.deprecated_evidence_decisions:
            dt.add_row(
                d.object_id,
                d.object_name or "—",
                d.status,
                d.domain or "—",
            )
        console.print(dt)

    if report.category_breakdown:
        console.print("")
        console.print("[bold]Category Breakdown[/bold]")
        ct = Table("Category", "Count")
        for c in report.category_breakdown:
            ct.add_row(c.category or "(none)", str(c.count))
        console.print(ct)

from __future__ import annotations

import json
from typing import Any

import typer
from rich.table import Table

from modelops_core.change_request import (
    approve_change_request,
    create_change_request,
    list_change_requests,
    load_change_request,
    reject_change_request,
    update_change_request_status,
)
from modelops_core.commands._common import _resolve_repo, console
from modelops_core.config import resolve_model_path
from modelops_core.notifications import emit_notification_event, preview_notifications
from modelops_core.reports.audit_service import AuditEventService, create_audit_event
from modelops_core.telemetry import with_telemetry

cr_app = typer.Typer(
    name="change-request",
    help="Create and manage ChangeRequests.",
)


@cr_app.command("create")
@with_telemetry("cr-create")
def cr_create(
    title: str = typer.Option(..., "--title", help="ChangeRequest title."),
    cr_id: str = typer.Option(..., "--id", help="ChangeRequest ID (e.g. CR-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    status: str = typer.Option("pending", "--status", help="Initial status."),
    requester: str | None = typer.Option(None, "--requester", help="Who requested the change."),
    reason: str | None = typer.Option(None, "--reason", help="Why the change is needed."),
    requested_change: str | None = typer.Option(
        None, "--requested-change", help="Summary of what should change."
    ),
    expected_impact: str | None = typer.Option(
        None, "--expected-impact", help="Expected impact on model."
    ),
    affected_object: list[str] = typer.Option(  # noqa: B008
        [], "--affected-object", help="Object ID affected by this change."
    ),
    linked_proposal: list[str] = typer.Option(  # noqa: B008
        [], "--linked-proposal", help="Linked PatchProposal ID."
    ),
    related_issue: list[str] = typer.Option(  # noqa: B008
        [], "--related-issue", help="Linked Issue ID."
    ),
    related_decision: list[str] = typer.Option(  # noqa: B008
        [], "--related-decision", help="Linked Decision ID."
    ),
    approver: list[str] = typer.Option(  # noqa: B008
        [], "--approver", help="Required approver ID."
    ),
    priority: str | None = typer.Option(None, "--priority", help="Priority level."),
    source_evidence: str | None = typer.Option(
        None, "--source-evidence", help="Source evidence reference."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview CR without writing files."),
) -> None:
    """Create a new ChangeRequest canonical file."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    try:
        path = create_change_request(
            model_path=model_path,
            cr_id=cr_id,
            title=title,
            status=status,
            requester=requester,
            reason=reason,
            requested_change=requested_change,
            expected_impact=expected_impact,
            affected_objects=list(affected_object) if affected_object else None,
            linked_proposals=list(linked_proposal) if linked_proposal else None,
            related_issues=list(related_issue) if related_issue else None,
            related_decisions=list(related_decision) if related_decision else None,
            approvers=list(approver) if approver else None,
            priority=priority,
            source_evidence=source_evidence,
            dry_run=dry_run,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        result = {
            "id": cr_id,
            "status": status,
            "title": title,
            "path": str(path),
            "dry_run": dry_run,
        }
        print(json.dumps(result, indent=2, default=str))
    else:
        if dry_run:
            console.print("[bold]Dry-run: ChangeRequest preview[/bold]")
        else:
            console.print(f"[green]ChangeRequest created: {path}[/green]")
        console.print(f"  ID:     {cr_id}")
        console.print(f"  Status: {status}")
        console.print(f"  Title:  {title}")

    if dry_run:
        return

    # Emit notification events for affected object owners/watchers
    try:
        preview_entries = preview_notifications(
            model_path=model_path,
            cr_id=cr_id,
        )
        for entry in preview_entries:
            emit_notification_event(
                repo_root=repo_root,
                event_type="change_request_requested",
                source_type="ChangeRequest",
                source_id=cr_id,
                recipient_id=entry.recipient_id,
                recipient_role=entry.recipient_role,
                reason=entry.reason,
                affected_objects=list(affected_object) if affected_object else [],
                message_summary=f"ChangeRequest {cr_id} created: {title}",
                status="pending",
            )
    except Exception:
        pass  # Preview failures should not block CR creation


@cr_app.command("list")
def cr_list(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List all ChangeRequests in the repository."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    crs = list_change_requests(model_path)

    if json_output:
        print(json.dumps(crs, indent=2, default=str))
        raise typer.Exit()

    if not crs:
        console.print("[yellow]No ChangeRequests found.[/yellow]")
        raise typer.Exit()

    table = Table("ID", "Status", "Title", "Requester")
    for cr in crs:
        table.add_row(
            cr["id"],
            cr["status"],
            cr["title"],
            cr["requester"],
        )
    console.print(table)


@cr_app.command("show")
def cr_show(
    cr_id: str = typer.Argument(..., help="ChangeRequest ID (e.g. CR-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show details of a ChangeRequest."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    cr = load_change_request(model_path, cr_id)

    if cr is None:
        console.print(f"[red]ChangeRequest not found: {cr_id}[/red]")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(cr, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]ChangeRequest: {cr_id}[/bold]")
    console.print(f"  Status: {cr.get('status', '—')}")
    console.print(f"  Title:  {cr.get('title') or cr.get('name') or '—'}")
    console.print(f"  Requester: {cr.get('requester', '—')}")
    if cr.get("priority"):
        console.print(f"  Priority: {cr['priority']}")
    if cr.get("affected_objects"):
        console.print(f"  Affected objects: {', '.join(cr['affected_objects'])}")
    if cr.get("linked_proposals"):
        console.print(f"  Linked proposals: {', '.join(cr['linked_proposals'])}")
    if cr.get("approvers"):
        console.print(f"  Approvers: {', '.join(cr['approvers'])}")


@cr_app.command("update-status")
def cr_update_status(
    cr_id: str = typer.Argument(..., help="ChangeRequest ID (e.g. CR-001)."),
    status: str = typer.Argument(..., help="New status."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    write: bool = typer.Option(False, "--write", help="Persist the status change."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the status change."),
) -> None:
    """Update the status of a ChangeRequest."""
    if dry_run and write:
        console.print("[red]Cannot use both --dry-run and --write.[/red]")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    is_preview = not write and not dry_run
    try:
        cr = update_change_request_status(model_path, cr_id, status, dry_run=not write)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(cr, indent=2, default=str))
    else:
        if is_preview:
            console.print(
                f"[yellow]Preview only: ChangeRequest {cr_id} would be updated to "
                f"'{status}'. Use --write to persist.[/yellow]"
            )
        elif dry_run:
            console.print(
                f"[yellow]Dry-run: ChangeRequest {cr_id} would be updated to "
                f"'{status}'. No files were modified.[/yellow]"
            )
        else:
            console.print(f"[green]ChangeRequest {cr_id} updated to '{status}'[/green]")

    if not write:
        raise typer.Exit()

    service = AuditEventService(repo_root)
    service.emit(
        create_audit_event(
            event_type="change_request_status_updated",
            actor="system",
            status="success",
            command="change-request update-status",
            proposal_id=cr_id,
            changed_object_ids=cr.get("affected_objects") or [],
            outputs={"new_status": status, "previous_status": cr.get("status")},
        )
    )

    # Emit notification events for status transition
    event_type_map = {
        "approved": "change_request_approved",
        "rejected": "change_request_rejected",
        "implemented": "change_request_applied",
    }
    event_type = event_type_map.get(status)
    if event_type:
        try:
            preview_entries = preview_notifications(
                model_path=model_path,
                cr_id=cr_id,
            )
            for entry in preview_entries:
                emit_notification_event(
                    repo_root=repo_root,
                    event_type=event_type,
                    source_type="ChangeRequest",
                    source_id=cr_id,
                    recipient_id=entry.recipient_id,
                    recipient_role=entry.recipient_role,
                    reason=entry.reason,
                    affected_objects=cr.get("affected_objects") or [],
                    message_summary=f"ChangeRequest {cr_id} {status}",
                    status=status,
                )
        except Exception:
            pass


@cr_app.command("approve")
def cr_approve(
    cr_id: str = typer.Argument(..., help="ChangeRequest ID (e.g. CR-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    approver: str = typer.Option(..., "--approver", help="Approver ID."),
    skip_risk_check: bool = typer.Option(
        False, "--skip-risk-check", help="Skip high-risk ChangeRequest blocking."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    write: bool = typer.Option(False, "--write", help="Persist the approval."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the approval."),
) -> None:
    """Approve a ChangeRequest."""
    if dry_run and write:
        console.print("[red]Cannot use both --dry-run and --write.[/red]")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    is_preview = not write and not dry_run
    try:
        cr = approve_change_request(
            model_path,
            cr_id,
            approver,
            skip_risk_check=skip_risk_check,
            dry_run=not write,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(cr, indent=2, default=str))
    else:
        if is_preview:
            console.print(
                f"[yellow]Preview only: ChangeRequest {cr_id} would be approved by "
                f"{approver}. Use --write to persist.[/yellow]"
            )
        elif dry_run:
            console.print(
                f"[yellow]Dry-run: ChangeRequest {cr_id} would be approved by "
                f"{approver}. No files were modified.[/yellow]"
            )
        else:
            console.print(f"[green]ChangeRequest {cr_id} approved by {approver}[/green]")
        if cr.get("approvals"):
            console.print(f"  Approvals: {len(cr['approvals'])}")
        if cr.get("risk_level"):
            console.print(f"  Risk level: {cr['risk_level']}")

    if not write:
        raise typer.Exit()

    service = AuditEventService(repo_root)
    outputs: dict[str, Any] = {"approver": approver, "approvals": cr.get("approvals", [])}
    if cr.get("risk_level"):
        outputs["risk_level"] = cr["risk_level"]
    if cr.get("risk_reasons"):
        outputs["risk_reasons"] = cr["risk_reasons"]
    if cr.get("risk_triggering_rules"):
        outputs["risk_triggering_rules"] = cr["risk_triggering_rules"]
    service.emit(
        create_audit_event(
            event_type="change_request_approved",
            actor=approver,
            status="success",
            command="change-request approve",
            proposal_id=cr_id,
            changed_object_ids=cr.get("affected_objects") or [],
            outputs=outputs,
        )
    )

    # Emit notification events
    try:
        preview_entries = preview_notifications(
            model_path=model_path,
            cr_id=cr_id,
        )
        for entry in preview_entries:
            emit_notification_event(
                repo_root=repo_root,
                event_type="change_request_approved",
                source_type="ChangeRequest",
                source_id=cr_id,
                recipient_id=entry.recipient_id,
                recipient_role=entry.recipient_role,
                reason=entry.reason,
                affected_objects=cr.get("affected_objects") or [],
                message_summary=f"ChangeRequest {cr_id} approved by {approver}",
                status="approved",
            )
    except Exception:
        pass


@cr_app.command("reject")
def cr_reject(
    cr_id: str = typer.Argument(..., help="ChangeRequest ID (e.g. CR-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    approver: str = typer.Option(..., "--approver", help="Approver ID."),
    reason: str | None = typer.Option(None, "--reason", help="Reason for rejection."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    write: bool = typer.Option(False, "--write", help="Persist the rejection."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the rejection."),
) -> None:
    """Reject a ChangeRequest."""
    if dry_run and write:
        console.print("[red]Cannot use both --dry-run and --write.[/red]")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    is_preview = not write and not dry_run
    try:
        cr = reject_change_request(model_path, cr_id, approver, reason=reason, dry_run=not write)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(cr, indent=2, default=str))
    else:
        if is_preview:
            console.print(
                f"[yellow]Preview only: ChangeRequest {cr_id} would be rejected by "
                f"{approver}. Use --write to persist.[/yellow]"
            )
        elif dry_run:
            console.print(
                f"[yellow]Dry-run: ChangeRequest {cr_id} would be rejected by "
                f"{approver}. No files were modified.[/yellow]"
            )
        else:
            console.print(f"[yellow]ChangeRequest {cr_id} rejected by {approver}[/yellow]")

    if not write:
        raise typer.Exit()

    service = AuditEventService(repo_root)
    service.emit(
        create_audit_event(
            event_type="change_request_rejected",
            actor=approver,
            status="success",
            command="change-request reject",
            proposal_id=cr_id,
            changed_object_ids=cr.get("affected_objects") or [],
            outputs={"approver": approver, "approvals": cr.get("approvals", [])},
        )
    )

    # Emit notification events
    try:
        preview_entries = preview_notifications(
            model_path=model_path,
            cr_id=cr_id,
        )
        for entry in preview_entries:
            emit_notification_event(
                repo_root=repo_root,
                event_type="change_request_rejected",
                source_type="ChangeRequest",
                source_id=cr_id,
                recipient_id=entry.recipient_id,
                recipient_role=entry.recipient_role,
                reason=entry.reason,
                affected_objects=cr.get("affected_objects") or [],
                message_summary=f"ChangeRequest {cr_id} rejected by {approver}",
                status="rejected",
            )
    except Exception:
        pass


# ---------------------------------------------------------------------------

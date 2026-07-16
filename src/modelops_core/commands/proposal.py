from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from modelops_core import __version__
from modelops_core.approval import compute_proposal_risk
from modelops_core.change_request import (
    approve_change_request,
    create_change_request,
    find_approved_cr_for_proposal,
)
from modelops_core.commands._common import (
    _resolve_repo,
    console,
)
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.impact.proposal_impact_service import generate_proposal_impact_report
from modelops_core.notifications import emit_notification_event, preview_notifications
from modelops_core.patching.apply_service import (
    apply_patch_proposal,
    dry_run_patch_proposal,
)
from modelops_core.patching.patch_proposal_service import (
    transition_patch_proposal_status,
)
from modelops_core.patching.proposal_reviewer_summary import (
    generate_reviewer_summary,
    reviewer_summary_to_dict,
)
from modelops_core.reports.audit_service import AuditEventService, create_audit_event
from modelops_core.repository import parse_file, scan_repository
from modelops_core.telemetry import with_telemetry

proposal_app = typer.Typer(
    name="proposal",
    help="Review and apply PatchProposals.",
)


@proposal_app.command("list")
def proposal_list(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    stale: bool = typer.Option(False, "--stale", help="Show only expired proposals."),
    status: str | None = typer.Option(
        None, "--status", help="Filter by status: pending_review, accepted, rejected, applied."
    ),
    reviewer: str | None = typer.Option(None, "--reviewer", help="Filter by reviewer identity."),
) -> None:
    """List all PatchProposals in the repository."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposals_dir = model_path / "patch-proposals"

    if not proposals_dir.exists():
        if json_output:
            print(json.dumps([]))
            raise typer.Exit()
        console.print("[yellow]No patch-proposals directory found.[/yellow]")
        raise typer.Exit()

    files = sorted(proposals_dir.glob("PP-*.md"))
    if not files:
        if json_output:
            print(json.dumps([]))
            raise typer.Exit()
        console.print("[yellow]No PatchProposals found.[/yellow]")
        raise typer.Exit()

    proposals = []

    for f in files:
        parsed = parse_file(f)
        fm = parsed.frontmatter or {}
        expires_at = fm.get("expires_at")
        is_expired = False
        if expires_at:
            try:
                exp_dt = datetime.fromisoformat(str(expires_at))
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=UTC)
                is_expired = exp_dt < datetime.now(UTC)
            except ValueError:
                pass
        if stale and not is_expired:
            continue
        if status and fm.get("status") != status:
            continue
        if reviewer and fm.get("reviewer") != reviewer:
            continue
        proposals.append(
            {
                "id": fm.get("id", f.stem),
                "status": fm.get("status", ""),
                "applied": bool(fm.get("applied_at")),
                "expires_at": expires_at,
                "expired": is_expired,
                "reviewer": fm.get("reviewer"),
                "reviewed_at": fm.get("reviewed_at"),
            }
        )

    if json_output:
        print(json.dumps(proposals, indent=2, default=str))
        raise typer.Exit()

    table = Table("ID", "Status", "Applied", "Reviewer", "Expires")
    for p in proposals:
        expires_label = p["expires_at"] or "—"
        if p.get("expired"):
            expires_label = f"[red]{expires_label}[/red]"
        reviewer_label = p.get("reviewer") or "—"
        table.add_row(
            p["id"],
            p["status"],
            "yes" if p["applied"] else "no",
            reviewer_label,
            expires_label,
        )
    console.print(table)


@proposal_app.command("show")
def proposal_show(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show details of a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}

    db_path = resolve_generated_path(repo_root) / "modelops.db"
    summary = generate_reviewer_summary(
        proposal=fm,
        repo_model_path=model_path,
        db_path=db_path,
    )

    if json_output:
        result = dict(fm)
        result["reviewer_summary"] = reviewer_summary_to_dict(summary)
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]PatchProposal: {proposal_id}[/bold]")
    console.print(f"  Status: {fm.get('status', '—')}")
    console.print(f"  Validation: {fm.get('validation_status', '—')}")
    console.print(f"  Operations: {len(fm.get('operations', []))}")
    if fm.get("reviewer"):
        console.print(f"  Reviewer: {fm['reviewer']}")
    if fm.get("reviewed_at"):
        console.print(f"  Reviewed at: {fm['reviewed_at']}")
    if fm.get("reviewer_notes"):
        console.print(f"  Reviewer notes: {fm['reviewer_notes']}")
    if fm.get("rejection_reason"):
        console.print(f"  Rejection reason: {fm['rejection_reason']}")
    if fm.get("expires_at"):
        console.print(f"  Expires at: {fm['expires_at']}")
    if fm.get("applied_at"):
        console.print(f"  Applied at: {fm['applied_at']}")
        console.print(f"  Changed files: {fm.get('applied_changed_files', [])}")

    # ---- Reviewer summary ----
    action_color = {
        "approve": "green",
        "approve_with_review": "yellow",
        "inspect": "red",
        "reject": "red",
    }.get(summary.recommended_action, "white")
    console.print("")
    console.print("[bold]Reviewer summary[/bold]")
    action_text = f"[{action_color}]{summary.recommended_action}[/{action_color}]"
    console.print(f"  Recommended action: {action_text}")
    console.print(f"  Risk level: {summary.risk_level}")
    console.print(f"  Requires approval: {summary.requires_approval}")
    console.print(f"  Affected objects: {len(summary.affected_object_ids)}")
    if summary.operations_by_type:
        console.print(
            "  Operations by type: "
            + ", ".join(f"{k}: {v}" for k, v in summary.operations_by_type.items())
        )

    if summary.risk_reasons:
        console.print("\n[bold]Risk reasons[/bold]")
        for reason in summary.risk_reasons:
            console.print(f"  - {reason}")

    if summary.validation_errors:
        console.print("\n[bold]Validation errors[/bold]")
        for message in summary.validation_errors:
            console.print(f"  - {message}")

    if summary.validation_warnings:
        console.print("\n[bold]Validation warnings[/bold]")
        for message in summary.validation_warnings:
            console.print(f"  - {message}")

    if summary.files_touched:
        console.print("\n[bold]Files touched[/bold]")
        for path in summary.files_touched:
            console.print(f"  - {path}")

    if summary.review_notes:
        console.print("\n[bold]Review notes[/bold]")
        for note in summary.review_notes:
            console.print(f"  - {note}")

    operations = fm.get("operations", [])
    if operations:
        console.print("")
        table = Table("Op", "Object ID", "Type", "Target")
        for op in operations:
            table.add_row(
                op.get("op", "—"),
                op.get("object_id", "—"),
                op.get("object_type", "—"),
                op.get("target_path", "—"),
            )
        console.print(table)


@proposal_app.command("accept")
@with_telemetry("proposal-accept")
def proposal_accept(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    reviewer: str = typer.Option(..., "--reviewer", help="Identity of the reviewer."),
    notes: str | None = typer.Option(None, "--notes", help="Reviewer notes."),
    skip_cr_creation: bool = typer.Option(
        False, "--skip-cr-creation", help="Skip auto-creating a ChangeRequest."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Accept a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    current_status = fm.get("status", "pending_review")
    is_applied = bool(fm.get("applied_at")) or fm.get("application_status") == "applied"

    if is_applied:
        msg = f"PatchProposal '{proposal_id}' has already been applied and cannot be accepted."
        if json_output:
            print(
                json.dumps(
                    {"proposal_id": proposal_id, "status": current_status, "error": msg},
                    indent=2,
                )
            )
            raise typer.Exit(code=1)
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(code=1)

    if current_status == "rejected":
        msg = f"PatchProposal '{proposal_id}' is rejected. It must be recreated to be accepted."
        if json_output:
            print(
                json.dumps(
                    {"proposal_id": proposal_id, "status": current_status, "error": msg},
                    indent=2,
                )
            )
            raise typer.Exit(code=1)
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(code=1)

    transition_warning = transition_patch_proposal_status(
        proposal_path, "accepted", reviewer=reviewer, reviewer_notes=notes
    )
    if transition_warning:
        console.print(f"[yellow]{transition_warning}[/yellow]")

    cr_id: str | None = None
    if not skip_cr_creation:
        cr_id = f"CR-{proposal_id}"
        create_change_request(
            model_path=model_path,
            cr_id=cr_id,
            title=f"Change Request: {proposal_id}",
            status="pending",
            requester=reviewer,
            linked_proposals=[proposal_id],
            affected_objects=fm.get("affected_objects") or [],
        )
        try:
            approve_change_request(model_path, cr_id, reviewer)
        except ValueError as exc:
            msg = str(exc)
            if json_output:
                print(
                    json.dumps(
                        {
                            "proposal_id": proposal_id,
                            "status": "accepted",
                            "change_request_id": cr_id,
                            "change_request_status": "pending",
                            "error": msg,
                        },
                        indent=2,
                    )
                )
                raise typer.Exit(code=1) from exc
            console.print(f"[green]PatchProposal {proposal_id} accepted.[/green]")
            console.print(f"[yellow]ChangeRequest {cr_id} created but not approved: {msg}[/yellow]")
            raise typer.Exit(code=1) from exc

        # Audit event for CR approval
        service = AuditEventService(repo_root)
        service.emit(
            create_audit_event(
                event_type="change_request_approved",
                actor=reviewer,
                status="success",
                command="proposal accept",
                proposal_id=cr_id,
                changed_object_ids=fm.get("affected_objects") or [],
                outputs={"auto_created": True, "linked_proposal": proposal_id},
            )
        )

    result: dict[str, Any] = {"proposal_id": proposal_id, "status": "accepted"}
    if cr_id:
        result["change_request_id"] = cr_id
        result["change_request_status"] = "approved"

    if json_output:
        print(json.dumps(result, indent=2))
        raise typer.Exit()

    console.print(f"[green]PatchProposal {proposal_id} accepted.[/green]")
    if cr_id:
        console.print(f"[green]ChangeRequest {cr_id} created and approved.[/green]")


@proposal_app.command("reject")
@with_telemetry("proposal-reject")
def proposal_reject(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    reviewer: str = typer.Option(..., "--reviewer", help="Identity of the reviewer."),
    reason: str | None = typer.Option(None, "--reason", help="Reason for rejection."),
    notes: str | None = typer.Option(None, "--notes", help="Reviewer notes."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Reject a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    current_status = fm.get("status", "pending_review")
    is_applied = bool(fm.get("applied_at")) or fm.get("application_status") == "applied"

    if is_applied:
        msg = f"PatchProposal '{proposal_id}' has already been applied and cannot be rejected."
        if json_output:
            print(
                json.dumps(
                    {"proposal_id": proposal_id, "status": current_status, "error": msg},
                    indent=2,
                )
            )
            raise typer.Exit(code=1)
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(code=1)

    if current_status == "accepted":
        msg = f"PatchProposal '{proposal_id}' is already accepted. It cannot be rejected."
        if json_output:
            print(
                json.dumps(
                    {"proposal_id": proposal_id, "status": current_status, "error": msg},
                    indent=2,
                )
            )
            raise typer.Exit(code=1)
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(code=1)

    transition_warning = transition_patch_proposal_status(
        proposal_path, "rejected", reviewer=reviewer, reviewer_notes=notes, rejection_reason=reason
    )
    if transition_warning:
        console.print(f"[yellow]{transition_warning}[/yellow]")

    if json_output:
        print(json.dumps({"proposal_id": proposal_id, "status": "rejected"}, indent=2))
        raise typer.Exit()

    console.print(f"[red]PatchProposal {proposal_id} rejected.[/red]")


@proposal_app.command("validate")
def proposal_validate(
    proposal_id: str | None = typer.Argument(None, help="PatchProposal ID (e.g. PP-001)."),
    proposal_file: Path | None = typer.Option(  # noqa: B008
        None, "--proposal", help="Path to a PatchProposal Markdown file outside the repository."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run deterministic validation on a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    if proposal_file is not None:
        proposal_path = proposal_file
        proposal_id = proposal_file.stem
    elif proposal_id is not None:
        proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"
    else:
        console.print("[red]Provide a PatchProposal ID or --proposal PATH.[/red]")
        raise typer.Exit(code=1)

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_path}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}

    from modelops_core.patching.patch_validator import validate_patch_proposal

    results = validate_patch_proposal(fm, repo_model_path=model_path)
    error_count = sum(1 for r in results if r.severity == "ERROR")
    warning_count = sum(1 for r in results if r.severity == "WARNING")

    if json_output:
        result = {
            "proposal_id": proposal_id,
            "error_count": error_count,
            "warning_count": warning_count,
            "results": [r.model_dump(mode="json") for r in results],
        }
        print(json.dumps(result, indent=2, default=str))

        service = AuditEventService(repo_root)
        service.emit(
            create_audit_event(
                event_type="proposal_validated",
                actor="system",
                status="success" if error_count == 0 else "failed",
                command="proposal validate",
                proposal_id=proposal_id,
                validation_status="valid" if error_count == 0 else "invalid",
                outputs={
                    "error_count": error_count,
                    "warning_count": warning_count,
                },
            )
        )

        if error_count > 0:
            raise typer.Exit(code=1)
        raise typer.Exit()

    console.print(f"[bold]Validation for {proposal_id}[/bold]")
    console.print(f"  Errors: {error_count}")
    console.print(f"  Warnings: {warning_count}")

    if results:
        table = Table("Severity", "Code", "Message", "Fix")
        for r in results:
            table.add_row(
                str(r.severity),
                r.code,
                r.message,
                r.suggested_fix or "—",
            )
        console.print(table)

    service = AuditEventService(repo_root)
    service.emit(
        create_audit_event(
            event_type="proposal_validated",
            actor="system",
            status="success" if error_count == 0 else "failed",
            command="proposal validate",
            proposal_id=proposal_id,
            validation_status="valid" if error_count == 0 else "invalid",
            outputs={
                "error_count": error_count,
                "warning_count": warning_count,
            },
        )
    )

    # Emit notification events for proposal validation
    try:
        preview_entries = preview_notifications(
            model_path=model_path,
            proposal_id=proposal_id,
        )
        for entry in preview_entries:
            emit_notification_event(
                repo_root=repo_root,
                event_type="patch_proposal_validated",
                source_type="PatchProposal",
                source_id=proposal_id,
                recipient_id=entry.recipient_id,
                recipient_role=entry.recipient_role,
                reason=entry.reason,
                affected_objects=fm.get("affected_objects") or [],
                message_summary=f"PatchProposal {proposal_id} validated",
                status="valid" if error_count == 0 else "invalid",
            )
    except Exception:
        pass

    if error_count > 0:
        raise typer.Exit(code=1)


@proposal_app.command("impact")
@with_telemetry("proposal-impact")
def proposal_impact(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    max_depth: int = typer.Option(2, "--max-depth", help="Maximum impact traversal depth."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show impact analysis for a PatchProposal's operations."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    operations = fm.get("operations", [])

    report = generate_proposal_impact_report(db_path, proposal_id, operations, max_depth=max_depth)

    # Risk assessment
    risk = compute_proposal_risk(operations, model_path, impact_report=report)

    if json_output:
        result = {
            "proposal_id": report.proposal_id,
            "high_risk": report.high_risk,
            "risk_assessment": {
                "requires_approval": risk.requires_approval,
                "risk_level": risk.risk_level,
                "risk_reasons": risk.risk_reasons,
                "triggering_rules": risk.triggering_rules,
                "affected_object_count": risk.affected_object_count,
                "max_impact_depth": risk.max_impact_depth,
            },
            "affected_objects": [
                {
                    "object_id": obj.object_id,
                    "object_type": obj.object_type,
                    "object_name": obj.object_name,
                    "relationship_type": obj.relationship_type,
                    "direction": obj.direction,
                    "depth": obj.depth,
                }
                for obj in report.all_affected_objects
            ],
            "operations": [
                {
                    "op": op_report.op,
                    "object_id": op_report.object_id,
                    "object_type": op_report.object_type,
                    "affected_count": len(op_report.impact_report.affected_objects)
                    + len(op_report.synthetic_affected),
                }
                for op_report in report.operation_reports
            ],
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Impact Report for {proposal_id}[/bold]")
    if report.high_risk:
        console.print("[red]  ⚠ High-risk proposal[/red]")
    console.print(f"  Risk level: {risk.risk_level}")
    if risk.requires_approval:
        console.print("[yellow]  ⚠ Approval required[/yellow]")
        for reason in risk.risk_reasons:
            console.print(f"    • {reason}")
    console.print(f"  Operations analyzed: {len(report.operation_reports)}")

    for op_report in report.operation_reports:
        console.print(
            f"\n  [bold]{op_report.op}[/bold] → {op_report.object_id}"
            f" ({op_report.object_type or 'Unknown'})"
        )
        all_affected = op_report.impact_report.affected_objects + op_report.synthetic_affected
        if all_affected:
            table = Table("Object ID", "Type", "Direction", "Depth", "Relationship")
            for obj in all_affected:
                table.add_row(
                    obj.object_id,
                    obj.object_type or "—",
                    obj.direction or "—",
                    str(obj.depth),
                    obj.relationship_type or "—",
                )
            console.print(table)
        else:
            console.print("    No affected objects found.")


@proposal_app.command("diff")
def proposal_diff(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show before/after diff for each operation in a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    operations = fm.get("operations", [])

    diffs: list[dict[str, Any]] = []
    for op in operations:
        if not isinstance(op, dict):
            continue
        op_type = op.get("op", "")
        object_id = op.get("object_id", "")
        target_path = op.get("target_path", "")
        after = op.get("after")

        diff_entry: dict[str, Any] = {
            "op": op_type,
            "object_id": object_id,
            "target_path": target_path,
        }

        if op_type in ("create_object", "add_object"):
            diff_entry["before"] = None
            diff_entry["after"] = after
            diffs.append(diff_entry)
        elif op_type == "update_object":
            # Find current value from canonical file
            current_value: Any = None
            for file_path in scan_repository(model_path):
                file_parsed = parse_file(file_path)
                if file_parsed.frontmatter and file_parsed.frontmatter.get("id") == object_id:
                    frontmatter = dict(file_parsed.frontmatter)
                    if "." in target_path:
                        parts = target_path.split(".")
                        current_value = frontmatter
                        for part in parts:
                            if isinstance(current_value, dict):
                                current_value = current_value.get(part)
                            else:
                                current_value = None
                                break
                    else:
                        current_value = frontmatter.get(target_path)
                    break
            diff_entry["before"] = current_value
            diff_entry["after"] = after
            diffs.append(diff_entry)
        elif op_type == "delete_object":
            # Find current object content
            current_obj: Any = None
            for file_path in scan_repository(model_path):
                file_parsed = parse_file(file_path)
                if file_parsed.frontmatter and file_parsed.frontmatter.get("id") == object_id:
                    current_obj = dict(file_parsed.frontmatter)
                    break
            diff_entry["before"] = current_obj
            diff_entry["after"] = None
            diffs.append(diff_entry)
        else:
            diff_entry["status"] = "skipped"
            diff_entry["reason"] = f"Operation '{op_type}' diff not supported."
            diffs.append(diff_entry)

    if json_output:
        print(json.dumps({"proposal_id": proposal_id, "diffs": diffs}, indent=2, default=str))
        raise typer.Exit()

    def _fmt_value(value: Any) -> str:
        if value is None:
            return "[dim]—[/dim]"
        if isinstance(value, dict):
            # Compact inline dict: show first 3 keys max
            items = list(value.items())[:3]
            inner = ", ".join(f"{k}={v!r}" for k, v in items)
            suffix = "…" if len(value) > 3 else ""
            return f"{{{inner}{suffix}}}"
        if isinstance(value, list):
            if not value:
                return "[]"
            inner = ", ".join(repr(v) for v in value[:3])
            suffix = "…" if len(value) > 3 else ""
            return f"[{inner}{suffix}]"
        return str(value)

    console.print(f"[bold]Diff for {proposal_id}[/bold]")
    if not diffs:
        console.print("  No operations to diff.")
        raise typer.Exit()

    for d in diffs:
        op_type = d["op"]
        obj_id = d.get("object_id", "—")
        if op_type in ("create_object", "add_object"):
            console.print(f"\n  [green]{op_type}[/green] → {obj_id}")
            after = d.get("after") or {}
            if isinstance(after, dict):
                # Prioritise key fields, then remaining keys
                key_order = ["id", "type", "name", "title", "status"]
                seen: set[str] = set()
                rows: list[tuple[str, str]] = []
                for key in key_order:
                    if key in after:
                        rows.append((key, _fmt_value(after[key])))
                        seen.add(key)
                for key, val in after.items():
                    if key not in seen:
                        rows.append((key, _fmt_value(val)))
                table = Table(show_header=False, box=None, padding=(0, 2))
                table.add_column("Field", style="cyan", no_wrap=True)
                table.add_column("Value")
                for field, value in rows:
                    table.add_row(field, value)
                console.print(table)
            else:
                console.print(f"    Value: {_fmt_value(after)}")
        elif op_type == "update_object":
            console.print(f"\n  [yellow]{op_type}[/yellow] → {obj_id}")
            path = d.get("target_path", "")
            before = d.get("before")
            after = d.get("after")
            if "." in path:
                parts = path.split(".")
                console.print(f"    [dim]path:[/dim]   {' → '.join(parts)}")
                console.print(f"    [dim]before:[/dim] {_fmt_value(before)}")
                console.print(f"    [dim]after:[/dim]  {_fmt_value(after)}")
            else:
                console.print(f"    [dim]{path}[/dim]: {_fmt_value(before)} → {_fmt_value(after)}")
        elif op_type == "delete_object":
            console.print(f"\n  [red]{op_type}[/red] → {obj_id}")
            before = d.get("before") or {}
            obj_type = before.get("type", "object") if isinstance(before, dict) else "object"
            console.print(f"    Would remove: {obj_type}")
        else:
            console.print(f"\n  [dim]{op_type}[/dim] → {obj_id}")
            console.print(f"    {d.get('reason')}")


@proposal_app.command("apply")
@with_telemetry("proposal-apply")
def proposal_apply(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying."),
    apply: bool = typer.Option(False, "--apply", help="Apply the proposal to canonical files."),
    force: bool = typer.Option(
        False,
        "--force",
        help=(
            "Bypass the medium-risk approval-gate lookup (not recommended). "
            "High-risk proposals still require an approved ChangeRequest."
        ),
    ),
    skip_risk_check: bool = typer.Option(
        False, "--skip-risk-check", help="Skip high-risk proposal blocking."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Apply an accepted PatchProposal to canonical files.

    By default, this command runs in dry-run mode and shows what would change.
    Pass --apply to actually mutate canonical files.
    """
    if dry_run and apply:
        console.print("[red]Cannot use both --dry-run and --apply.[/red]")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    # Load proposal for risk assessment and notifications
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed_proposal = parse_file(proposal_path)
    fm = parsed_proposal.frontmatter or {}
    operations = fm.get("operations", [])

    # Risk assessment
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    impact_report = None
    if db_path.exists():
        impact_report = generate_proposal_impact_report(
            db_path, proposal_id, operations, max_depth=2
        )
    risk = compute_proposal_risk(operations, model_path, impact_report=impact_report)

    is_dry_run = not apply

    if is_dry_run:
        result = dry_run_patch_proposal(model_path, proposal_id)
        if result.error:
            if json_output:
                print(json.dumps({"error": result.error, "proposal_id": proposal_id}))
            else:
                console.print(f"[red]{result.error}[/red]")
            raise typer.Exit(code=1)

        if json_output:
            output = {
                "proposal_id": proposal_id,
                "dry_run": True,
                "would_change": result.would_change,
                "risk_level": risk.risk_level,
                "risk_assessment": {
                    "requires_approval": risk.requires_approval,
                    "risk_level": risk.risk_level,
                    "risk_reasons": risk.risk_reasons,
                    "triggering_rules": risk.triggering_rules,
                    "affected_object_count": risk.affected_object_count,
                    "max_impact_depth": risk.max_impact_depth,
                },
                "operations_preview": result.operations_preview,
            }
            if impact_report:
                output["affected_objects"] = [
                    {
                        "object_id": obj.object_id,
                        "object_type": obj.object_type,
                        "direction": obj.direction,
                        "depth": obj.depth,
                        "relationship_type": obj.relationship_type,
                    }
                    for obj in impact_report.all_affected_objects
                ]
            print(json.dumps(output, indent=2, default=str))
            raise typer.Exit()

        console.print(f"[bold]Dry-run for {proposal_id}[/bold]")
        console.print(f"  Would change: {result.would_change}")
        console.print(f"  Risk level: {risk.risk_level}")
        if risk.requires_approval:
            console.print("[yellow]  ⚠ Approval required[/yellow]")
            for reason in risk.risk_reasons:
                console.print(f"    • {reason}")
        if result.operations_preview:
            table = Table("Op", "Object", "Status", "Details")
            for p in result.operations_preview:
                details = p.get("file", "") or p.get("reason", "")
                table.add_row(
                    p.get("op", "—"),
                    p.get("object_id", "—"),
                    p.get("status", "—"),
                    details,
                )
            console.print(table)

        # Show impact summary
        if impact_report:
            console.print("\n[bold]Impact Summary[/bold]")
            if impact_report.high_risk:
                console.print("[red]  ⚠ High-risk proposal[/red]")
            affected = impact_report.all_affected_objects
            console.print(f"  Affected objects: {len(affected)}")
            if affected:
                table = Table("Object ID", "Type", "Direction", "Depth")
                for obj in affected[:10]:
                    table.add_row(
                        obj.object_id,
                        obj.object_type or "—",
                        obj.direction or "—",
                        str(obj.depth),
                    )
                console.print(table)
                if len(affected) > 10:
                    console.print(f"  ... and {len(affected) - 10} more")
        console.print(
            "\n[yellow]This was a dry-run. Pass --apply to actually mutate files.[/yellow]"
        )
        raise typer.Exit()

    # Approval gate
    approved_cr = None
    if risk.risk_level == "high" and not skip_risk_check:
        # High-risk proposals always require an approved ChangeRequest, even with --force.
        approved_cr = find_approved_cr_for_proposal(model_path, proposal_id)
        if approved_cr is None:
            if json_output:
                print(
                    json.dumps(
                        {
                            "error": "Approval required",
                            "proposal_id": proposal_id,
                            "risk_level": risk.risk_level,
                            "risk_reasons": risk.risk_reasons,
                        }
                    )
                )
            else:
                console.print(
                    f"[red]Approval required for {proposal_id}. Risk level: {risk.risk_level}[/red]"
                )
                for reason in risk.risk_reasons:
                    console.print(f"  • {reason}")
                console.print(
                    "[yellow]Create an approved ChangeRequest linking to this proposal, "
                    "or use --skip-risk-check to override.[/yellow]"
                )
            raise typer.Exit(code=1)
        if not json_output:
            console.print(f"[green]Approved via ChangeRequest {approved_cr.get('id')}[/green]")
    elif risk.requires_approval and not force and not skip_risk_check:
        approved_cr = find_approved_cr_for_proposal(model_path, proposal_id)
        if approved_cr is None:
            if json_output:
                print(
                    json.dumps(
                        {
                            "error": "Approval required",
                            "proposal_id": proposal_id,
                            "risk_level": risk.risk_level,
                            "risk_reasons": risk.risk_reasons,
                        }
                    )
                )
            else:
                console.print(
                    f"[red]Approval required for {proposal_id}. Risk level: {risk.risk_level}[/red]"
                )
                for reason in risk.risk_reasons:
                    console.print(f"  • {reason}")
                console.print(
                    "[yellow]Create an approved ChangeRequest linking to this proposal, "
                    "or use --force or --skip-risk-check to override.[/yellow]"
                )
            raise typer.Exit(code=1)
        if not json_output:
            console.print(f"[green]Approved via ChangeRequest {approved_cr.get('id')}[/green]")

    skip_risk = skip_risk_check or (approved_cr is not None)

    try:
        result = apply_patch_proposal(
            model_path,
            proposal_id,
            skip_risk_check=skip_risk,
            approved_change_request_id=approved_cr.get("id") if approved_cr else None,
        )
    except (ValueError, FileNotFoundError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc), "proposal_id": proposal_id}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        output = {
            "proposal_id": proposal_id,
            "applied": True,
            "changed_files": result.changed_files,
            "audit_event_written": result.audit_event_written,
            "index_rebuilt": result.index_rebuilt,
            "risk_level": result.risk_level,
            "risk_assessment": result.risk_assessment,
        }
        if result.approved_change_request_id:
            output["approved_change_request_id"] = result.approved_change_request_id
        print(json.dumps(output, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[green]Applied {proposal_id}[/green]")
    console.print(f"  Changed files: {len(result.changed_files)}")
    for f in result.changed_files:
        console.print(f"    {f}")
    if result.risk_level:
        console.print(f"  Risk level: {result.risk_level}")
    if force:
        console.print(
            "[yellow]  Warning: --force was used; normal approval workflow was bypassed.[/yellow]"
        )
    if result.audit_event_written:
        console.print("  Audit event written")
    if result.index_rebuilt:
        console.print("  Index rebuilt")

    # Emit notification events for proposal application
    try:
        preview_entries = preview_notifications(
            model_path=model_path,
            proposal_id=proposal_id,
        )
        for entry in preview_entries:
            emit_notification_event(
                repo_root=repo_root,
                event_type="patch_proposal_applied",
                source_type="PatchProposal",
                source_id=proposal_id,
                recipient_id=entry.recipient_id,
                recipient_role=entry.recipient_role,
                reason=entry.reason,
                affected_objects=[op.get("object_id", "") for op in operations],
                message_summary=f"PatchProposal {proposal_id} applied",
                status="applied",
            )
    except Exception:
        pass


@proposal_app.command("report")
@with_telemetry("proposal-report")
def proposal_report(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    stale_days: int | None = typer.Option(
        None, "--stale-days", help="Treat proposals older than N days as stale."
    ),
) -> None:
    """Generate a consolidated proposal lifecycle report."""
    from datetime import timedelta

    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposals_dir = model_path / "patch-proposals"

    proposals: list[dict[str, Any]] = []
    if proposals_dir.exists():
        for f in sorted(proposals_dir.glob("PP-*.md")):
            parsed = parse_file(f)
            fm = parsed.frontmatter or {}
            status = fm.get("status", "pending_review")
            applied = bool(fm.get("applied_at")) or fm.get("application_status") == "applied"
            effective_status = "applied" if applied else status

            expires_at = fm.get("expires_at")
            is_stale = False
            if expires_at:
                try:
                    exp_dt = datetime.fromisoformat(str(expires_at))
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=UTC)
                    is_stale = exp_dt < datetime.now(UTC)
                except ValueError:
                    pass

            if stale_days is not None and not is_stale:
                created_at = fm.get("created_at")
                if created_at:
                    try:
                        cre_dt = datetime.fromisoformat(str(created_at))
                        if cre_dt.tzinfo is None:
                            cre_dt = cre_dt.replace(tzinfo=UTC)
                        is_stale = cre_dt < datetime.now(UTC) - timedelta(days=stale_days)
                    except ValueError:
                        pass

            operations = fm.get("operations") or []
            risk = compute_proposal_risk(operations, model_path)

            proposals.append(
                {
                    "id": fm.get("id", f.stem),
                    "status": status,
                    "effective_status": effective_status,
                    "created_at": fm.get("created_at"),
                    "expires_at": expires_at,
                    "is_stale": is_stale,
                    "reviewer": fm.get("reviewer"),
                    "reviewed_at": fm.get("reviewed_at"),
                    "rejection_reason": fm.get("rejection_reason"),
                    "risk_level": risk.risk_level,
                    "requires_approval": risk.requires_approval,
                    "affected_object_count": risk.affected_object_count,
                    "operations_count": len(operations),
                    "validation_status": fm.get("validation_status"),
                }
            )

    # Audit trail
    service = AuditEventService(repo_root)
    all_events = service.read_events()
    proposal_events = [e for e in all_events if e.proposal_id is not None]

    # Rejection analysis
    rejection_reasons: dict[str, int] = {}
    rejected_by_reviewer: dict[str, int] = {}
    for p in proposals:
        if p["effective_status"] == "rejected" and p.get("rejection_reason"):
            reason = p["rejection_reason"]
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        if p["effective_status"] == "rejected" and p.get("reviewer"):
            reviewer = p["reviewer"]
            rejected_by_reviewer[reviewer] = rejected_by_reviewer.get(reviewer, 0) + 1

    # Stale summary
    stale_proposals = [p for p in proposals if p["is_stale"]]
    oldest_stale = None
    if stale_proposals:
        oldest_stale = min(
            (p for p in stale_proposals if p.get("expires_at")),
            key=lambda x: str(x["expires_at"]),
            default=None,
        )

    # Count by status
    by_status: dict[str, int] = {
        "pending": 0,
        "accepted": 0,
        "rejected": 0,
        "applied": 0,
        "stale": 0,
    }
    _STATUS_MAP = {
        "pending_review": "pending",
        "accepted": "accepted",
        "rejected": "rejected",
        "applied": "applied",
    }
    for p in proposals:
        key = _STATUS_MAP.get(p["effective_status"], p["effective_status"])
        if key in by_status:
            by_status[key] += 1
        if p["is_stale"]:
            by_status["stale"] += 1

    if json_output:
        report = {
            "martenweave_version": __version__,
            "proposals_total": len(proposals),
            "by_status": by_status,
            "stale_threshold_days": stale_days,
            "proposals": proposals,
            "rejected_analysis": {
                "total_rejected": by_status.get("rejected", 0),
                "rejection_reason_frequencies": rejection_reasons,
                "rejected_by_reviewer": rejected_by_reviewer,
            },
            "stale_summary": {
                "stale_count": len(stale_proposals),
                "oldest_stale_proposal_id": oldest_stale["id"] if oldest_stale else None,
                "oldest_stale_expires_at": oldest_stale["expires_at"] if oldest_stale else None,
            },
            "audit_summary": {
                "events_total": len(all_events),
                "proposal_events_total": len(proposal_events),
                "recent_events": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp,
                        "actor": e.actor,
                        "proposal_id": e.proposal_id,
                        "status": e.status,
                    }
                    for e in proposal_events[-5:]
                ],
            },
        }
        print(json.dumps(report, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Proposal Lifecycle Report[/bold]")
    console.print(f"  Total proposals: {len(proposals)}")
    console.print("")
    console.print("[bold]Status Breakdown[/bold]")
    for label, count in by_status.items():
        console.print(f"  {label}: {count}")

    if stale_proposals:
        console.print("")
        console.print(f"[yellow]Stale proposals: {len(stale_proposals)}[/yellow]")
        if oldest_stale:
            console.print(
                f"  Oldest stale: {oldest_stale['id']} (expires_at: {oldest_stale['expires_at']})"
            )

    if by_status.get("rejected", 0) > 0:
        console.print("")
        console.print("[bold]Rejection Analysis[/bold]")
        console.print(f"  Total rejected: {by_status['rejected']}")
        if rejection_reasons:
            console.print("  Rejection reasons:")
            for reason, count in sorted(rejection_reasons.items(), key=lambda x: -x[1]):
                console.print(f"    {reason}: {count}")
        if rejected_by_reviewer:
            console.print("  Rejected by reviewer:")
            for reviewer, count in sorted(rejected_by_reviewer.items(), key=lambda x: -x[1]):
                console.print(f"    {reviewer}: {count}")

    if proposals:
        console.print("")
        table = Table("ID", "Status", "Risk", "Ops", "Affected", "Stale", "Reviewer")
        for p in proposals:
            risk_label = p["risk_level"]
            if risk_label == "high":
                risk_label = f"[red]{risk_label}[/red]"
            elif risk_label == "medium":
                risk_label = f"[yellow]{risk_label}[/yellow]"
            stale_label = "yes" if p["is_stale"] else "no"
            if p["is_stale"]:
                stale_label = f"[red]{stale_label}[/red]"
            table.add_row(
                p["id"],
                p["effective_status"],
                risk_label,
                str(p["operations_count"]),
                str(p["affected_object_count"]),
                stale_label,
                p.get("reviewer") or "—",
            )
        console.print(table)

    if proposal_events:
        console.print("")
        console.print("[bold]Audit Trail Summary[/bold]")
        console.print(f"  Total events: {len(all_events)}")
        console.print(f"  Proposal-related events: {len(proposal_events)}")
        if len(proposal_events) > 0:
            recent = proposal_events[-5:]
            event_table = Table("Event Type", "Timestamp", "Actor", "Proposal")
            for e in recent:
                event_table.add_row(
                    e.event_type,
                    e.timestamp,
                    e.actor,
                    e.proposal_id or "—",
                )
            console.print(event_table)

    if not proposals:
        console.print("[yellow]No proposals found.[/yellow]")


@proposal_app.command("review-bundle")
@with_telemetry("proposal-review-bundle")
def proposal_review_bundle(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run report + impact + validate for a single PatchProposal."""

    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    # Handle nonexistent proposal
    if not proposal_path.exists():
        if json_output:
            print(
                json.dumps(
                    {
                        "proposal_id": proposal_id,
                        "error": "PatchProposal not found",
                        "report": None,
                        "impact": None,
                        "validation": None,
                    },
                    indent=2,
                    default=str,
                )
            )
            raise typer.Exit(code=1)
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    operations = fm.get("operations", [])

    # ---- Report section (same shape as proposal report per-proposal) ----
    status = fm.get("status", "pending_review")
    applied = bool(fm.get("applied_at")) or fm.get("application_status") == "applied"
    effective_status = "applied" if applied else status

    expires_at = fm.get("expires_at")
    is_stale = False
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(str(expires_at))
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=UTC)
            is_stale = exp_dt < datetime.now(UTC)
        except ValueError:
            pass

    risk = compute_proposal_risk(operations, model_path)

    report_section = {
        "id": fm.get("id", proposal_id),
        "status": status,
        "effective_status": effective_status,
        "created_at": fm.get("created_at"),
        "expires_at": expires_at,
        "is_stale": is_stale,
        "reviewer": fm.get("reviewer"),
        "reviewed_at": fm.get("reviewed_at"),
        "rejection_reason": fm.get("rejection_reason"),
        "risk_level": risk.risk_level,
        "requires_approval": risk.requires_approval,
        "affected_object_count": risk.affected_object_count,
        "operations_count": len(operations),
        "validation_status": fm.get("validation_status"),
    }

    # ---- Impact section ----
    impact_section: dict[str, Any] = {}
    if db_path.exists():
        impact_report = generate_proposal_impact_report(
            db_path, proposal_id, operations, max_depth=2
        )
        impact_risk = compute_proposal_risk(operations, model_path, impact_report=impact_report)
        impact_section = {
            "proposal_id": impact_report.proposal_id,
            "high_risk": impact_report.high_risk,
            "risk_assessment": {
                "requires_approval": impact_risk.requires_approval,
                "risk_level": impact_risk.risk_level,
                "risk_reasons": impact_risk.risk_reasons,
                "triggering_rules": impact_risk.triggering_rules,
                "affected_object_count": impact_risk.affected_object_count,
                "max_impact_depth": impact_risk.max_impact_depth,
            },
            "affected_objects": [
                {
                    "object_id": obj.object_id,
                    "object_type": obj.object_type,
                    "object_name": obj.object_name,
                    "relationship_type": obj.relationship_type,
                    "direction": obj.direction,
                    "depth": obj.depth,
                }
                for obj in impact_report.all_affected_objects
            ],
            "operations": [
                {
                    "op": op_report.op,
                    "object_id": op_report.object_id,
                    "object_type": op_report.object_type,
                    "affected_count": len(op_report.impact_report.affected_objects)
                    + len(op_report.synthetic_affected),
                }
                for op_report in impact_report.operation_reports
            ],
        }
    else:
        impact_section = {
            "proposal_id": proposal_id,
            "high_risk": False,
            "risk_assessment": {},
            "affected_objects": [],
            "operations": [],
            "note": "No index found. Run `martenweave build-index` first.",
        }

    # ---- Validation section ----
    from modelops_core.patching.patch_validator import validate_patch_proposal

    validation_results = validate_patch_proposal(fm)
    error_count = sum(1 for r in validation_results if r.severity == "ERROR")
    warning_count = sum(1 for r in validation_results if r.severity == "WARNING")

    validation_section = {
        "is_safe": error_count == 0,
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": [r.model_dump(mode="json") for r in validation_results],
    }

    if json_output:
        result = {
            "martenweave_version": __version__,
            "proposal_id": proposal_id,
            "report": report_section,
            "impact": impact_section,
            "validation": validation_section,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    # Human-readable output
    console.print(f"[bold]Proposal Review Bundle: {proposal_id}[/bold]")
    console.print("")

    # Report section
    console.print("[bold]─ Report ─[/bold]")
    stat = report_section["status"]
    eff_stat = report_section["effective_status"]
    console.print(f"  Status: {stat} (effective: {eff_stat})")
    console.print(f"  Risk level: {report_section['risk_level']}")
    console.print(f"  Requires approval: {report_section['requires_approval']}")
    console.print(f"  Operations: {report_section['operations_count']}")
    console.print(f"  Affected objects: {report_section['affected_object_count']}")
    if report_section["is_stale"]:
        console.print("  [red]Stale: yes[/red]")
    console.print("")

    # Impact section
    console.print("[bold]─ Impact ─[/bold]")
    if impact_section.get("note"):
        console.print(f"  [yellow]{impact_section['note']}[/yellow]")
    else:
        if impact_section.get("high_risk"):
            console.print("  [red]⚠ High-risk proposal[/red]")
        console.print(f"  Affected objects: {len(impact_section.get('affected_objects', []))}")
        console.print(f"  Operations analyzed: {len(impact_section.get('operations', []))}")
    console.print("")

    # Validation section
    console.print("[bold]─ Validation ─[/bold]")
    if validation_section["is_safe"]:
        console.print("  [green]✓ Safe[/green]")
    else:
        console.print("  [red]✗ Issues found[/red]")
    console.print(f"  Errors: {validation_section['error_count']}")
    console.print(f"  Warnings: {validation_section['warning_count']}")

    if validation_section["issues"]:
        table = Table("Severity", "Code", "Message", "Fix")
        for issue in validation_section["issues"]:
            table.add_row(
                str(issue.get("severity", "—")),
                issue.get("code", "—"),
                issue.get("message", "—"),
                issue.get("suggested_fix") or "—",
            )
        console.print(table)

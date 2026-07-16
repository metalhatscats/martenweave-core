"""Typer CLI for Martenweave Core."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.table import Table

from modelops_core import __version__
from modelops_core.agents import (
    ProductOwnerAgent,
    ProductOwnerInput,
    ReadinessAgent,
    ReadinessInput,
)
from modelops_core.ai.agent_loop import run_agent_loop
from modelops_core.approval import compute_proposal_risk
from modelops_core.assessment.assessment_service import (
    generate_assessment_package,
    generate_review_pack,
    generate_risk_report,
)
from modelops_core.assessment.comparison import (
    AssessmentComparisonError,
    compare_assessments,
    write_assessment_comparison,
)
from modelops_core.bundle import create_git_bundle
from modelops_core.change_request import (
    approve_change_request,
    create_change_request,
    find_approved_cr_for_proposal,
    list_change_requests,
    load_change_request,
    reject_change_request,
    update_change_request_status,
)
from modelops_core.commands._common import (
    _build_impact_grouping,
    _check_and_warn_stale_index,
    _print_validation_summary,
    _resolve_repo,
    app,
    console,
)
from modelops_core.commands.ai_provider import ai_provider_app
from modelops_core.commands.dataset import (
    gaps,
    import_drive,
    import_sheet,
    infer_model,
    profile_dataset,
    source_show,
    sources_list,
)
from modelops_core.commands.scaffold import bootstrap_assessment_command, init
from modelops_core.commands.health_reports import (
    analyze,
    doctor,
    gap_report,
    health,
    model_summary,
    object_card,
    owners,
    readiness,
    review_pack_app,
    risk_report,
    scorecard,
)
from modelops_core.commands.impact_trace import impact, trace
from modelops_core.commands.proposal import proposal_app
from modelops_core.commands.standalone import (
    agent_loop,
    executive_summary,
    pilot_outcome,
    propose_patch,
)
from modelops_core.commands.validate_index import (
    build_index,
    clean,
    index_fresh,
    validate,
)

app.add_typer(ai_provider_app, name="ai-provider")
app.add_typer(review_pack_app, name="review-pack")
app.add_typer(proposal_app, name="proposal")
from modelops_core.config import (
    load_repo_config,
    load_resource_limits,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.connectors.google_drive import GoogleDriveConnector
from modelops_core.diff import diff_repositories
from modelops_core.docs.static_doc_generator import generate_static_docs
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.exports import export_model_csv, export_model_jsonl, export_model_xlsx
from modelops_core.exports.github_publish_service import (
    publish_issue_from_draft,
    publish_pr_from_bundle,
)
from modelops_core.exports.google_sheets_export import export_to_google_sheets
from modelops_core.exports.schema_export_service import (
    export_schemas,
    write_schema_export,
)
from modelops_core.gaps import detect_dataset_gaps
from modelops_core.guardrails.config_guard import (
    ConfigGuardMode,
    has_blocking_issues,
    run_all_checks,
)
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.impact.proposal_impact_service import generate_proposal_impact_report
from modelops_core.imports import (
    dataset_profile_to_dict,
    infer_model_from_profile,
    profile_csv,
    profile_xlsx,
)
from modelops_core.imports.dataset_profiler import WorkbookProfile
from modelops_core.imports.google_sheets_import_service import (
    import_google_sheet_as_proposal,
)
from modelops_core.imports.model_sheet_import_service import (
    SpreadsheetImportError,
    import_model_sheet_csv,
    import_model_sheet_xlsx,
)
from modelops_core.imports.privacy import (
    DatasetPrivacyPolicy,
    apply_privacy_to_profile,
    apply_privacy_to_workbook,
    detect_high_risk_columns,
)
from modelops_core.index import build_index as _build_index
from modelops_core.index.dataset_profile_sync import link_dataset_profile_to_index
from modelops_core.index.query_service import (
    PaginatedResult,
    SearchResult,
    query_objects,
    search_objects,
    semantic_search_objects,
)
from modelops_core.issue_draft import (
    create_draft_from_change_request,
    create_draft_from_proposal,
    create_draft_from_validation,
    write_draft,
)
from modelops_core.notifications import (
    emit_notification_event,
    filter_notification_events,
    preview_notifications,
    read_notification_events,
)
from modelops_core.patching.apply_service import (
    apply_patch_proposal,
    dry_run_patch_proposal,
)
from modelops_core.patching.patch_proposal_service import (
    render_patch_proposal_markdown,
    transition_patch_proposal_status,
    write_patch_proposal,
)
from modelops_core.patching.proposal_reviewer_summary import (
    generate_reviewer_summary,
    reviewer_summary_to_dict,
)
from modelops_core.pilot import demo_bundle as demo_bundle_service
from modelops_core.pilot import executive_summary as executive_summary_service
from modelops_core.pilot import outcome as pilot_outcome_service
from modelops_core.pilot import review as assessment_review_service
from modelops_core.pilot.bootstrap import BootstrapAssessmentError, bootstrap_assessment
from modelops_core.pilot.preflight import run_preflight
from modelops_core.pilot.sanitize import sanitize_assessment
from modelops_core.reports.analysis_service import generate_analysis_report
from modelops_core.reports.audit_service import (
    AuditEventService,
    create_audit_event,
    filter_audit_events,
)
from modelops_core.reports.decisions_report import generate_decisions_report
from modelops_core.reports.diagnostics_bundle import write_diagnostics_bundle
from modelops_core.reports.gap_summary import generate_gap_summary_report
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.reports.index_freshness import check_index_freshness
from modelops_core.reports.model_summary_service import (
    generate_model_summary,
    model_summary_to_dict,
    model_summary_to_markdown,
)
from modelops_core.reports.object_card_service import (
    generate_object_card,
    object_card_to_dict,
)
from modelops_core.reports.ownership_report import generate_ownership_report
from modelops_core.reports.scorecard_service import generate_scorecard
from modelops_core.reports.source_registry_service import (
    SourceRegistryService,
    register_dataset_source,
    register_import_source,
)
from modelops_core.reports.usage_report_service import generate_usage_report
from modelops_core.repository import parse_file, scan_repository
from modelops_core.run import (
    generate_dataset_readiness_report,
    generate_migration_assessment,
    write_readiness_report,
)
from modelops_core.schemas.migration import can_migrate_from, migrate_object, needs_migration
from modelops_core.schemas.versioning import (
    CURRENT_SCHEMA_VERSION,
    validate_repo_schema_version,
)
from modelops_core.telemetry import record_object_count, with_telemetry
from modelops_core.trace import trace_object
from modelops_core.validation import validate_objects

diagnostics_app = typer.Typer(
    help="Export safe diagnostics bundles for support and agent handoffs.",
    no_args_is_help=True,
)
app.add_typer(diagnostics_app, name="diagnostics")



@diagnostics_app.command("export")
@with_telemetry("diagnostics_export")
def diagnostics_export(
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for the diagnostics bundle."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    include_outputs: bool = typer.Option(
        False,
        "--include-outputs",
        help="Include JSON snapshots of key commands in the bundle.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw manifest JSON."),
) -> None:
    """Export a safe diagnostics bundle for support and agent handoffs."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    bundle = write_diagnostics_bundle(
        repo_root,
        out,
        include_command_outputs=include_outputs,
    )

    if json_output:
        print(json.dumps(bundle.manifest, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Diagnostics bundle written to[/bold] {out}")
    console.print(f"  Total objects: {bundle.manifest.get('object_count', 0)}")
    console.print(f"  Index fresh:   {bundle.manifest.get('index_fresh')}")
    console.print(f"  Validation:    {bundle.manifest.get('validation', {}).get('is_valid')}")
    console.print("\n[bold]Bundle files[/bold]")
    for child in sorted(out.iterdir()):
        label = "dir" if child.is_dir() else "file"
        console.print(f"  [{label}] {child.name}")






# ---------------------------------------------------------------------------
# Run subcommands — end-to-end workflow orchestration
# ---------------------------------------------------------------------------
run_app = typer.Typer(
    name="run",
    help="Run end-to-end model governance workflows.",
)
app.add_typer(run_app, name="run")


@run_app.command("dataset-readiness")
@with_telemetry("run_dataset_readiness")
def dataset_readiness(
    dataset: Path = typer.Argument(  # noqa: B008
        ..., help="Path to CSV or XLSX dataset file."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Directory where readiness reports will be written."
    ),
    check_model: bool = typer.Option(
        False, "--check-model", help="Also include model-side gaps in the report."
    ),
    promote_to_proposal: bool = typer.Option(
        False,
        "--promote-to-proposal",
        help="Promote dataset gaps to a draft PatchProposal in model/patch-proposals/.",
    ),
    issue_draft: bool = typer.Option(
        False,
        "--issue-draft",
        help="Generate a GitHub-ready issue draft from the readiness report.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview the report without writing files."
    ),
) -> None:
    """Run a dataset readiness workflow: validate, index, profile, gaps, report."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if not model_path.exists():
        console.print(f"[red]Model path does not exist: {model_path}[/red]")
        raise typer.Exit(code=1)

    if not dataset.exists():
        console.print(f"[red]Dataset not found: {dataset}[/red]")
        raise typer.Exit(code=1)

    try:
        report = generate_dataset_readiness_report(
            repo_root=repo_root,
            dataset_path=dataset,
            check_model=check_model,
            dry_run=dry_run,
            promote_to_proposal=promote_to_proposal,
            issue_draft=issue_draft,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if not dry_run:
        json_path, md_path = write_readiness_report(report, out)

    if json_output:
        print(json.dumps(report.__dict__, indent=2, default=str, sort_keys=True))
        raise typer.Exit()

    verdict_color = {
        "ready": "green",
        "ready_with_warnings": "yellow",
        "blocked": "red",
    }.get(report.verdict, "white")

    console.print(
        f"[bold]Dataset Readiness:[/bold] [{verdict_color}]{report.verdict}[/{verdict_color}]"
    )
    console.print(f"  Repository: {repo_root}")
    console.print(f"  Dataset:    {dataset}")
    console.print(
        f"  Validation: {report.validation['error_count']} errors, "
        f"{report.validation['warning_count']} warnings"
    )
    if report.coverage:
        console.print(
            f"  Coverage:   {report.coverage.get('match_rate', 0.0):.1%} match rate "
            f"({report.coverage.get('matched_columns', 0)} / "
            f"{report.coverage.get('total_columns', 0)} columns)"
        )
    if report.dataset_gaps:
        console.print(f"  Dataset gaps: {len(report.dataset_gaps)}")
    if report.model_gaps:
        console.print(f"  Model gaps:   {len(report.model_gaps)}")
    if report.promoted_proposal_path:
        console.print(f"[green]Promoted to proposal: {report.promoted_proposal_path}[/green]")
    if report.issue_draft_path:
        console.print(f"[green]Issue draft: {report.issue_draft_path}[/green]")

    if dry_run:
        console.print("[yellow]Dry-run: no files written.[/yellow]")
    else:
        console.print(f"[green]Report written to {json_path}[/green]")
        console.print(f"[green]Report written to {md_path}[/green]")


@run_app.command("migration-assessment")
@with_telemetry("run_migration_assessment")
def migration_assessment(
    mapping: Path = typer.Option(  # noqa: B008
        ..., "--mapping", help="Path to the XLSX mapping workbook."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    dataset: Path | None = typer.Option(  # noqa: B008
        None, "--dataset", help="Optional path to a CSV or XLSX sample dataset."
    ),
    evidence: list[Path] = typer.Option(  # noqa: B008
        [], "--evidence", help="Optional evidence file (repeatable)."
    ),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for the assessment package."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw manifest JSON."),
) -> None:
    """Run a full SAP migration assessment from workbook to review pack."""
    repo_root = _resolve_repo(repo)

    if not mapping.exists():
        console.print(f"[red]Mapping workbook not found: {mapping}[/red]")
        raise typer.Exit(code=1)

    if dataset is not None and not dataset.exists():
        console.print(f"[red]Dataset not found: {dataset}[/red]")
        raise typer.Exit(code=1)

    for ev_path in evidence:
        if not ev_path.exists():
            console.print(f"[red]Evidence file not found: {ev_path}[/red]")
            raise typer.Exit(code=1)

    model_path = resolve_model_path(repo_root)
    if not model_path.exists():
        console.print(f"[red]Model path does not exist: {model_path}[/red]")
        raise typer.Exit(code=1)

    try:
        manifest = generate_migration_assessment(
            repo_root=repo_root,
            mapping_path=mapping,
            dataset_path=dataset,
            evidence_paths=evidence,
            out_dir=out,
        )
    except (ValueError, RuntimeError, ResourceLimitExceeded) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
            raise typer.Exit(code=1) from exc
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        data = {
            "martenweave_version": manifest.martenweave_version,
            "repo_name": manifest.repo_name,
            "repo_path": manifest.repo_path,
            "generated_at": manifest.generated_at,
            "inputs": manifest.inputs,
            "stage_statuses": [
                {"name": s.name, "status": s.status, "message": s.message}
                for s in manifest.stage_statuses
            ],
            "generated_artifacts": manifest.generated_artifacts,
        }
        print(json.dumps(data, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Migration assessment complete: {manifest.repo_name}[/bold]")
    console.print(f"  Output: {out}")
    console.print("\n[bold]Stage statuses[/bold]")
    for stage in manifest.stage_statuses:
        color = {"success": "green", "skipped": "yellow", "failed": "red"}.get(
            stage.status, "white"
        )
        console.print(f"  [{color}]{stage.status}[/{color}] {stage.name}: {stage.message}")
    console.print(f"\n[bold]Artifacts[/bold]: {len(manifest.generated_artifacts)} files")
    console.print(f"[green]Manifest: {out / 'manifest.json'}[/green]")


@app.command("pilot-preflight")
@with_telemetry("pilot_preflight")
def pilot_preflight(
    mapping: Path = typer.Option(  # noqa: B008
        ..., "--mapping", help="Path to the XLSX mapping workbook."
    ),
    dataset: list[Path] = typer.Option(  # noqa: B008
        [], "--dataset", help="Path to a CSV or XLSX dataset (repeatable)."
    ),
    evidence: list[Path] = typer.Option(  # noqa: B008
        [], "--evidence", help="Path to an evidence note (.md/.txt, repeatable)."
    ),
    validation_report: list[Path] = typer.Option(  # noqa: B008
        [],
        "--validation-report",
        help="Path to a validation report (.csv/.xlsx, repeatable).",
    ),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Directory where preflight reports will be written."
    ),
    include_raw_samples: bool = typer.Option(
        False,
        "--include-raw-samples",
        help="Include raw dataset sample values in the report (not recommended for sharing).",
    ),
) -> None:
    """Inspect pilot input files for safety before running an assessment."""
    if not mapping.exists():
        console.print(f"[red]Mapping workbook not found: {mapping}[/red]")
        raise typer.Exit(code=1)

    all_inputs = [mapping, *dataset, *evidence, *validation_report]
    for p in all_inputs:
        if not p.exists():
            console.print(f"[red]Input file not found: {p}[/red]")
            raise typer.Exit(code=1)

    report = run_preflight(
        mapping_path=mapping,
        dataset_paths=dataset,
        evidence_paths=evidence,
        validation_report_paths=validation_report,
        out_dir=out,
        include_raw_samples=include_raw_samples,
    )

    color = {"allowed": "green", "warning": "yellow", "blocked": "red"}.get(
        report.overall_status, "white"
    )
    console.print(f"[bold]Preflight complete:[/bold] [{color}]{report.overall_status}[/{color}]")
    console.print(f"  Output: {out}")
    for f in report.files:
        fcolor = {"allowed": "green", "warning": "yellow", "blocked": "red"}.get(
            f["status"], "white"
        )
        console.print(f"  [{fcolor}]{f['status']}[/{fcolor}] {Path(f['path']).name}")


# ---------------------------------------------------------------------------
# Evidence ingestion subcommands
# ---------------------------------------------------------------------------
evidence_app = typer.Typer(
    name="evidence",
    help="Create reviewable proposals from local project evidence.",
)
app.add_typer(evidence_app, name="evidence")


@evidence_app.command("ingest")
@with_telemetry("evidence-ingest")
def evidence_ingest(
    source: Path = typer.Option(  # noqa: B008
        ..., "--from", help="Markdown/text note or CSV/XLSX validation report."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Explicit output path for the reviewable PatchProposal Markdown file."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output proposal metadata as JSON."),
) -> None:
    """Extract deterministic candidate Issues into a proposal without mutating canonical files."""
    from modelops_core.evidence_ingestion import (
        EvidenceIngestionError,
        ingest_evidence,
        write_evidence_proposal,
    )

    repo_root = _resolve_repo(repo)
    try:
        result = ingest_evidence(source, resolve_model_path(repo_root))
        output_path = write_evidence_proposal(result, out)
    except EvidenceIngestionError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            console.print(f"[red]Evidence ingestion failed: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    payload = {
        "proposal_id": result.proposal["id"],
        "path": str(output_path),
        "finding_count": result.finding_count,
        "source_sha256": result.source_sha256,
        "validation_status": "valid",
        "canonical_files_changed": False,
    }
    if json_output:
        print(json.dumps(payload, indent=2))
        return
    console.print(f"[green]Review proposal written: {output_path}[/green]")
    console.print(f"  Candidate findings: {result.finding_count}")
    console.print("  Canonical files changed: no")


# ---------------------------------------------------------------------------
# Issue-draft subcommands
# ---------------------------------------------------------------------------
draft_app = typer.Typer(
    name="issue-draft",
    help="Generate GitHub-ready issue drafts from model artifacts.",
)
app.add_typer(draft_app, name="issue-draft")


@draft_app.command("create")
def draft_create(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    change_request: str | None = typer.Option(
        None, "--change-request", help="ChangeRequest ID to draft from."
    ),
    proposal: str | None = typer.Option(None, "--proposal", help="PatchProposal ID to draft from."),
    from_validation: bool = typer.Option(
        False, "--from-validation", help="Draft from current validation results."
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None, "--output", help="Output file path (default: generated/issues/<id>.md)."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate a GitHub issue draft Markdown file."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    generated_path = resolve_generated_path(repo_root)

    sources_selected = sum(bool(x) for x in (change_request, proposal, from_validation))
    if sources_selected == 0:
        console.print(
            "[red]Specify one source: --change-request, --proposal, or --from-validation[/red]"
        )
        raise typer.Exit(code=1)
    if sources_selected > 1:
        console.print("[red]Specify only one source at a time.[/red]")
        raise typer.Exit(code=1)

    try:
        if change_request:
            draft = create_draft_from_change_request(model_path, change_request)
        elif proposal:
            draft = create_draft_from_proposal(model_path, generated_path, proposal)
        elif from_validation:
            draft = create_draft_from_validation(repo_root)
        else:
            # unreachable
            raise typer.Exit(code=1)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    path = write_draft(repo_root, draft, output_path=output)

    if json_output:
        result = {
            "title": draft.title,
            "body": draft.body,
            "source_type": draft.source_type,
            "source_id": draft.source_id,
            "labels": draft.labels,
            "suggested_assignees": draft.suggested_assignees,
            "path": str(path),
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[green]Draft written to {path}[/green]")
    console.print(f"  Title: {draft.title}")
    console.print(f"  Labels: {', '.join(draft.labels)}")
    if draft.suggested_assignees:
        console.print(f"  Suggested assignees: {', '.join(draft.suggested_assignees)}")


# ---------------------------------------------------------------------------
# Change-request subcommands
# ---------------------------------------------------------------------------
cr_app = typer.Typer(
    name="change-request",
    help="Create and manage ChangeRequests.",
)
app.add_typer(cr_app, name="change-request")


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
# Notification subcommands
# ---------------------------------------------------------------------------
notifications_app = typer.Typer(
    name="notifications",
    help="Preview notification recipients for workflow actions.",
)
app.add_typer(notifications_app, name="notifications")


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
# ---------------------------------------------------------------------------
decisions_app = typer.Typer(
    name="decisions",
    help="Browse and inspect Decision objects.",
)
app.add_typer(decisions_app, name="decisions")


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


# ---------------------------------------------------------------------------
# Proposal subcommands
# ---------------------------------------------------------------------------
@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(8000, "--port", help="Bind port."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    mutation_token: str | None = typer.Option(
        None, "--mutation-token", help="Optional token required for API mutations."
    ),
) -> None:
    """Start the local API server."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print(
            "[red]uvicorn is required for the API server. "
            "Install it with: pip install uvicorn[/red]"
        )
        raise typer.Exit(code=1) from exc

    repo_root = _resolve_repo(repo)
    console.print(f"[green]Starting API server at http://{host}:{port}[/green]")
    console.print(f"  Repository: {repo_root}")

    from modelops_core.api.app import app as api_app
    from modelops_core.api.workspace import configure_workspace

    configure_workspace(repo_root, mutation_token=mutation_token)
    uvicorn.run(api_app, host=host, port=port)


@app.command("workbench")
def workbench(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(8000, "--port", help="Bind port."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    no_open: bool = typer.Option(False, "--no-open", help="Do not open a browser tab."),
) -> None:
    """Launch the local Martenweave Workbench (API + packaged UI)."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print(
            "[red]uvicorn is required for the workbench. Install it with: pip install uvicorn[/red]"
        )
        raise typer.Exit(code=1) from exc

    import importlib.resources
    import webbrowser
    from threading import Timer

    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    if not model_path.exists():
        console.print(f"[red]Repository not found or missing model/ directory: {repo_root}[/red]")
        raise typer.Exit(code=1)

    # Prefer the in-tree frontend/dist during development; fall back to the
    # packaged workbench_static directory shipped inside the wheel.
    static_dir = Path("frontend/dist").resolve()
    if not static_dir.is_dir():
        static_dir = Path(str(importlib.resources.files("modelops_core") / "workbench_static"))

    if not static_dir.is_dir():
        console.print(
            "[red]Workbench static files not found. Build the frontend first:\n"
            "  cd frontend && npm run build[/red]"
        )
        raise typer.Exit(code=1)

    from modelops_core.api.workbench_app import create_workbench_app

    workbench_app = create_workbench_app(repo_root, static_dir)
    url = f"http://{host}:{port}"

    console.print(f"[green]Starting Martenweave Workbench at {url}[/green]")
    console.print(f"  Repository: {repo_root}")
    console.print(f"  Static files: {static_dir}")

    if not no_open:
        Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        uvicorn.run(workbench_app, host=host, port=port)
    except SystemExit as exc:
        # uvicorn raises SystemExit on startup failure (e.g. port in use).
        raise typer.Exit(code=exc.code) from exc


@app.command("mcp")
def mcp_server_cmd(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    transport: str = typer.Option("stdio", "--transport", help="Transport: stdio or sse."),
) -> None:
    """Start the MCP server for agent integration."""
    try:
        from modelops_core.mcp_server import create_mcp_server
    except ImportError as exc:
        console.print(
            "[red]The MCP server requires the 'mcp' package. Install it with: pip install mcp[/red]"
        )
        raise typer.Exit(code=1) from exc

    repo_root = _resolve_repo(repo)
    console.print(f"[green]Starting MCP server ({transport})[/green]")
    console.print(f"  Repository: {repo_root}")

    mcp = create_mcp_server(repo=str(repo_root))
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "sse":
        mcp.run(transport="sse")
    else:
        console.print(f"[red]Unknown transport: {transport}. Use 'stdio' or 'sse'.[/red]")
        raise typer.Exit(code=1)


@app.command("import-model-sheet")
def import_model_sheet(
    input_path: Path = typer.Argument(  # noqa: B008
        ..., help="Path to CSV folder or XLSX workbook."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Import spreadsheet edits and generate a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if not input_path.exists():
        console.print(f"[red]Input not found: {input_path}[/red]")
        raise typer.Exit(code=1)

    limits = load_resource_limits(repo_root)
    try:
        if input_path.is_dir():
            proposal = import_model_sheet_csv(input_path, model_path)
        elif input_path.suffix.lower() == ".xlsx":
            proposal = import_model_sheet_xlsx(
                input_path, model_path, max_rows=limits.max_import_rows
            )
        else:
            console.print("[red]Input must be a CSV directory or an .xlsx workbook.[/red]")
            raise typer.Exit(code=1)
    except SpreadsheetImportError as exc:
        console.print(f"[red]Review import rejected: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    service = AuditEventService(repo_root)
    changed_object_ids = [op.get("object_id", "") for op in proposal.get("operations", [])]
    service.emit(
        create_audit_event(
            event_type="model_import",
            actor="system",
            status="success",
            command="import-model-sheet",
            changed_object_ids=changed_object_ids,
            proposal_id=proposal.get("id"),
            outputs={
                "proposal_id": proposal.get("id"),
                "operations_count": len(proposal.get("operations", [])),
                "warnings_count": len(proposal.get("warnings", [])),
            },
        )
    )

    # Register source
    src_service = SourceRegistryService(repo_root)
    register_import_source(
        src_service,
        proposal_id=proposal.get("id", ""),
        source_path=input_path,
        operations_count=len(proposal.get("operations", [])),
        warnings_count=len(proposal.get("warnings", [])),
    )

    if json_output:
        print(json.dumps(proposal, indent=2, default=str))
    else:
        console.print(f"[bold]PatchProposal: {proposal['id']}[/bold]")
        console.print(f"  Operations: {len(proposal['operations'])}")
        console.print(f"  Warnings: {len(proposal.get('warnings', []))}")
        for w in proposal.get("warnings", []):
            console.print(f"    [yellow]{w}[/yellow]")
        if proposal["operations"]:
            table = Table("Op", "Object", "Type", "Target")
            for op in proposal["operations"][:20]:
                table.add_row(
                    op.get("op", "—"),
                    op.get("object_id", "—"),
                    op.get("object_type", "—"),
                    op.get("target_path", "—"),
                )
            console.print(table)
            if len(proposal["operations"]) > 20:
                console.print(f"  ... and {len(proposal['operations']) - 20} more")


@app.command("import-excel-review")
def import_excel_review(
    input_path: Path = typer.Option(..., "--from", help="Reviewed XLSX workbook to import."),  # noqa: B008
    output: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Path for the generated PatchProposal Markdown."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Create a reviewable PatchProposal from a business-review XLSX workbook.

    This command writes only the requested proposal artifact. It never edits the
    canonical model; use the proposal review and approval workflow to apply an
    accepted proposal later.
    """
    repo_root = _resolve_repo(repo)
    if not input_path.is_file() or input_path.suffix.lower() != ".xlsx":
        console.print("[red]--from must point to an existing .xlsx workbook.[/red]")
        raise typer.Exit(code=1)

    try:
        proposal = import_model_sheet_xlsx(
            input_path,
            resolve_model_path(repo_root),
            max_rows=load_resource_limits(repo_root).max_import_rows,
            require_stable_ids=True,
        )
    except SpreadsheetImportError as exc:
        console.print(f"[red]Review import rejected: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_patch_proposal_markdown(proposal), encoding="utf-8")
    console.print(f"[green]PatchProposal written:[/green] {output}")
    console.print(f"  ID: {proposal['id']}")
    console.print(f"  Operations: {len(proposal['operations'])}")
    console.print("  Canonical model files were not changed.")


@app.command("export-model")
@with_telemetry("export-model")
def export_model(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    fmt: str = typer.Option("csv", "--format", help="Export format: csv, xlsx, or json."),
    business_review: bool = typer.Option(
        False, "--business-review", help="Styled XLSX for non-technical review."
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None, "--out", help="Output path for a single XLSX export."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Export canonical model objects to CSV or XLSX."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    limits = load_resource_limits(repo_root)
    try:
        if fmt.lower() == "csv":
            written = export_model_csv(model_path, max_objects=limits.max_export_objects)
            if json_output:
                print(
                    json.dumps(
                        {
                            "format": "csv",
                            "files": [str(f) for f in written],
                            "business_review": business_review,
                        },
                        indent=2,
                        default=str,
                    )
                )
                raise typer.Exit()
            console.print(f"[green]Exported {len(written)} CSV files[/green]")
            for f in written:
                console.print(f"  {f}")
            path = written[0] if written else None
        elif fmt.lower() == "json":
            written = export_model_jsonl(model_path, max_objects=limits.max_export_objects)
            if json_output:
                print(
                    json.dumps(
                        {
                            "format": "json",
                            "files": [str(f) for f in written],
                            "business_review": business_review,
                        },
                        indent=2,
                        default=str,
                    )
                )
                raise typer.Exit()
            console.print(f"[green]Exported {len(written)} JSONL files[/green]")
            for f in written:
                console.print(f"  {f}")
            path = written[0] if written else None
        elif fmt.lower() == "xlsx":
            if output is not None and output.suffix.lower() != ".xlsx":
                console.print(
                    "[red]--out must use an .xlsx filename when --format xlsx is selected.[/red]"
                )
                raise typer.Exit(code=1)
            path = export_model_xlsx(
                model_path,
                output_path=output,
                max_objects=limits.max_export_objects,
                business_review=business_review,
            )
            if json_output:
                print(
                    json.dumps(
                        {
                            "format": "xlsx",
                            "file": str(path),
                            "business_review": business_review,
                        },
                        indent=2,
                        default=str,
                    )
                )
                raise typer.Exit()
            label = "business-review XLSX workbook" if business_review else "XLSX workbook"
            console.print(f"[green]Exported {label}[/green]")
            console.print(f"  {path}")
        else:
            if json_output:
                print(json.dumps({"error": f"Unknown format: {fmt}"}))
            else:
                console.print(f"[red]Unknown format: {fmt}. Use 'csv', 'xlsx', or 'json'.[/red]")
            raise typer.Exit(code=1)
    except ResourceLimitExceeded as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    is_list_format = fmt.lower() in ("csv", "json")
    changed_files = [str(f) for f in (written if is_list_format else [path])]
    service = AuditEventService(repo_root)
    service.emit(
        create_audit_event(
            event_type="model_export",
            actor="system",
            status="success",
            command=f"export-model --format {fmt}",
            changed_files=changed_files,
            outputs={
                "format": fmt,
                "file_count": len(written) if is_list_format else 1,
            },
        )
    )


@app.command("export-schema")
@with_telemetry("export-schema")
def export_schema(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    type: str = typer.Option(
        "all", "--type", help="Object type to export. Use 'all' for every type."
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None, "--output", help="Output file path."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Export JSON Schema for canonical object types."""
    repo_root = _resolve_repo(repo)

    if output is None:
        output = resolve_generated_path(repo_root) / "schemas" / "canonical_objects.json"

    try:
        result = export_schemas(type_filter=type)
    except ValueError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    output_path = write_schema_export(output, type_filter=type)

    if json_output:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        raise typer.Exit()

    console.print(f"[green]Exported {result['type_count']} JSON Schema(s) to {output_path}[/green]")


@app.command("export-sheets")
def export_sheets(
    spreadsheet_id: str = typer.Argument(..., help="Google Sheets spreadsheet ID."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Export canonical model objects to Google Sheets.

    Requires google-api-python-client. Install with:
    pip install modelops_core[google]
    """
    repo_root = _resolve_repo(repo)

    limits = load_resource_limits(repo_root)
    try:
        result = export_to_google_sheets(
            repo_root,
            spreadsheet_id,
            max_objects=limits.max_export_objects,
        )
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[red]Export failed: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print("[green]Exported to Google Sheets[/green]")
    console.print(f"  URL: {result.spreadsheet_url}")
    console.print(f"  Sheets: {', '.join(result.sheet_names)}")
    console.print(f"  Total objects: {sum(result.object_counts.values())}")


@app.command("git-bundle")
def git_bundle(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID to bundle."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate a GitHub-ready change bundle from a PatchProposal."""
    repo_root = _resolve_repo(repo)

    try:
        result = create_git_bundle(repo_root, proposal_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        output = {
            "bundle_dir": str(result.bundle_dir),
            "proposal_id": result.proposal_id,
            "affected_objects": result.affected_objects,
            "commit_message": result.commit_message,
            "files": {
                "bundle_json": str(result.bundle_json_path),
                "readme": str(result.readme_path),
                "pr_body": str(result.pr_body_path),
                "changed_files_dir": str(result.changed_files_dir),
            },
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        console.print(f"[green]Bundle created for {proposal_id}[/green]")
        console.print(f"  Directory: {result.bundle_dir}")
        console.print(f"  Affected objects: {len(result.affected_objects)}")
        console.print(f"  README: {result.readme_path}")
        console.print(f"  PR body: {result.pr_body_path}")
        console.print(f"  Commit message: {result.pr_body_path.parent / 'COMMIT_MESSAGE.txt'}")


@app.command("publish-issue")
def publish_issue(
    draft: Path = typer.Argument(  # noqa: B008
        ..., help="Path to issue draft Markdown file."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    github_repo: str = typer.Option(  # noqa: B008
        ..., "--github-repo", help="Target GitHub repo (owner/name)."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating."),
    label: list[str] | None = typer.Option(  # noqa: B008
        None, "--label", help="GitHub labels."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Publish an issue draft to GitHub.

    Requires requests. Install with: pip install modelops_core[github]
    """
    repo_root = _resolve_repo(repo)

    try:
        result = publish_issue_from_draft(
            repo_root=repo_root,
            github_repo=github_repo,
            draft_path=draft,
            labels=label if label else None,
            dry_run=dry_run,
        )
    except Exception as exc:
        console.print(f"[red]Failed to publish issue: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        if dry_run:
            console.print("[yellow]Dry-run preview:[/yellow]")
            console.print(f"  Title: {result['title']}")
            console.print(f"  Repo: {result['repo']}")
            console.print(f"  Labels: {', '.join(result['labels'])}")
            console.print(f"  Body preview: {result['body']}")
        else:
            console.print("[green]Issue published[/green]")
            console.print(f"  URL: {result['issue_url']}")
            console.print(f"  Number: {result['issue_number']}")


@app.command("publish-pr")
def publish_pr(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID to publish."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    github_repo: str = typer.Option(..., "--github-repo", help="Target GitHub repo (owner/name)."),
    head: str = typer.Option(..., "--head", help="Branch with changes."),
    base: str = typer.Option("main", "--base", help="Branch to merge into."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Publish a git bundle as a GitHub pull request.

    Requires requests. Install with: pip install modelops_core[github]
    """
    repo_root = _resolve_repo(repo)

    try:
        result = publish_pr_from_bundle(
            repo_root=repo_root,
            github_repo=github_repo,
            proposal_id=proposal_id,
            head_branch=head,
            base_branch=base,
            dry_run=dry_run,
        )
    except Exception as exc:
        console.print(f"[red]Failed to publish PR: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        if dry_run:
            console.print("[yellow]Dry-run preview:[/yellow]")
            console.print(f"  Title: {result['title']}")
            console.print(f"  Repo: {result['repo']}")
            console.print(f"  Head: {result['head']} -> Base: {result['base']}")
            console.print(f"  Affected objects: {len(result['affected_objects'])}")
            console.print(f"  Body preview: {result['body']}")
        else:
            console.print("[green]Pull request published[/green]")
            console.print(f"  URL: {result['pr_url']}")
            console.print(f"  Number: {result['pr_number']}")


@app.command("audit-log")
def audit_log(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    object_id: str | None = typer.Option(None, "--object-id", help="Filter by changed object ID."),
    proposal_id: str | None = typer.Option(None, "--proposal-id", help="Filter by proposal ID."),
    event_type: str | None = typer.Option(None, "--event-type", help="Filter by event type."),
    date_from: str | None = typer.Option(None, "--date-from", help="Filter from date (ISO)."),
    date_to: str | None = typer.Option(None, "--date-to", help="Filter to date (ISO)."),
    filter_expr: list[str] | None = typer.Option(  # noqa: B008
        None, "--filter", help="Filter expressions in key=value format (e.g. proposal_id=PP-001)."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Query the append-only audit log."""
    repo_root = _resolve_repo(repo)
    service = AuditEventService(repo_root)
    events = service.read_events()

    if not events:
        if json_output:
            print(json.dumps([]))
            raise typer.Exit()
        console.print("[yellow]No audit events found.[/yellow]")
        raise typer.Exit()

    # Parse --filter expressions into individual filter params
    for expr in filter_expr or []:
        if "=" not in expr:
            console.print(f"[red]Invalid filter expression: {expr}. Use key=value format.[/red]")
            raise typer.Exit(code=1)
        key, value = expr.split("=", 1)
        if key == "object_id":
            object_id = value
        elif key == "proposal_id":
            proposal_id = value
        elif key == "event_type":
            event_type = value
        elif key == "date_from":
            date_from = value
        elif key == "date_to":
            date_to = value
        else:
            console.print(f"[yellow]Unknown filter key: {key}. Ignored.[/yellow]")

    filtered = filter_audit_events(
        events,
        object_id=object_id,
        proposal_id=proposal_id,
        event_type=event_type,
        date_from=date_from,
        date_to=date_to,
    )

    if json_output:
        print(json.dumps([e.to_dict() for e in filtered], indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Audit Log ({len(filtered)} events)[/bold]")
    if not filtered:
        console.print("  No events match the filters.")
        raise typer.Exit()

    table = Table("Event ID", "Type", "Timestamp", "Status", "Command", "Proposal")
    for e in filtered:
        table.add_row(
            e.event_id,
            e.event_type,
            e.timestamp,
            e.status,
            e.command or "—",
            e.proposal_id or "—",
        )
    console.print(table)


@app.command("usage-report")
def usage_report(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show usage report from audit events."""
    repo_root = _resolve_repo(repo)
    report = generate_usage_report(repo_root)

    if json_output:
        result = {
            "total_events": report.total_events,
            "event_type_counts": report.event_type_counts,
            "command_counts": report.command_counts,
            "status_counts": report.status_counts,
            "ai_usage_summary": report.ai_usage_summary,
            "date_range": report.date_range,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Usage Report[/bold]")
    console.print(f"  Total events: {report.total_events}")

    if report.date_range.get("from"):
        console.print(f"  Period: {report.date_range['from']} to {report.date_range['to']}")

    if report.event_type_counts:
        console.print("\n[bold]Event Types[/bold]")
        table = Table("Event Type", "Count")
        for et, count in sorted(report.event_type_counts.items(), key=lambda x: -x[1]):
            table.add_row(et, str(count))
        console.print(table)

    if report.command_counts:
        console.print("\n[bold]Commands[/bold]")
        table = Table("Command", "Count")
        for cmd, count in sorted(report.command_counts.items(), key=lambda x: -x[1]):
            table.add_row(cmd, str(count))
        console.print(table)

    if report.status_counts:
        console.print("\n[bold]Status[/bold]")
        table = Table("Status", "Count")
        for status, count in sorted(report.status_counts.items(), key=lambda x: -x[1]):
            table.add_row(status, str(count))
        console.print(table)

    console.print("\n[bold]AI Usage[/bold]")
    ai = report.ai_usage_summary
    console.print(f"  AI calls: {ai.get('ai_calls', 0)}")
    console.print(f"  Total tokens: {ai.get('total_tokens', 0)}")
    console.print(f"  Note: {ai.get('note', '')}")

    if report.total_events == 0:
        console.print(
            "\n[yellow]No audit events found. Run workflows to generate usage data.[/yellow]"
        )


@app.command("docs-build")
def docs_build(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    output: str = typer.Option(
        "generated/docs_site",
        "--output",
        "--site",
        help="Output directory for generated docs.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate static Markdown docs and a local read-only HTML viewer from the model index."""
    repo_root = _resolve_repo(repo)
    output_path = repo_root / output

    try:
        result = generate_static_docs(repo_root, output_path)
    except FileNotFoundError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[yellow]{exc}[/yellow]")
        raise typer.Exit(code=1) from None

    files = sorted(str(f.relative_to(result)) for f in result.rglob("*") if f.is_file())
    markdown_files = [name for name in files if name.endswith(".md")]
    viewer_files = [name for name in files if name.endswith((".html", ".json", ".css", ".js"))]
    manifest_path = result / "viewer-manifest.json"
    viewer_manifest = None
    if manifest_path.exists():
        viewer_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if json_output:
        print(
            json.dumps(
                {
                    "output_dir": str(result),
                    "files": files,
                    "viewer_files": viewer_files,
                    "viewer_manifest": viewer_manifest,
                },
                indent=2,
                default=str,
            )
        )
        raise typer.Exit()

    console.print(f"[bold]Documentation generated[/bold] at {result}")
    console.print(f"  {len(markdown_files)} Markdown file(s):")
    for name in markdown_files:
        console.print(f"    - {name}")
    console.print(f"  {len(viewer_files)} viewer file(s), including index.html")


@app.command("config-guard")
def config_guard(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    mode: ConfigGuardMode = typer.Option(  # noqa: B008
        ConfigGuardMode.LOCAL,
        "--mode",
        help=(
            "Scan mode. 'local' reports all blocking findings, including ignored local files. "
            "'release' does not block on ignored local-only files."
        ),
    ),
) -> None:
    """Scan repository for secrets and configuration guardrail issues."""
    repo_root = _resolve_repo(repo)

    results = run_all_checks(repo_root, mode=mode)

    if json_output:
        output: dict[str, Any] = {}
        for check_name, issues in results.items():
            output[check_name] = [
                {
                    "code": i.code,
                    "message": i.message,
                    "file_path": i.file_path,
                    "line_number": i.line_number,
                    "severity": i.severity,
                    "file_status": i.file_status,
                }
                for i in issues
            ]
        print(json.dumps(output, indent=2, default=str))
        if has_blocking_issues(results, mode=mode):
            raise typer.Exit(code=1)
        raise typer.Exit()

    total_issues = sum(len(v) for v in results.values())
    error_count = sum(1 for issues in results.values() for i in issues if i.severity == "ERROR")
    warning_count = sum(1 for issues in results.values() for i in issues if i.severity == "WARNING")

    console.print("[bold]Configuration Guardrails[/bold]")
    console.print(f"  Mode: {mode.value}")
    console.print(f"  Checks: {len(results)}")
    console.print(f"  Issues: {total_issues} ({error_count} errors, {warning_count} warnings)")

    for check_name, issues in results.items():
        if not issues:
            continue
        console.print(f"\n[bold]{check_name}[/bold] ({len(issues)} issues)")
        table = Table("Severity", "Code", "File Status", "File", "Line", "Message")
        for i in issues:
            table.add_row(
                i.severity,
                i.code,
                i.file_status or "—",
                i.file_path or "—",
                str(i.line_number) if i.line_number else "—",
                i.message,
            )
        console.print(table)

    if has_blocking_issues(results, mode=mode):
        console.print("[red]Blocking issues found.[/red]")
        raise typer.Exit(code=1)

    if total_issues == 0:
        console.print("[green]All guardrail checks passed.[/green]")


@app.command("diff")
def diff(
    base: Path = typer.Argument(  # noqa: B008
        ..., help="Path to base model repository."
    ),
    head: Path = typer.Argument(  # noqa: B008
        ..., help="Path to head model repository."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Compare two model repositories and show differences."""
    base_model = resolve_model_path(base.resolve())
    head_model = resolve_model_path(head.resolve())

    if not base_model.exists():
        console.print(f"[red]Base model path does not exist: {base_model}[/red]")
        raise typer.Exit(code=1)
    if not head_model.exists():
        console.print(f"[red]Head model path does not exist: {head_model}[/red]")
        raise typer.Exit(code=1)

    result = diff_repositories(base_model, head_model)

    if json_output:
        output = {
            "has_changes": result.has_changes,
            "base_count": result.base_count,
            "head_count": result.head_count,
            "added": result.added,
            "removed": result.removed,
            "changed": [
                {
                    "object_id": c.object_id,
                    "object_type": c.object_type,
                    "object_name": c.object_name,
                    "field_changes": [
                        {
                            "field": fc.field,
                            "old_value": fc.old_value,
                            "new_value": fc.new_value,
                        }
                        for fc in c.field_changes
                    ],
                }
                for c in result.changed
            ],
        }
        print(json.dumps(output, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Model Diff[/bold]")
    console.print(f"  Base objects: {result.base_count}")
    console.print(f"  Head objects: {result.head_count}")

    if not result.has_changes:
        console.print("[green]No differences found.[/green]")
        raise typer.Exit()

    if result.added:
        console.print(f"\n[bold green]Added ({len(result.added)})[/bold green]")
        table = Table("Object ID", "Type", "Name")
        for obj in result.added:
            table.add_row(
                obj["object_id"],
                obj.get("object_type") or "—",
                obj.get("object_name") or "—",
            )
        console.print(table)

    if result.removed:
        console.print(f"\n[bold red]Removed ({len(result.removed)})[/bold red]")
        table = Table("Object ID", "Type", "Name")
        for obj in result.removed:
            table.add_row(
                obj["object_id"],
                obj.get("object_type") or "—",
                obj.get("object_name") or "—",
            )
        console.print(table)

    if result.changed:
        console.print(f"\n[bold yellow]Changed ({len(result.changed)})[/bold yellow]")
        for obj in result.changed:
            console.print(f"  {obj.object_id} ({obj.object_type})")
            table = Table("Field", "Old Value", "New Value")
            for fc in obj.field_changes:
                old_str = str(fc.old_value) if fc.old_value is not None else "—"
                new_str = str(fc.new_value) if fc.new_value is not None else "—"
                table.add_row(fc.field, old_str, new_str)
            console.print(table)


def _filter_semantic_ids(
    db_path: Path,
    semantic_results: list[Any],
    object_type: str | None,
    status: str | None,
    domain: str | None,
    tags: list[str] | None,
) -> set[str]:
    """Return semantic result IDs that pass the same filters as keyword search."""
    if not semantic_results:
        return set()
    object_ids = [r.object_id for r in semantic_results]
    conditions: list[str] = [f"id IN ({', '.join('?' for _ in object_ids)})"]
    params: list[Any] = list(object_ids)
    if object_type:
        conditions.append("type = ?")
        params.append(object_type)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if domain:
        conditions.append("domain = ?")
        params.append(domain)
    if tags:
        placeholders = ", ".join("?" for _ in tags)
        conditions.append(f"id IN (SELECT object_id FROM tags WHERE tag IN ({placeholders}))")
        params.extend(tags)
    sql = "SELECT id FROM objects WHERE " + " AND ".join(conditions)
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return {row[0] for row in rows}


def _load_search_results_for_ids(db_path: Path, object_ids: set[str]) -> dict[str, SearchResult]:
    """Load SearchResult metadata for a set of object IDs."""
    if not object_ids:
        return {}
    placeholders = ", ".join("?" for _ in object_ids)
    sql = f"SELECT * FROM objects WHERE id IN ({placeholders})"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, list(object_ids)).fetchall()
    finally:
        conn.close()
    return {
        row["id"]: SearchResult(
            object_id=row["id"],
            object_type=row["type"],
            status=row["status"],
            name=row["name"],
            title=row["title"],
            domain=row["domain"],
            description=row["description"],
            source_file=row["source_file"],
        )
        for row in rows
    }


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query (keywords)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    object_type: str | None = typer.Option(None, "--type", help="Filter by object type."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    domain: str | None = typer.Option(None, "--domain", help="Filter by domain ID."),
    tags: list[str] | None = typer.Option(  # noqa: B008
        None, "--tag", help="Filter by tag (repeatable)."
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum results."),
    offset: int = typer.Option(0, "--offset", help="Skip first N results."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    semantic: bool = typer.Option(
        False,
        "--semantic",
        help=(
            "Rerank keyword results by local semantic similarity and surface "
            "additional semantically related objects."
        ),
    ),
    semantic_expand: bool = typer.Option(
        False, "--semantic-expand", help="Expand query with one-hop related object terms."
    ),
) -> None:
    """Search indexed objects by keyword."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    stale = _check_and_warn_stale_index(repo_root, json_output)

    paginated = search_objects(
        db_path=db_path,
        query=query,
        object_type=object_type,
        status=status,
        domain=domain,
        tags=tags,
        limit=limit,
        offset=offset,
    )
    results = paginated.results
    total_count = paginated.total_count
    semantic_error: str | None = None

    if semantic:
        keyword_by_id = {r.object_id: r for r in results}
        keyword_ids = set(keyword_by_id)
        # Search the full semantic index so related objects are surfaced even when
        # they do not contain the literal query terms.
        try:
            semantic_results = semantic_search_objects(
                db_path=db_path,
                query=query,
                candidate_ids=None,
                expand=semantic_expand,
                limit=limit + offset,
                expand_candidate_ids=keyword_ids,
                repo_root=repo_root,
            )
            allowed_ids = _filter_semantic_ids(
                db_path,
                semantic_results,
                object_type=object_type,
                status=status,
                domain=domain,
                tags=tags,
            )
            semantic_by_id = {
                r.object_id: r for r in semantic_results if r.object_id in allowed_ids
            }

            # Fetch metadata for semantic results that keyword search missed.
            semantic_only_ids = set(semantic_by_id) - keyword_ids
            metadata = _load_search_results_for_ids(db_path, semantic_only_ids)

            merged: dict[str, SearchResult] = {}
            for obj_id, sr in semantic_by_id.items():
                result = keyword_by_id.get(obj_id) or metadata.get(obj_id)
                if result is None:
                    continue
                result.score = sr.semantic_score
                result.matched_fields = result.matched_fields + [
                    "semantic:" + t for t in sr.matched_terms
                ]
                merged[obj_id] = result

            # Include keyword-only results with a zero semantic score so the ranking
            # stays on a single float scale and keyword-only matches do not outrank
            # real semantic matches.
            for r in results:
                if r.object_id not in merged:
                    r.score = 0.0
                    merged[r.object_id] = r

            results = sorted(merged.values(), key=lambda r: r.score, reverse=True)
            results = results[offset : offset + limit]
            total_count = len(merged)
            paginated = PaginatedResult(results=results, total_count=total_count)
        except ResourceLimitExceeded as exc:
            semantic_error = str(exc)
            if not json_output:
                console.print(f"[yellow]Semantic search disabled: {semantic_error}[/yellow]")
        except Exception as exc:  # noqa: BLE001
            semantic_error = f"Semantic search failed: {exc}"
            if not json_output:
                console.print(f"[yellow]{semantic_error}[/yellow]")

    if json_output:
        output: dict[str, Any] = {
            "stale_index_warning": stale,
            "results": [],
            "total_count": total_count,
        }
        if semantic and semantic_error is not None:
            output["semantic_error"] = semantic_error
        for r in results:
            result_obj = {
                "object_id": r.object_id,
                "object_type": r.object_type,
                "status": r.status,
                "name": r.name,
                "title": r.title,
                "domain": r.domain,
                "source_file": r.source_file,
                "score": r.score,
                "matched_fields": r.matched_fields,
            }
            if semantic:
                result_obj["semantic_score"] = r.score
                result_obj["semantic_matched_terms"] = [
                    f.removeprefix("semantic:")
                    for f in r.matched_fields
                    if f.startswith("semantic:")
                ]
            output["results"].append(result_obj)
        print(json.dumps(output, indent=2, default=str))
        raise typer.Exit()

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        raise typer.Exit()

    console.print(f"[bold]Search Results ({paginated.total_count})[/bold]")
    table = Table("ID", "Type", "Name", "Status", "Score", "Matched")
    for r in results:
        table.add_row(
            r.object_id,
            r.object_type,
            r.name or r.title or "—",
            r.status,
            str(r.score),
            ", ".join(r.matched_fields) or "—",
        )
    console.print(table)


@app.command("query")
def query(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    object_type: str | None = typer.Option(None, "--type", help="Filter by object type."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    domain: str | None = typer.Option(None, "--domain", help="Filter by domain ID."),
    name_like: str | None = typer.Option(None, "--name-like", help="Substring match on name."),
    tags: list[str] | None = typer.Option(  # noqa: B008
        None, "--tag", help="Filter by tag (repeatable)."
    ),
    owner: str | None = typer.Option(None, "--owner", help="Filter by owner/steward/approver ID."),
    sap_table: str | None = typer.Option(None, "--sap-table", help="Filter by SAP table name."),
    limit: int = typer.Option(50, "--limit", help="Maximum results."),
    offset: int = typer.Option(0, "--offset", help="Skip first N results."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run a structured query over the generated index."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    stale = _check_and_warn_stale_index(repo_root, json_output)

    paginated = query_objects(
        db_path=db_path,
        object_type=object_type,
        status=status,
        domain=domain,
        name_like=name_like,
        tags=tags,
        owner=owner,
        sap_table=sap_table,
        limit=limit,
        offset=offset,
    )
    results = paginated.results

    if json_output:
        output = {
            "stale_index_warning": stale,
            "results": [
                {
                    "object_id": r.object_id,
                    "object_type": r.object_type,
                    "status": r.status,
                    "name": r.name,
                    "title": r.title,
                    "domain": r.domain,
                    "source_file": r.source_file,
                }
                for r in results
            ],
            "total_count": paginated.total_count,
        }
        print(json.dumps(output, indent=2, default=str))
        raise typer.Exit()

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        raise typer.Exit()

    console.print(f"[bold]Query Results ({paginated.total_count})[/bold]")
    table = Table("ID", "Type", "Name", "Status", "Domain")
    for r in results:
        table.add_row(
            r.object_id,
            r.object_type,
            r.name or r.title or "—",
            r.status,
            r.domain or "—",
        )
    console.print(table)


@app.command("migrate")
def migrate(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    dry_run: bool = typer.Option(
        True, "--dry-run/--apply", help="Preview by default; use --apply to write."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Migrate canonical objects to the current schema version."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if not model_path.exists():
        if json_output:
            print(json.dumps({"error": f"Model path does not exist: {model_path}"}))
        else:
            console.print(f"[red]Model path does not exist: {model_path}[/red]")
        raise typer.Exit(code=1)

    files = scan_repository(model_path)
    migrated_count = 0
    skipped_count = 0
    migrated_files = []
    config_updated = False
    unsupported_files: list[str] = []
    planned_writes: list[tuple[Path, dict[str, Any]]] = []

    for file_path_str in files:
        file_path = Path(file_path_str)
        parsed = parse_file(file_path)
        fm = parsed.frontmatter
        if fm is None:
            skipped_count += 1
            continue
        if not needs_migration(fm):
            skipped_count += 1
            continue

        if not can_migrate_from(fm.get("schema_version")):
            unsupported_files.append(file_path.relative_to(repo_root).as_posix())
            continue

        new_fm = migrate_object(fm)
        if new_fm is None:
            skipped_count += 1
            continue

        migrated_count += 1
        old_version = fm.get("schema_version", "none")
        migrated_files.append(
            {
                "file": file_path.name,
                "old_version": old_version,
                "new_version": CURRENT_SCHEMA_VERSION,
            }
        )
        planned_writes.append((file_path, new_fm))
        if dry_run:
            if not json_output:
                console.print(
                    f"[yellow]Would migrate[/yellow] {file_path.name} "
                    f"({old_version} → {CURRENT_SCHEMA_VERSION})"
                )
            continue

    # Update repo config schema_version
    config_path = repo_root / "modelops.config.yaml"
    if not config_path.exists():
        config_path = repo_root / "modelops.config.yml"
    if config_path.exists():
        config = load_repo_config(repo_root)
        if config and config.schema_version != CURRENT_SCHEMA_VERSION:
            if not can_migrate_from(config.schema_version):
                unsupported_files.append(config_path.name)
            else:
                config_updated = True
        if config_updated:
            if dry_run:
                if not json_output:
                    console.print(
                        f"[yellow]Would update[/yellow] {config_path.name} "
                        f"({config.schema_version} → {CURRENT_SCHEMA_VERSION})"
                    )
    if unsupported_files:
        message = (
            "Migration refused: this Core does not support writing the following schema versions: "
            + ", ".join(unsupported_files)
        )
        if json_output:
            print(json.dumps({"error": message, "unsupported_files": unsupported_files}))
        else:
            console.print(f"[red]{message}[/red]")
        raise typer.Exit(code=1)

    receipt_path: Path | None = None
    if not dry_run and (planned_writes or config_updated):
        # Preserve exact originals before an atomic write.  A failed validation
        # restores them verbatim, including unknown frontmatter fields and bodies.
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_root = resolve_generated_path(repo_root) / "migration-backups" / timestamp
        originals: dict[Path, str] = {}
        try:
            for path, frontmatter in planned_writes:
                originals[path] = path.read_text(encoding="utf-8")
                backup_path = backup_root / path.relative_to(repo_root)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_text(originals[path], encoding="utf-8")
                from modelops_core.repository import rewrite_frontmatter

                temporary = path.with_name(f".{path.stem}.migrate{path.suffix}")
                temporary.write_text(originals[path], encoding="utf-8")
                rewrite_frontmatter(temporary, frontmatter)
                temporary.replace(path)
            if config_updated:
                originals[config_path] = config_path.read_text(encoding="utf-8")
                backup_path = backup_root / config_path.name
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_text(originals[config_path], encoding="utf-8")
                raw = yaml.safe_load(originals[config_path]) or {}
                raw["schema_version"] = CURRENT_SCHEMA_VERSION
                temporary = config_path.with_name(
                    f".{config_path.stem}.migrate{config_path.suffix}"
                )
                temporary.write_text(
                    yaml.safe_dump(raw, default_flow_style=False, sort_keys=False), encoding="utf-8"
                )
                temporary.replace(config_path)

            summary = validate_objects([parse_file(path) for path, _ in planned_writes])
            if not summary.is_valid:
                raise ValueError(
                    f"Post-migration validation failed with {summary.error_count} error(s)."
                )
            _build_index(
                repo_root=repo_root, db_path=resolve_generated_path(repo_root) / "modelops.db"
            )
            receipt_path = (
                resolve_generated_path(repo_root) / "migration-receipts" / f"{timestamp}.json"
            )
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(
                    {
                        "schema_version": CURRENT_SCHEMA_VERSION,
                        "changed_files": [
                            path.relative_to(repo_root).as_posix() for path, _ in planned_writes
                        ],
                        "backup": backup_root.relative_to(repo_root).as_posix(),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except Exception as exc:
            for path, original in originals.items():
                path.write_text(original, encoding="utf-8")
            if json_output:
                print(json.dumps({"error": str(exc), "rolled_back": True}))
            else:
                console.print(f"[red]Migration rolled back: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    if json_output:
        print(
            json.dumps(
                {
                    "dry_run": dry_run,
                    "migrated_count": migrated_count,
                    "skipped_count": skipped_count,
                    "schema_version": CURRENT_SCHEMA_VERSION,
                    "migrated_files": migrated_files,
                    "config_updated": config_updated,
                    "receipt": str(receipt_path.relative_to(repo_root)) if receipt_path else None,
                    "rollback": (
                        "Restore files from generated/migration-backups/<timestamp> and rebuild "
                        "the index."
                    ),
                },
                indent=2,
                default=str,
            )
        )
        raise typer.Exit()

    console.print(
        f"\n[bold]Migration complete[/bold] — {migrated_count} migrated, {skipped_count} skipped"
    )


# ---------------------------------------------------------------------------
# Assessment review subcommands
# ---------------------------------------------------------------------------
assessment_review_app = typer.Typer(
    name="assessment-review",
    help="Human disposition workflow for assessment findings.",
)
app.add_typer(assessment_review_app, name="assessment-review")


@assessment_review_app.command("set")
def assessment_review_set(
    assessment: Path = typer.Option(  # noqa: B008
        ..., "--assessment", help="Path to assessment manifest.json."
    ),
    finding_id: str = typer.Option(  # noqa: B008
        ..., "--finding-id", help="Stable finding ID from findings.json."
    ),
    disposition: str = typer.Option(  # noqa: B008
        ...,
        "--disposition",
        help=("Disposition: confirmed, false_positive, accepted_risk, deferred, resolved."),
    ),
    reviewer: str = typer.Option(  # noqa: B008
        ..., "--reviewer", help="Name or identifier of the reviewer."
    ),
    note: str | None = typer.Option(  # noqa: B008
        None, "--note", help="Optional review note."
    ),
) -> None:
    """Record a human disposition for a single assessment finding."""
    assessment_dir = assessment.resolve().parent
    try:
        record = assessment_review_service.set_review(
            assessment_dir=assessment_dir,
            finding_id=finding_id,
            disposition=disposition,
            reviewer=reviewer,
            note=note,
        )
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Review recorded for {finding_id}[/green]")
    console.print(f"  Disposition: {record['disposition']}")
    console.print(f"  Reviewer:    {record['reviewer']}")


@assessment_review_app.command("summary")
def assessment_review_summary(
    assessment: Path = typer.Option(  # noqa: B008
        ..., "--assessment", help="Path to assessment manifest.json."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Summarize current review state for an assessment."""
    assessment_dir = assessment.resolve().parent
    try:
        summary = assessment_review_service.summarize_reviews(assessment_dir)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(summary, indent=2, default=str, sort_keys=True))
        raise typer.Exit()

    console.print("[bold]Assessment Review Summary[/bold]")
    console.print(f"  Total findings:   {summary['total_findings']}")
    console.print(f"  Reviewed:         {summary['reviewed_count']}")
    console.print(f"  Unreviewed:       {summary['unreviewed_count']}")
    if summary["by_disposition"]:
        console.print("\n[bold]By disposition:[/bold]")
        for disp, count in sorted(summary["by_disposition"].items()):
            console.print(f"  {disp}: {count}")
    if summary["by_severity"]:
        console.print("\n[bold]By severity:[/bold]")
        for sev, count in sorted(summary["by_severity"].items()):
            console.print(f"  {sev}: {count}")
    if summary["by_category"]:
        console.print("\n[bold]By category:[/bold]")
        for cat, count in sorted(summary["by_category"].items()):
            console.print(f"  {cat}: {count}")
    if summary["unreviewed"]:
        console.print("\n[bold]Unreviewed findings:[/bold]")
        for fid in summary["unreviewed"][:20]:
            console.print(f"  - {fid}")
        if len(summary["unreviewed"]) > 20:
            console.print(f"  ... and {len(summary['unreviewed']) - 20} more")


@assessment_review_app.command("promote")
def assessment_review_promote(
    assessment: Path = typer.Option(  # noqa: B008
        ..., "--assessment", help="Path to assessment manifest.json."
    ),
    finding_id: str = typer.Option(  # noqa: B008
        ..., "--finding-id", help="Stable finding ID to promote."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Promote a confirmed finding to a PatchProposal for human approval."""
    assessment_dir = assessment.resolve().parent
    repo_root = _resolve_repo(repo)
    try:
        proposal_path = assessment_review_service.promote_finding(
            assessment_dir=assessment_dir,
            repo_root=repo_root,
            finding_id=finding_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Promoted {finding_id} to PatchProposal[/green]")
    console.print(f"  {proposal_path}")




# ---------------------------------------------------------------------------
# Demo bundle subcommands
# ---------------------------------------------------------------------------
demo_bundle_app = typer.Typer(
    name="demo-bundle",
    help="Build deterministic, sanitized demo bundles for public sharing.",
)
app.add_typer(demo_bundle_app, name="demo-bundle")


@demo_bundle_app.command("build")
@with_telemetry("demo_bundle_build")
def demo_bundle_build(
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for the demo bundle."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    mapping: Path | None = typer.Option(  # noqa: B008
        None, "--mapping", help="Path to the synthetic mapping workbook."
    ),
    generated_at: str | None = typer.Option(
        None,
        "--generated-at",
        help="Optional ISO timestamp for deterministic output.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw manifest JSON."),
) -> None:
    """Build a deterministic, sanitized demo bundle from the golden assessment."""
    repo_root = _resolve_repo(repo) if repo else None
    mapping_path = mapping

    try:
        bundle = demo_bundle_service.build_demo_bundle(
            out_dir=out,
            repo_root=repo_root,
            mapping_path=mapping_path,
            generated_at=generated_at,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
            raise typer.Exit(code=1) from exc
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    validation_errors = demo_bundle_service.validate_demo_bundle(bundle.bundle_dir)

    if json_output:
        print(json.dumps(bundle.manifest, indent=2, sort_keys=True))
        raise typer.Exit()

    console.print("[bold]Demo bundle complete[/bold]")
    console.print(f"  Output: {bundle.bundle_dir}")
    console.print(f"  Artifacts: {bundle.manifest['artifact_count']}")
    if validation_errors:
        console.print("[yellow]Validation warnings:[/yellow]")
        for error in validation_errors:
            console.print(f"  - {error}")
    else:
        console.print("[green]Bundle validation passed[/green]")


# ---------------------------------------------------------------------------
# Assessment subcommands
# ---------------------------------------------------------------------------
assessment_app = typer.Typer(
    name="assessment",
    help="Migration Model Readiness Assessment.",
)
app.add_typer(assessment_app, name="assessment")


@assessment_app.command("run")
@with_telemetry("assessment_run")
def assessment_run(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for assessment package."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON metadata."),
) -> None:
    """Run a full migration readiness assessment and write the output package."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Building index first...[/yellow]")
        try:
            _build_index(repo_root=repo_root, allow_invalid=True)
        except (ValueError, ResourceLimitExceeded) as exc:
            if json_output:
                print(json.dumps({"error": str(exc)}, indent=2))
                raise typer.Exit(code=1) from exc
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc

    try:
        package = generate_assessment_package(repo_root, out)
    except (ValueError, ResourceLimitExceeded, RuntimeError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
            raise typer.Exit(code=1) from exc
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        result = {
            "martenweave_version": __version__,
            "repo_name": package.repo_name,
            "generated_at": package.generated_at,
            "readiness_level": package.readiness_level,
            "object_count": package.object_count,
            "gap_score": package.gap_score,
            "high_risk_count": package.high_risk_count,
            "artifacts": [
                {
                    "path": str(a.path),
                    "description": a.description,
                }
                for a in package.artifacts
            ],
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Assessment complete: {package.repo_name}[/bold]")
    console.print(f"  Readiness level: {package.readiness_level}")
    console.print(f"  Objects:         {package.object_count}")
    console.print(f"  Gap score:       {package.gap_score}")
    console.print(f"  High risk items: {package.high_risk_count}")
    console.print(f"  Output:          {out}")
    console.print("\n[bold]Artifacts generated[/bold]")
    for a in package.artifacts:
        console.print(f"  {a.path.name} — {a.description}")


@assessment_app.command("compare")
def assessment_compare(
    base_manifest: Path = typer.Argument(  # noqa: B008
        ..., help="Earlier assessment manifest.json."
    ),
    head_manifest: Path = typer.Argument(  # noqa: B008
        ..., help="Later assessment manifest.json."
    ),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Directory for Markdown and JSON comparison reports."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print the comparison JSON to stdout."),
) -> None:
    """Compare two assessment runs using stable finding IDs and input fingerprints."""
    try:
        report = compare_assessments(base_manifest, head_manifest)
        json_path, markdown_path = write_assessment_comparison(report, out)
    except AssessmentComparisonError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    payload = report.to_dict()
    payload["artifacts"] = {"json": str(json_path), "markdown": str(markdown_path)}
    if json_output:
        print(json.dumps(payload, indent=2))
        return
    counts = payload["counts"]
    console.print(
        f"[bold]Assessment comparison: {report.base_run_id} → {report.head_run_id}[/bold]"
    )
    console.print("  " + ", ".join(f"{kind}: {count}" for kind, count in sorted(counts.items())))
    console.print(f"  JSON: {json_path}")
    console.print(f"  Markdown: {markdown_path}")


@assessment_app.command("sanitize")
@with_telemetry("assessment_sanitize")
def assessment_sanitize(
    input_dir: Path = typer.Option(  # noqa: B008
        ..., "--input", help="Input assessment directory to sanitize."
    ),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for the sanitized package."
    ),
    include_raw_datasets: bool = typer.Option(
        False,
        "--include-raw-datasets",
        help="Include raw dataset files from dataset_readiness/ (default: excluded).",
    ),
) -> None:
    """Create a sanitized, shareable copy of an assessment package."""
    if not input_dir.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/red]")
        raise typer.Exit(code=1)

    try:
        manifest = sanitize_assessment(
            input_dir,
            out,
            exclude_raw_datasets=not include_raw_datasets,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Sanitized package written to {out}[/green]")
    console.print(f"  Included: {len(manifest['included_files'])}")
    console.print(f"  Excluded: {len(manifest['excluded_files'])}")
    console.print(f"  Redacted: {len(manifest['redactions'])}")


# ---------------------------------------------------------------------------
# Agent subcommands
# ---------------------------------------------------------------------------
agent_app = typer.Typer(
    name="agent",
    help="Agentic workflow orchestrators.",
)
app.add_typer(agent_app, name="agent")


@agent_app.command("product-owner")
@with_telemetry("agent_product_owner")
def agent_product_owner(
    source: Path = typer.Argument(  # noqa: B008
        ..., help="Path to a note/issue Markdown file or a ChangeRequest ID."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    source_type: str = typer.Option(
        "auto",
        "--source-type",
        help="Input type: auto, issue, note, change_request.",
    ),
    max_iterations: int = typer.Option(
        3,
        "--max-iterations",
        help="Maximum proposal refinement iterations.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview intended changes without writing files.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run the ProductOwner agent loop on a product input."""
    from modelops_core.config import load_repo_config

    repo_root = _resolve_repo(repo)
    config = load_repo_config(repo_root)
    if config is None:
        if json_output:
            print(json.dumps({"error": "No modelops.config.yaml found."}, indent=2))
        else:
            console.print("[red]No modelops.config.yaml found.[/red]")
        raise typer.Exit(code=1)

    inferred_type = source_type
    raw_text = ""
    source_id: str | None = None

    if inferred_type == "auto":
        if source.suffix.lower() in {".md", ".txt"}:
            inferred_type = "issue" if "issue" in source.name.lower() else "note"
        else:
            inferred_type = "change_request"

    if inferred_type == "change_request":
        source_id = source.name
        cr_path = resolve_model_path(repo_root) / "change-requests" / f"{source_id}.md"
        if not cr_path.exists():
            if json_output:
                print(json.dumps({"error": f"ChangeRequest not found: {source_id}"}, indent=2))
            else:
                console.print(f"[red]ChangeRequest not found: {source_id}[/red]")
            raise typer.Exit(code=1)
        raw_text = cr_path.read_text(encoding="utf-8")
    else:
        if not source.exists():
            if json_output:
                print(json.dumps({"error": f"File not found: {source}"}, indent=2))
            else:
                console.print(f"[red]File not found: {source}[/red]")
            raise typer.Exit(code=1)
        raw_text = source.read_text(encoding="utf-8")
        source_id = source.stem

    agent = ProductOwnerAgent(dry_run=dry_run, max_iterations=max_iterations)
    result = agent.run(
        ProductOwnerInput(
            source_type=inferred_type,
            raw_text=raw_text,
            source_id=source_id,
            repo_root=repo_root,
        )
    )

    if json_output:
        print(
            json.dumps(
                {
                    "success": result.success,
                    "iterations": result.iterations,
                    "proposal_id": result.proposal_id,
                    "proposal_path": str(result.proposal_path) if result.proposal_path else None,
                    "change_request_id": result.change_request_id,
                    "change_request_path": (
                        str(result.change_request_path) if result.change_request_path else None
                    ),
                    "validation_status": result.validation_status,
                    "impact_summary": result.impact_summary,
                    "draft_issue_path": (
                        str(result.draft_issue_path) if result.draft_issue_path else None
                    ),
                    "notification_event_ids": result.notification_event_ids,
                    "assumptions": result.assumptions,
                    "human_checks": result.human_checks,
                    "error_message": result.error_message,
                },
                indent=2,
                default=str,
            )
        )
        raise typer.Exit(code=0 if result.success else 1)

    if result.success:
        console.print(
            f"[green]ProductOwner loop completed in {result.iterations} iteration(s)[/green]"
        )
    else:
        console.print(
            f"[yellow]ProductOwner loop finished in {result.iterations} iteration(s) "
            "but did not produce a valid proposal.[/yellow]"
        )

    console.print(f"  Proposal:       {result.proposal_id or '—'}")
    console.print(f"  Validation:     {result.validation_status or '—'}")
    if result.proposal_path:
        console.print(f"  Proposal path:  {result.proposal_path}")
    if result.change_request_id:
        console.print(f"  ChangeRequest:  {result.change_request_id}")
    if result.draft_issue_path:
        console.print(f"  Issue draft:    {result.draft_issue_path}")
    if result.impact_summary:
        affected = result.impact_summary.get("affected_object_count")
        if affected is not None:
            console.print(f"  Affected objects: {affected}")

    if result.assumptions:
        console.print("\n[bold]Assumptions[/bold]")
        for assumption in result.assumptions:
            console.print(f"  - {assumption}")

    if result.human_checks:
        console.print("\n[bold]Human checks[/bold]")
        for check in result.human_checks:
            console.print(f"  - {check}")

    if result.error_message:
        console.print(f"\n[red]Error: {result.error_message}[/red]")
        raise typer.Exit(code=1)


def _run_readiness_cli(
    repo_root: Path,
    profile: str,
    dry_run: bool,
    json_output: bool,
    require_config: bool = True,
) -> None:
    """Shared implementation for the readiness CLI commands."""
    if require_config:
        config = load_repo_config(repo_root)
        if config is None:
            if json_output:
                print(json.dumps({"error": "No modelops.config.yaml found."}, indent=2))
            else:
                console.print("[red]No modelops.config.yaml found.[/red]")
            raise typer.Exit(code=1)

    agent = ReadinessAgent(dry_run=dry_run)
    result = agent.run(ReadinessInput(repo_root=repo_root, profile=profile))

    if json_output:
        print(
            json.dumps(
                {
                    "ready": result.ready,
                    "profile": result.profile,
                    "gate_count": result.gate_count,
                    "failed_gates": result.failed_gates,
                    "blockers": [
                        {
                            "gate": b.gate,
                            "severity": b.severity,
                            "message": b.message,
                            "object_id": b.object_id,
                            "issue_id": b.issue_id,
                        }
                        for b in result.blockers
                    ],
                    "issues_created": result.issues_created,
                    "proposal_created": result.proposal_created,
                    "draft_issue_path": (
                        str(result.draft_issue_path) if result.draft_issue_path else None
                    ),
                    "notification_event_ids": result.notification_event_ids,
                },
                indent=2,
                default=str,
            )
        )
        raise typer.Exit(code=0 if result.ready else 1)

    if result.ready:
        console.print(
            f"[green]Repository is ready for {result.profile}: "
            f"{result.gate_count}/{result.gate_count} gates passed[/green]"
        )
    else:
        console.print(
            f"[yellow]Repository is not ready for {result.profile}: "
            f"{len(result.failed_gates)} gate(s) failed[/yellow]"
        )

    console.print(f"\n[bold]Gates checked:[/bold] {result.gate_count}")
    if result.failed_gates:
        console.print(f"[bold]Failed gates:[/bold] {', '.join(result.failed_gates)}")
    if result.issues_created:
        console.print(f"[bold]Issues created:[/bold] {len(result.issues_created)}")
        for issue_id in result.issues_created:
            console.print(f"  - {issue_id}")
    if result.proposal_created:
        console.print(f"[bold]Proposal created:[/bold] {result.proposal_created}")
    if result.draft_issue_path:
        console.print(f"[bold]Draft issue:[/bold] {result.draft_issue_path}")
    if result.notification_event_ids:
        console.print(f"[bold]Notifications:[/bold] {len(result.notification_event_ids)}")

    if result.blockers:
        table = Table("Gate", "Severity", "Object", "Message")
        for b in result.blockers:
            table.add_row(b.gate, b.severity, b.object_id or "—", b.message)
        console.print("\n[bold]Blockers[/bold]")
        console.print(table)

    raise typer.Exit(code=0 if result.ready else 1)


@agent_app.command("readiness")
@with_telemetry("agent_readiness")
def agent_readiness(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    profile: str = typer.Option(
        "pilot",
        "--profile",
        help="Readiness profile: demo, pilot, release.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview intended changes without writing files.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run readiness gates and create Issue/Proposal artifacts for blockers."""
    repo_root = _resolve_repo(repo)
    _run_readiness_cli(repo_root, profile, dry_run, json_output, require_config=True)


if __name__ == "__main__":
    app()

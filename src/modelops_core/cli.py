"""Typer CLI for ModelOps MDM Core."""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from modelops_core import __version__
from modelops_core.approval import compute_proposal_risk
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
from modelops_core.config import (
    RepoConfig,
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
from modelops_core.gaps import detect_dataset_gaps
from modelops_core.guardrails.config_guard import (
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
from modelops_core.index.query_service import (
    query_objects,
    search_objects,
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
    transition_patch_proposal_status,
    write_patch_proposal,
)
from modelops_core.reports.analysis_service import generate_analysis_report
from modelops_core.reports.audit_service import (
    AuditEventService,
    create_audit_event,
    filter_audit_events,
)
from modelops_core.reports.decisions_report import generate_decisions_report
from modelops_core.reports.gap_summary import generate_gap_summary_report
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.reports.index_freshness import check_index_freshness
from modelops_core.reports.ownership_report import generate_ownership_report
from modelops_core.reports.scorecard_service import generate_scorecard
from modelops_core.reports.source_registry_service import (
    SourceRegistryService,
    register_dataset_source,
    register_import_source,
)
from modelops_core.reports.usage_report_service import generate_usage_report
from modelops_core.repository import parse_file, scan_repository
from modelops_core.schemas.migration import migrate_object, needs_migration
from modelops_core.schemas.versioning import (
    CURRENT_SCHEMA_VERSION,
    validate_repo_schema_version,
)
from modelops_core.telemetry import record_object_count, with_telemetry
from modelops_core.trace import trace_object
from modelops_core.validation import validate_objects

app = typer.Typer(
    name="modelops",
    help="ModelOps MDM Core — backend-first model registry CLI.",
    no_args_is_help=True,
)
_base_console = Console()
console = _base_console

_quiet = False
_no_color = False
_unwrapped_console: Console = _base_console


class _QuietConsole:
    """Wraps a Rich Console to suppress non-error output in quiet mode."""

    def __init__(self, wrapped: Console) -> None:
        self.wrapped = wrapped

    def print(self, *args: Any, **kwargs: Any) -> None:
        if _quiet:
            text = " ".join(str(a) for a in args)
            if "[red]" in text:
                self.wrapped.print(*args, **kwargs)
            return
        self.wrapped.print(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.wrapped, name)


def _resolve_repo(repo: str | None) -> Path:
    if repo is None:
        return Path.cwd()
    return Path(repo).resolve()


def _build_impact_grouping(
    report: Any, group_by: str
) -> dict[str, Any]:
    from modelops_core.impact.impact_report import ImpactReport

    assert isinstance(report, ImpactReport)
    if group_by == "type":
        return {
            obj_type: [
                {"object_id": o.object_id, "direction": o.direction, "depth": o.depth}
                for o in objs
            ]
            for obj_type, objs in report.grouped_by_type.items()
        }
    if group_by == "direction":
        return {
            "downstream": [
                {"object_id": o.object_id, "object_type": o.object_type, "depth": o.depth}
                for o in report.downstream_objects
            ],
            "upstream": [
                {"object_id": o.object_id, "object_type": o.object_type, "depth": o.depth}
                for o in report.upstream_objects
            ],
        }
    if group_by == "relationship":
        groups: dict[str, list[Any]] = {}
        for o in report.affected_objects:
            groups.setdefault(o.relationship_type or "Unknown", []).append(
                {
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "direction": o.direction,
                    "depth": o.depth,
                }
            )
        return groups
    return {}


def _print_validation_summary(summary: Any) -> None:
    if _quiet and summary.is_valid:
        return
    target = _unwrapped_console if (_quiet and not summary.is_valid) else console
    target.print("[bold]Validation Results:[/bold]")
    target.print(f"  Errors:   {summary.error_count}")
    target.print(f"  Warnings: {summary.warning_count}")
    target.print(f"  Info:     {summary.info_count}")
    target.print(f"  Valid:    {summary.is_valid}")
    if summary.results:
        table = Table("Severity", "Code", "Object", "Message", "Fix")
        for r in summary.results:
            table.add_row(
                str(r.severity),
                r.code,
                r.object_id or "—",
                r.message,
                r.suggested_fix or "—",
            )
        target.print(table)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"modelops {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Suppress non-error output.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable ANSI color codes in terminal output.",
    ),
) -> None:
    global console, _quiet, _no_color, _unwrapped_console
    _quiet = quiet
    _no_color = no_color

    if no_color:
        _unwrapped_console = Console(color_system=None)
    else:
        _unwrapped_console = _base_console

    console = _unwrapped_console

    if quiet:
        console = _QuietConsole(console)


_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "model_spines"


@app.command()
def init(
    path: Path = typer.Argument(  # noqa: B008
        ..., help="Directory to scaffold the model repository."
    ),
    name: str = typer.Option("My Model Repository", help="Repository name."),
    template: str | None = typer.Option(
        None,
        "--template",
        help="Model spine template to copy (business_partner, generic_large_object).",
    ),
) -> None:
    """Scaffold a new model repository."""
    target = path.resolve()
    target.mkdir(parents=True, exist_ok=True)

    model_dir = target / "model"
    model_dir.mkdir(exist_ok=True)

    generated_dir = target / "generated"
    generated_dir.mkdir(exist_ok=True)

    data_dir = target / "data" / "samples"
    data_dir.mkdir(parents=True, exist_ok=True)

    config = RepoConfig(name=name)
    config_path = target / "modelops.config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            config.model_dump(), default_flow_style=False, sort_keys=False
        ),
        encoding="utf-8",
    )

    if template:
        template_path = _TEMPLATES_DIR / template
        if not template_path.exists():
            console.print(f"[red]Template not found: {template}[/red]")
            available = ", ".join(t.name for t in _TEMPLATES_DIR.iterdir() if t.is_dir())
            console.print(f"  Available: {available}")
            raise typer.Exit(code=1)

        template_model = template_path / "model"
        if template_model.exists():
            for src_file in template_model.iterdir():
                if src_file.is_file():
                    shutil.copy2(src_file, model_dir / src_file.name)

        template_config = template_path / "modelops.config.yaml"
        if template_config.exists():
            shutil.copy2(template_config, config_path)

        console.print(
            f"[green]Initialized model repository at {target} "
            f"from template '{template}'[/green]"
        )
    else:
        # Create a minimal example domain object
        example_md = model_dir / "DOMAIN-EXAMPLE.md"
        example_md.write_text(
            "---\n"
            "id: DOMAIN-EXAMPLE\n"
            "type: MasterDataDomain\n"
            "status: draft\n"
            "schema_version: \"1.0\"\n"
            "name: Example Domain\n"
            "---\n\n"
            "# Example Domain\n\n"
            "This is a placeholder domain object.\n",
            encoding="utf-8",
        )

        console.print(f"[green]Initialized model repository at {target}[/green]")

    console.print(f"  Config:   {config_path}")
    console.print(f"  Model:    {model_dir}")
    console.print(f"  Generated: {generated_dir}")


@app.command()
def profile_dataset(
    file: Path = typer.Argument(..., help="Path to CSV or XLSX file."),  # noqa: B008
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    include_raw_samples: bool = typer.Option(
        False,
        "--include-raw-samples",
        help="Include raw sample values in the saved profile (default: redacted).",
    ),
) -> None:
    """Profile a dataset file (CSV or XLSX) and save the profile."""
    repo_root = _resolve_repo(repo)
    generated_path = resolve_generated_path(repo_root)
    profile_dir = generated_path / "dataset_profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)

    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(code=1)

    limits = load_resource_limits(repo_root)
    dataset_id = file.stem
    suffix = file.suffix.lower()

    if suffix == ".csv":
        raw_profile = profile_csv(
            file,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )
    elif suffix in {".xlsx", ".xls"}:
        raw_profile = profile_xlsx(
            file,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )
    else:
        console.print(f"[red]Unsupported file format: {suffix}[/red]")
        raise typer.Exit(code=1)

    # Apply privacy controls
    policy = DatasetPrivacyPolicy(include_raw_samples=include_raw_samples)
    if isinstance(raw_profile, WorkbookProfile):
        profile = apply_privacy_to_workbook(raw_profile, policy)
        high_risk_cols: list[str] = []
        for sheet in profile.sheets:
            high_risk_cols.extend(detect_high_risk_columns(sheet))
    else:
        profile = apply_privacy_to_profile(raw_profile, policy)
        high_risk_cols = detect_high_risk_columns(profile)

    profile_dict = dataset_profile_to_dict(profile)
    output_path = profile_dir / f"{dataset_id}.json"
    output_path.write_text(
        json.dumps(profile_dict, indent=2, default=str, sort_keys=True),
        encoding="utf-8",
    )

    # Register source
    src_service = SourceRegistryService(repo_root)
    register_dataset_source(
        src_service,
        dataset_id=dataset_id,
        file_path=file,
        file_hash=profile_dict.get("file_hash", ""),
        row_count=profile_dict.get("row_count", 0),
        column_count=profile_dict.get("column_count", 0),
    )

    if json_output:
        print(json.dumps(profile_dict, indent=2, default=str, sort_keys=True))
    else:
        console.print(f"[green]Profile saved to {output_path}[/green]")
        if hasattr(profile, "sheet_names"):
            console.print(f"  Sheets: {len(profile.sheets)}")
            for sheet in profile.sheets:
                console.print(
                    f"    {sheet.sheet_name}: {sheet.row_count} rows, "
                    f"{sheet.column_count} cols"
                )
        else:
            console.print(f"  Rows: {profile.row_count}")
            console.print(f"  Columns: {profile.column_count}")
            status_label = "OK"
            if not profile.status.success:
                status_label = "TRUNCATED"
            elif profile.status.sampled:
                status_label = "SAMPLED"
            console.print(f"  Status: {status_label}")
            if profile.status.sampled and profile.status.reason:
                console.print(f"  [yellow]{profile.status.reason}[/yellow]")

    if high_risk_cols:
        console.print(
            f"[yellow]Privacy warning: detected high-risk columns: "
            f"{', '.join(sorted(set(high_risk_cols)))}. "
            f"Sample values redacted.[/yellow]"
        )


@app.command("gaps")
@with_telemetry("gaps")
def gaps(
    dataset: Path = typer.Argument(..., help="Path to CSV or XLSX dataset file."),  # noqa: B008
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    create_issues: bool = typer.Option(
        False, "--create-issues", help="Create Issue canonical files for gaps."
    ),
    promote_to_proposal: bool = typer.Option(
        False, "--promote-to-proposal", help="Promote gaps to a draft PatchProposal."
    ),
    check_model: bool = typer.Option(
        False, "--check-model", help="Also check model-side gaps."
    ),
) -> None:
    """Detect dataset-to-model gaps by comparing dataset columns against FieldEndpoints."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    model_path = resolve_model_path(repo_root)

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    if not dataset.exists():
        console.print(f"[red]Dataset not found: {dataset}[/red]")
        raise typer.Exit(code=1)

    limits = load_resource_limits(repo_root)
    dataset_id = dataset.stem
    suffix = dataset.suffix.lower()

    if suffix == ".csv":
        raw_profile = profile_csv(
            dataset,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )
    elif suffix in {".xlsx", ".xls"}:
        raw_profile = profile_xlsx(
            dataset,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )
    else:
        console.print(f"[red]Unsupported dataset format: {suffix}[/red]")
        raise typer.Exit(code=1)

    policy = DatasetPrivacyPolicy(include_raw_samples=False)
    if isinstance(raw_profile, WorkbookProfile):
        profile = apply_privacy_to_workbook(raw_profile, policy)
    else:
        profile = apply_privacy_to_profile(raw_profile, policy)

    report = detect_dataset_gaps(profile, db_path)

    model_gaps: list[Any] = []
    if check_model:
        from modelops_core.gaps.gap_detection import detect_model_gaps

        model_gaps = detect_model_gaps(db_path)

    all_gaps = report.gaps + model_gaps

    if json_output:
        result = {
            "dataset_id": report.dataset_id,
            "matches": [
                {
                    "column_name": m.column_name,
                    "matched_endpoint_id": m.matched_endpoint_id,
                    "match_type": m.match_type,
                }
                for m in report.matches
            ],
            "gaps": [
                {
                    "column_name": g.column_name,
                    "gap_code": g.gap_code,
                    "severity": g.severity,
                    "message": g.message,
                    "evidence_ids": g.evidence_ids,
                    "source_dataset_metadata": g.source_dataset_metadata,
                    "recommended_proposal_op": g.recommended_proposal_op,
                }
                for g in all_gaps
            ],
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    if all_gaps:
        console.print(f"[bold]Gaps found for {report.dataset_id} ({len(all_gaps)})[/bold]")
        table = Table("Column", "Code", "Severity", "Message")
        for g in all_gaps:
            table.add_row(g.column_name, g.gap_code, g.severity, g.message)
        console.print(table)
    else:
        console.print(f"[green]No gaps found for {report.dataset_id}[/green]")

    if report.matches:
        console.print(f"\n[bold]Matches ({len(report.matches)})[/bold]")
        match_table = Table("Column", "Endpoint", "Match Type")
        for m in report.matches:
            match_table.add_row(m.column_name, m.matched_endpoint_id, m.match_type)
        console.print(match_table)

    if create_issues and all_gaps:
        issues_dir = model_path / "issues"
        issues_dir.mkdir(parents=True, exist_ok=True)
        for idx, g in enumerate(all_gaps, start=1):
            issue_id = f"ISSUE-GAP-{dataset_id.upper()}-{idx:03d}"
            issue_fm = {
                "id": issue_id,
                "type": "Issue",
                "status": "open",
                "name": f"Gap: {g.gap_code}",
                "issue_type": "dataset_gap",
                "severity": g.severity,
                "source_dataset_id": dataset_id,
                "source_column": g.column_name,
                "source_gap_code": g.gap_code,
                "recommended_action": g.message,
            }
            issue_path = issues_dir / f"{issue_id}.md"
            body_text = f"# {g.gap_code}\n\n{g.message}\n"
            yaml_text = yaml.safe_dump(
                issue_fm, default_flow_style=False, sort_keys=False, allow_unicode=True
            )
            issue_path.write_text(
                f"---\n{yaml_text}---\n\n{body_text}\n",
                encoding="utf-8",
            )
            console.print(f"[green]Created {issue_path.name}[/green]")

    if promote_to_proposal and report.gaps:
        from modelops_core.gaps.gap_detection import promote_gaps_to_proposal

        proposal_path = promote_gaps_to_proposal(report, model_path)
        console.print(f"[green]Created PatchProposal {proposal_path.name}[/green]")


@app.command("import-drive")
def import_drive(
    file_id: str = typer.Argument(..., help="Google Drive file ID."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    include_raw_samples: bool = typer.Option(
        False,
        "--include-raw-samples",
        help="Include raw sample values in the saved profile (default: redacted).",
    ),
) -> None:
    """Import a CSV or XLSX file from Google Drive and profile it.

    Requires google-api-python-client. Install with:
    pip install modelops_core[google]
    """
    repo_root = _resolve_repo(repo)
    generated_path = resolve_generated_path(repo_root)
    profile_dir = generated_path / "dataset_profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)

    try:
        connector = GoogleDriveConnector()
        meta = connector.fetch_metadata(file_id)
        content = connector.fetch_content(file_id)
    except Exception as exc:
        console.print(f"[red]Failed to fetch from Google Drive: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    # Determine file extension from MIME type or display name
    ext = ".csv"
    if meta.mime_type in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ):
        ext = ".xlsx"
    elif ".xlsx" in meta.display_name.lower():
        ext = ".xlsx"
    elif ".csv" in meta.display_name.lower():
        ext = ".csv"

    safe_name = meta.display_name or file_id
    if safe_name.endswith((".csv", ".xlsx", ".xls")):
        safe_name = Path(safe_name).stem
    dataset_id = f"drive_{safe_name}"

    temp_file = profile_dir / f"{dataset_id}{ext}"
    temp_file.write_bytes(content)

    limits = load_resource_limits(repo_root)

    if ext == ".csv":
        raw_profile = profile_csv(
            temp_file,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )
    else:
        raw_profile = profile_xlsx(
            temp_file,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )

    # Apply privacy controls
    from modelops_core.imports.privacy import (
        DatasetPrivacyPolicy,
        apply_privacy_to_profile,
        apply_privacy_to_workbook,
        detect_high_risk_columns,
    )

    policy = DatasetPrivacyPolicy(include_raw_samples=include_raw_samples)
    if isinstance(raw_profile, WorkbookProfile):
        profile = apply_privacy_to_workbook(raw_profile, policy)
        high_risk_cols: list[str] = []
        for sheet in profile.sheets:
            high_risk_cols.extend(detect_high_risk_columns(sheet))
    else:
        profile = apply_privacy_to_profile(raw_profile, policy)
        high_risk_cols = detect_high_risk_columns(profile)

    profile_dict = dataset_profile_to_dict(profile)
    output_path = profile_dir / f"{dataset_id}.json"
    output_path.write_text(
        json.dumps(profile_dict, indent=2, default=str, sort_keys=True),
        encoding="utf-8",
    )

    # Register source
    src_service = SourceRegistryService(repo_root)
    entry = connector.to_source_entry(file_id)
    entry.source_id = dataset_id
    entry.display_name = f"Drive import: {meta.display_name or file_id}"
    entry.metadata = {
        **entry.metadata,
        "drive_file_id": file_id,
        "row_count": profile_dict.get("row_count", 0),
        "column_count": profile_dict.get("column_count", 0),
        "profiled_at": profile_dict.get("profiled_at", ""),
    }
    src_service.register(entry)

    if json_output:
        print(json.dumps(profile_dict, indent=2, default=str, sort_keys=True))
    else:
        console.print(f"[green]Profile saved to {output_path}[/green]")
        if hasattr(profile, "sheet_names"):
            console.print(f"  Sheets: {len(profile.sheets)}")
            for sheet in profile.sheets:
                console.print(
                    f"    {sheet.sheet_name}: {sheet.row_count} rows, "
                    f"{sheet.column_count} cols"
                )
        else:
            console.print(f"  Rows: {profile.row_count}")
            console.print(f"  Columns: {profile.column_count}")
            status_label = "OK"
            if not profile.status.success:
                status_label = "TRUNCATED"
            elif profile.status.sampled:
                status_label = "SAMPLED"
            console.print(f"  Status: {status_label}")
            if profile.status.sampled and profile.status.reason:
                console.print(f"  [yellow]{profile.status.reason}[/yellow]")

    if high_risk_cols:
        console.print(
            f"[yellow]Privacy warning: detected high-risk columns: "
            f"{', '.join(sorted(set(high_risk_cols)))}. "
            f"Sample values redacted.[/yellow]"
        )


@app.command("import-sheet")
def import_sheet(
    spreadsheet_id: str = typer.Argument(..., help="Google Sheets spreadsheet ID."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Import a Google Sheet as a PatchProposal.

    Reads all non-metadata tabs and compares against existing canonical
    objects to generate a PatchProposal for human review.

    Requires google-api-python-client. Install with:
    pip install modelops_core[google]
    """
    repo_root = _resolve_repo(repo)

    try:
        proposal = import_google_sheet_as_proposal(repo_root, spreadsheet_id)
    except Exception as exc:
        console.print(f"[red]Failed to import from Google Sheets: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(proposal, indent=2, default=str))
    else:
        console.print(f"[bold]PatchProposal: {proposal['id']}[/bold]")
        console.print(f"  Operations: {len(proposal['operations'])}")
        console.print(f"  Warnings: {len(proposal.get('warnings', []))}")
        for w in proposal.get("warnings", [])[:5]:
            console.print(f"    [yellow]{w}[/yellow]")
        if len(proposal.get("warnings", [])) > 5:
            console.print(
                f"    ... and {len(proposal['warnings']) - 5} more warnings"
            )
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


@app.command("sources")
def sources_list(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List registered external sources for this repository."""
    repo_root = _resolve_repo(repo)
    service = SourceRegistryService(repo_root)
    entries = service.list_sources()

    if json_output:
        print(json.dumps(entries, indent=2, default=str))
    else:
        if not entries:
            console.print("[yellow]No sources registered.[/yellow]")
            return
        console.print(f"[bold]Registered sources ({len(entries)}):[/bold]")
        table = Table("Source ID", "Type", "Status", "File")
        for e in entries:
            table.add_row(
                e.get("source_id", "—"),
                e.get("source_type", "—"),
                e.get("status", "—"),
                e.get("file_path", "—") or "—",
            )
        console.print(table)


@app.command("source-show")
def source_show(
    source_id: str = typer.Argument(..., help="Source ID to show."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show details for a single registered source."""
    repo_root = _resolve_repo(repo)
    service = SourceRegistryService(repo_root)
    entry = service.get_latest_by_id(source_id)

    if entry is None:
        console.print(f"[red]Source not found: {source_id}[/red]")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(entry.to_dict(), indent=2, default=str))
    else:
        console.print(f"[bold]Source: {entry.source_id}[/bold]")
        console.print(f"  Type:   {entry.source_type}")
        console.print(f"  Status: {entry.status}")
        if entry.file_path:
            console.print(f"  File:   {entry.file_path}")
        if entry.file_hash:
            console.print(f"  Hash:   {entry.file_hash}")
        console.print(f"  Registered: {entry.registered_at}")
        if entry.metadata:
            for key, val in entry.metadata.items():
                console.print(f"  {key}: {val}")


@app.command()
@with_telemetry("infer-model")
def infer_model(
    profile: Path = typer.Argument(  # noqa: B008
        ..., help="Path to dataset profile JSON (e.g. generated/dataset_profiles/xxx.json)."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Infer draft model objects from a dataset profile and create a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if not profile.exists():
        console.print(f"[red]Profile not found: {profile}[/red]")
        raise typer.Exit(code=1)

    profile_text = profile.read_text(encoding="utf-8")
    try:
        profile_dict = json.loads(profile_text)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON in profile: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    dataset_id = profile.stem
    proposal = infer_model_from_profile(profile_dict, dataset_id=dataset_id)

    from modelops_core.patching.patch_validator import validate_patch_proposal

    validation_results = validate_patch_proposal(proposal)
    proposal["validation_status"] = (
        "valid" if not any(v.severity == "ERROR" for v in validation_results) else "invalid"
    )
    proposal["validation_results"] = [
        {k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v)
         for k, v in r.model_dump().items()}
        for r in validation_results
    ]

    from modelops_core.patching.patch_proposal_service import write_patch_proposal

    proposal_path = write_patch_proposal(proposal, model_path)

    if json_output:
        print(json.dumps(proposal, indent=2, default=str, sort_keys=True))
    else:
        console.print(f"[green]PatchProposal written to {proposal_path}[/green]")
        console.print(f"  ID: {proposal['id']}")
        console.print(f"  Operations: {len(proposal['operations'])}")
        console.print(f"  Validation: {proposal['validation_status']}")
        if proposal.get("assumptions"):
            console.print("[bold]Assumptions:[/bold]")
            for a in proposal["assumptions"]:
                console.print(f"  • {a}")
        if proposal.get("human_checks"):
            console.print("[bold]Human checks:[/bold]")
            for h in proposal["human_checks"]:
                console.print(f"  • {h}")


@app.command()
@with_telemetry("validate")
def validate(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    check_decisions: bool = typer.Option(
        False, "--check-decisions", help="Run extended Decision evidence validation."
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Exit with code 2 if any warnings exist."
    ),
) -> None:
    """Run deterministic validation on canonical files."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if not model_path.exists():
        console.print(f"[red]Model path does not exist: {model_path}[/red]")
        raise typer.Exit(code=1)

    files = scan_repository(model_path)
    record_object_count(len(files))
    parsed_objects = [parse_file(f) for f in files]
    config = load_repo_config(repo_root)
    enabled_packs = config.enabled_domain_packs if config else None
    summary = validate_objects(parsed_objects, enabled_packs, check_decisions=check_decisions)

    # Validate repo config schema version
    repo_config_issues = validate_repo_schema_version(
        config.model_dump() if config else None,
        source_file=str(repo_root / "modelops.config.yaml"),
    )
    for issue in repo_config_issues:
        from modelops_core.validation.result import ValidationResult, ValidationSeverity

        summary.results.append(
            ValidationResult(
                severity=ValidationSeverity(issue.severity),
                code=issue.code,
                message=issue.message,
                source_file=issue.source_file,
                suggested_fix=issue.suggested_fix,
            )
        )

    if json_output:
        result = {
            "is_valid": summary.is_valid,
            "error_count": summary.error_count,
            "warning_count": summary.warning_count,
            "info_count": summary.info_count,
            "results": [r.model_dump() for r in summary.results],
        }
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_validation_summary(summary)

    if not summary.is_valid:
        raise typer.Exit(code=1)

    if strict and summary.warning_count > 0:
        raise typer.Exit(code=2)


@app.command()
@with_telemetry("build-index")
def build_index(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    db: str | None = typer.Option(None, "--db", help="Path for SQLite DB output."),
    jsonl: bool = typer.Option(
        False,
        "--jsonl",
        help="Also export search_documents.jsonl and lineage_edges.jsonl.",
    ),
    allow_invalid: bool = typer.Option(
        False,
        "--allow-invalid",
        help="Build index even if validation fails.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be indexed without writing the database.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output raw JSON.",
    ),
) -> None:
    """Build SQLite index from canonical files."""
    repo_root = _resolve_repo(repo)
    db_path = Path(db).resolve() if db else None

    config = load_repo_config(repo_root)
    max_objects = config.resource_limits.max_index_objects if config else None

    try:
        summary = _build_index(
            repo_root=repo_root,
            db_path=db_path,
            allow_invalid=allow_invalid,
            export_jsonl=jsonl,
            max_objects=max_objects,
            dry_run=dry_run,
        )
    except (ValueError, ResourceLimitExceeded) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
            raise typer.Exit(code=1) from exc
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    record_object_count(len(scan_repository(resolve_model_path(repo_root))))

    if db_path is None:
        db_path = resolve_generated_path(repo_root) / "modelops.db"

    object_count = len(scan_repository(resolve_model_path(repo_root)))
    gen = resolve_generated_path(repo_root)
    jsonl_paths = []
    if jsonl:
        jsonl_paths = [
            str(gen / "search_documents.jsonl"),
            str(gen / "lineage_edges.jsonl"),
        ]

    if json_output:
        result = {
            "martenweave_version": __version__,
            "repo": str(repo_root),
            "db_path": str(db_path),
            "objects_count": object_count,
            "valid": summary.is_valid,
            "dry_run": dry_run,
            "jsonl_paths": jsonl_paths,
            "errors": [
                r.model_dump(mode="json")
                for r in summary.results
                if r.severity == "ERROR"
            ],
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    if dry_run:
        console.print("[bold]Dry-run: index preview[/bold]")
        console.print(f"  Objects: {object_count}")
        console.print(f"  Valid:   {summary.is_valid}")
        console.print(f"  Would write to: {db_path}")
        if jsonl:
            console.print(f"  Would export JSONL: {gen / 'search_documents.jsonl'}")
            console.print(f"  Would export JSONL: {gen / 'lineage_edges.jsonl'}")
        return

    console.print(f"[green]Index built at {db_path}[/green]")
    console.print(f"  Objects: {object_count}")
    console.print(f"  Valid:   {summary.is_valid}")

    if jsonl:
        console.print(f"  JSONL:   {gen / 'search_documents.jsonl'}")
        console.print(f"  JSONL:   {gen / 'lineage_edges.jsonl'}")


@app.command()
@with_telemetry("clean")
def clean(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be cleaned without deleting.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Remove generated artifacts (database, JSONL exports, dataset profiles)."""
    repo_root = _resolve_repo(repo)
    generated_path = resolve_generated_path(repo_root)

    # Safety: generated must be a subdirectory of repo_root
    try:
        generated_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        console.print(
            f"[red]Refusing to clean: {generated_path} is not a subdirectory of {repo_root}[/red]"
        )
        raise typer.Exit(code=1) from None

    targets: list[Path] = []
    if generated_path.exists():
        targets.extend(generated_path.glob("*.jsonl"))
        targets.extend(generated_path.glob("*.db"))
        targets.extend(generated_path.glob("*.db.tmp"))
        profile_dir = generated_path / "dataset_profiles"
        if profile_dir.exists():
            targets.extend(profile_dir.glob("*.json"))

    removed: list[str] = []
    skipped: list[str] = []

    for path in targets:
        if dry_run:
            skipped.append(str(path))
        else:
            try:
                path.unlink()
                removed.append(str(path))
            except OSError:
                skipped.append(str(path))

    if not dry_run:
        # Also try to remove empty dataset_profiles dir
        profile_dir = generated_path / "dataset_profiles"
        if profile_dir.exists() and not any(profile_dir.iterdir()):
            try:
                profile_dir.rmdir()
                removed.append(str(profile_dir))
            except OSError:
                skipped.append(str(profile_dir))

    if json_output:
        result = {
            "dry_run": dry_run,
            "generated_path": str(generated_path),
            "removed_count": len(removed),
            "skipped_count": len(skipped),
            "removed": removed,
            "skipped": skipped,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    if dry_run:
        console.print(f"[bold]Dry-run: would clean {len(skipped)} file(s)[/bold]")
        for path in skipped:
            console.print(f"  [dim]{path}[/dim]")
    else:
        console.print(f"[green]Cleaned {len(removed)} file(s)[/green]")
        for path in removed:
            console.print(f"  [dim]{path}[/dim]")
        if skipped:
            console.print(f"[yellow]Skipped {len(skipped)} file(s)[/yellow]")
            for path in skipped:
                console.print(f"  [dim]{path}[/dim]")


@app.command("index-fresh")
@with_telemetry("index-fresh")
def index_fresh(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Check whether the generated index is stale relative to canonical files."""
    repo_root = _resolve_repo(repo)
    report = check_index_freshness(repo_root)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "fresh": report.fresh,
            "db_path": str(report.db_path),
            "db_mtime": report.db_mtime.isoformat() if report.db_mtime else None,
            "newest_source_mtime": (
                report.newest_source_mtime.isoformat()
                if report.newest_source_mtime
                else None
            ),
            "reason": report.reason,
            "stale_sources": report.stale_sources,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    status_label = "[green]fresh[/green]" if report.fresh else "[red]stale[/red]"
    console.print(f"[bold]Index freshness: {status_label}[/bold]")
    console.print(f"  DB: {report.db_path}")
    if report.db_mtime:
        console.print(f"  DB mtime: {report.db_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    if report.newest_source_mtime:
        console.print(
            f"  Newest source: {report.newest_source_mtime.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    if report.reason:
        console.print(f"  Reason: {report.reason}")
    if report.stale_sources:
        console.print(f"  Stale sources: {len(report.stale_sources)} file(s)")
        for src in report.stale_sources[:10]:
            console.print(f"    [dim]{src}[/dim]")
        if len(report.stale_sources) > 10:
            console.print(f"    ... and {len(report.stale_sources) - 10} more")


@app.command()
@with_telemetry("health")
def health(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show repository health report."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_repository_health(db_path)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "object_count": report.object_count,
            "index_fresh": report.index_fresh,
            "coverage_gaps": {
                "objects_without_name": report.coverage_gaps.objects_without_name
                if report.coverage_gaps
                else 0,
                "objects_without_description": report.coverage_gaps.objects_without_description
                if report.coverage_gaps
                else 0,
            },
            "ownership_coverage": report.ownership_coverage.__dict__
            if report.ownership_coverage
            else {},
            "data_quality_coverage": report.data_quality_coverage.__dict__
            if report.data_quality_coverage
            else {},
            "coverage_gaps_list": [
                {
                    "object_id": g.object_id,
                    "object_type": g.object_type,
                    "object_name": g.object_name,
                    "gap_type": g.gap_type,
                    "suggested_action": g.suggested_action,
                }
                for g in report.coverage_gaps_list
            ],
            "type_counts": report.type_counts,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Repository Health[/bold]")
    console.print(f"  Total objects: {report.object_count}")
    console.print(f"  Index fresh:   {report.index_fresh}")
    if report.coverage_gaps:
        console.print(f"  Missing name:        {report.coverage_gaps.objects_without_name}")
        console.print(f"  Missing description: {report.coverage_gaps.objects_without_description}")
    if report.ownership_coverage:
        oc = report.ownership_coverage
        console.print(
            f"  Ownership coverage:  {oc.with_owner}/{oc.total_eligible} "
            f"({oc.percentage}%)"
        )
    if report.data_quality_coverage:
        dq = report.data_quality_coverage
        console.print("\n[bold]Data Quality Coverage[/bold]")
        console.print(
            f"  Attributes with rules:    "
            f"{dq.attributes_with_rules}/{dq.active_attributes} "
            f"({dq.attribute_rule_coverage_percent}%)"
        )
        console.print(
            f"  Endpoints with LoV:       "
            f"{dq.endpoints_with_lov}/{dq.active_field_endpoints} "
            f"({dq.endpoint_lov_coverage_percent}%)"
        )
        console.print(
            f"  Mappings with value map:  "
            f"{dq.mappings_with_value_mapping}/{dq.active_mappings} "
            f"({dq.mapping_logic_coverage_percent}%)"
        )
        console.print(
            f"  Datasets with profile:    "
            f"{dq.datasets_with_profile}/{dq.active_datasets} "
            f"({dq.dataset_profile_coverage_percent}%)"
        )
        console.print(
            f"  Active objects with owner: "
            f"{dq.objects_with_owner}/{dq.active_objects} ({dq.ownership_coverage_percent}%)"
        )
    if report.coverage_gaps_list:
        console.print(f"\n[bold]Coverage Gaps ({len(report.coverage_gaps_list)})[/bold]")
        table = Table("Object ID", "Type", "Gap", "Suggested Action")
        for g in report.coverage_gaps_list[:20]:
            table.add_row(
                g.object_id,
                g.object_type,
                g.gap_type,
                g.suggested_action,
            )
        console.print(table)
        if len(report.coverage_gaps_list) > 20:
            console.print(f"  ... and {len(report.coverage_gaps_list) - 20} more gaps")
    if report.type_counts:
        table = Table("Type", "Count")
        for t, c in sorted(report.type_counts.items()):
            table.add_row(t, str(c))
        console.print(table)


@app.command()
@with_telemetry("scorecard")
def scorecard(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show a compact governance scorecard with readiness metrics."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print(
            "[yellow]No index found. Run `modelops build-index` first.[/yellow]"
        )
        raise typer.Exit(code=1)

    report = generate_scorecard(db_path, repo_root)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "repo_name": report.repo_name,
            "generated_at": report.generated_at,
            "readiness_level": report.readiness_level,
            "object_count": report.object_count,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "target": m.target,
                    "status": m.status,
                    "explanation": m.explanation,
                    "suggested_action": m.suggested_action,
                }
                for m in report.metrics
            ],
            "gaps": [
                {
                    "object_id": g.object_id,
                    "object_type": g.object_type,
                    "gap_type": g.gap_type,
                    "suggested_action": g.suggested_action,
                }
                for g in report.gaps
            ],
            "summary": report.summary,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Scorecard: {report.repo_name}[/bold]")
    console.print(f"  Readiness: {report.readiness_level}")
    console.print(f"  Objects:   {report.object_count}")
    console.print(f"  Generated: {report.generated_at}")
    console.print("")

    table = Table("Metric", "Value", "Target", "Status", "Explanation")
    for m in report.metrics:
        status_color = {
            "pass": "[green]",
            "warning": "[yellow]",
            "fail": "[red]",
        }.get(m.status, "")
        table.add_row(
            m.name,
            str(m.value),
            str(m.target),
            f"{status_color}{m.status}[/]",
            m.explanation,
        )
    console.print(table)

    if report.gaps:
        console.print("")
        console.print(f"[bold]Top Gaps ({len(report.gaps)} shown)[/bold]")
        gap_table = Table("Object ID", "Type", "Gap", "Suggested Action")
        for g in report.gaps:
            gap_table.add_row(
                g.object_id or "—",
                g.object_type or "—",
                g.gap_type,
                g.suggested_action,
            )
        console.print(gap_table)

    console.print("")
    console.print(f"[italic]{report.summary}[/italic]")


@app.command("owners")
@with_telemetry("owners")
def owners(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show ownership coverage and steward workload."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print(
            "[yellow]No index found. Run `modelops build-index` first.[/yellow]"
        )
        raise typer.Exit(code=1)

    report = generate_ownership_report(db_path, repo_root)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "owners": [
                {
                    "owner_id": o.owner_id,
                    "role": o.role,
                    "object_count": o.object_count,
                    "object_types": o.object_types,
                }
                for o in report.owners
            ],
            "orphaned_objects": [
                {
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "object_name": o.object_name,
                }
                for o in report.orphaned_objects
            ],
            "coverage_percent": report.coverage_percent,
            "total_eligible": report.total_eligible,
            "total_with_owner": report.total_with_owner,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Ownership Report[/bold]")
    console.print(f"  Coverage: {report.coverage_percent}%")
    console.print(f"  Eligible objects: {report.total_eligible}")
    console.print(f"  With owner: {report.total_with_owner}")
    console.print(f"  Orphaned: {len(report.orphaned_objects)}")
    console.print("")

    if report.owners:
        table = Table("Owner", "Role", "Objects", "Type Breakdown")
        for o in report.owners:
            type_breakdown = ", ".join(
                f"{k}: {v}" for k, v in o.object_types.items()
            )
            table.add_row(o.owner_id, o.role, str(o.object_count), type_breakdown)
        console.print(table)
    else:
        console.print("[yellow]No owners found.[/yellow]")

    if report.orphaned_objects:
        console.print("")
        console.print("[bold]Orphaned Objects[/bold]")
        orphan_table = Table("Object ID", "Type", "Name")
        for o in report.orphaned_objects:
            orphan_table.add_row(o.object_id, o.object_type, o.object_name or "—")
        console.print(orphan_table)


@app.command()
def analyze(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Analyze model completeness, risk, and readiness."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_analysis_report(db_path, repo_root)

    if json_output:
        result = {
            "object_count": report.object_count,
            "type_counts": report.type_counts,
            "orphan_fields": {
                "field_endpoints_without_attribute": (
                    report.orphan_fields.field_endpoints_without_attribute
                    if report.orphan_fields
                    else []
                ),
            },
            "attribute_coverage": {
                "attributes_without_fields": (
                    report.attribute_coverage.attributes_without_fields
                    if report.attribute_coverage
                    else []
                ),
            },
            "ownership_gaps": report.ownership_gaps,
            "validation_coverage": report.validation_coverage,
            "lov_coverage": report.lov_coverage,
            "mapping_coverage": report.mapping_coverage,
            "risk_report": {
                "issue_count": report.risk_report.issue_count
                if report.risk_report
                else 0,
                "risk_count": report.risk_report.risk_count
                if report.risk_report
                else 0,
                "open_issues": report.risk_report.open_issues
                if report.risk_report
                else [],
            },
            "change_activity": {
                "event_count": report.change_activity.event_count
                if report.change_activity
                else 0,
                "recent_events": report.change_activity.recent_events
                if report.change_activity
                else [],
            },
            "lifecycle_summary": (
                {
                    "proposed": report.lifecycle_summary.proposed,
                    "draft": report.lifecycle_summary.draft,
                    "active": report.lifecycle_summary.active,
                    "under_review": report.lifecycle_summary.under_review,
                    "deprecated": report.lifecycle_summary.deprecated,
                    "retired": report.lifecycle_summary.retired,
                    "blocked": report.lifecycle_summary.blocked,
                    "planned": report.lifecycle_summary.planned,
                    "implemented": report.lifecycle_summary.implemented,
                    "other": report.lifecycle_summary.other,
                    "with_target_release": report.lifecycle_summary.with_target_release,
                    "with_roadmap_priority": report.lifecycle_summary.with_roadmap_priority,
                }
                if report.lifecycle_summary
                else {}
            ),
            "martenweave_version": __version__,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Model Analysis[/bold]")
    console.print(f"  Objects: {report.object_count}")

    if report.lifecycle_summary:
        ls = report.lifecycle_summary
        console.print("\n[bold]Lifecycle Summary[/bold]")
        counts = []
        if ls.proposed:
            counts.append(f"proposed: {ls.proposed}")
        if ls.draft:
            counts.append(f"draft: {ls.draft}")
        if ls.active:
            counts.append(f"active: {ls.active}")
        if ls.under_review:
            counts.append(f"under_review: {ls.under_review}")
        if ls.deprecated:
            counts.append(f"deprecated: {ls.deprecated}")
        if ls.retired:
            counts.append(f"retired: {ls.retired}")
        if ls.blocked:
            counts.append(f"blocked: {ls.blocked}")
        if ls.planned:
            counts.append(f"planned: {ls.planned}")
        if ls.implemented:
            counts.append(f"implemented: {ls.implemented}")
        if ls.other:
            counts.append(f"other: {ls.other}")
        if counts:
            console.print("  " + ", ".join(counts))
        if ls.with_target_release:
            console.print(f"  with_target_release: {ls.with_target_release}")
        if ls.with_roadmap_priority:
            console.print(f"  with_roadmap_priority: {ls.with_roadmap_priority}")

    if report.orphan_fields and report.orphan_fields.field_endpoints_without_attribute:
        console.print(
            f"\n[bold]Orphan Fields[/bold] "
            f"({len(report.orphan_fields.field_endpoints_without_attribute)})"
        )
        table = Table("Field Endpoint", "Name", "Reason")
        for item in report.orphan_fields.field_endpoints_without_attribute[:10]:
            table.add_row(
                item["object_id"],
                item.get("object_name") or "—",
                item["reason"],
            )
        console.print(table)

    if report.attribute_coverage and report.attribute_coverage.attributes_without_fields:
        console.print(
            f"\n[bold]Attributes without Fields[/bold] "
            f"({len(report.attribute_coverage.attributes_without_fields)})"
        )
        table = Table("Attribute", "Name", "Reason")
        for item in report.attribute_coverage.attributes_without_fields[:10]:
            table.add_row(
                item["object_id"],
                item.get("object_name") or "—",
                item["reason"],
            )
        console.print(table)

    if report.ownership_gaps:
        console.print(f"\n[bold]Ownership Gaps[/bold] ({len(report.ownership_gaps)})")
        table = Table("Object ID", "Type", "Name")
        for item in report.ownership_gaps[:10]:
            table.add_row(
                item["object_id"],
                item["object_type"],
                item.get("object_name") or "—",
            )
        console.print(table)

    if report.risk_report and (report.risk_report.issue_count or report.risk_report.risk_count):
        console.print(
            f"\n[bold]Risk Report[/bold]"
            f" — Issues: {report.risk_report.issue_count}"
            f", Risks: {report.risk_report.risk_count}"
        )

    if report.change_activity and report.change_activity.recent_events:
        console.print(
            f"\n[bold]Recent Activity[/bold] "
            f"({len(report.change_activity.recent_events)} of "
            f"{report.change_activity.event_count} events)"
        )
        table = Table("Event Type", "Timestamp", "Status", "Proposal")
        for item in report.change_activity.recent_events[:10]:
            table.add_row(
                item["event_type"],
                item["timestamp"],
                item["status"],
                item.get("proposal_id") or "—",
            )
        console.print(table)


@app.command("gap-report")
@with_telemetry("gap-report")
def gap_report(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate a consolidated gap summary report."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_gap_summary_report(db_path, repo_root)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "gaps_by_type": {
                key: {
                    "count": summary.count,
                    "sample_object_ids": summary.sample_object_ids,
                }
                for key, summary in report.gaps_by_type.items()
            },
            "total_gap_count": report.total_gap_count,
            "gap_score": report.gap_score,
            "top_objects": report.top_objects,
            "total_objects": report.total_objects,
            "sources_checked": report.sources_checked,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Gap Summary Report[/bold]")
    console.print(f"  Total objects: {report.total_objects}")
    console.print(f"  Total gaps: {report.total_gap_count}")
    console.print(f"  Gap score: {report.gap_score}")
    console.print(f"  Sources checked: {', '.join(report.sources_checked)}")

    if report.gaps_by_type:
        console.print("")
        table = Table("Gap Type", "Count", "Sample Objects")
        for gap_type, summary in report.gaps_by_type.items():
            samples = ", ".join(summary.sample_object_ids) or "—"
            table.add_row(gap_type, str(summary.count), samples)
        console.print(table)

    if report.top_objects:
        console.print("")
        console.print("[bold]Top affected objects[/bold]")
        for obj_id in report.top_objects:
            console.print(f"  {obj_id}")

    if not report.gaps_by_type:
        console.print("[green]No gaps found.[/green]")


@app.command("trace")
@with_telemetry("trace")
def trace(
    object_id: str = typer.Argument(..., help="Object ID to trace from."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    direction: str = typer.Option("both", "--direction", help="upstream, downstream, or both."),
    max_depth: int = typer.Option(5, "--max-depth", help="Maximum traversal depth."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Trace upstream and downstream relationships for an object."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    result = trace_object(db_path, object_id, max_depth=max_depth, direction=direction)

    if json_output:
        import json

        data = {
            "root_object_id": result.root_object_id,
            "root_object_type": result.root_object_type,
            "root_object_name": result.root_object_name,
            "nodes": [
                {
                    "object_id": n.object_id,
                    "object_type": n.object_type,
                    "object_name": n.object_name,
                    "source_file": n.source_file,
                    "depth": n.depth,
                }
                for n in result.nodes
            ],
            "edges": [
                {
                    "from_object_id": e.from_object_id,
                    "to_object_id": e.to_object_id,
                    "relationship_type": e.relationship_type,
                    "direction": e.direction,
                }
                for e in result.edges
            ],
        }
        print(json.dumps(data, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Trace: {object_id}[/bold]")
    if result.root_object_name:
        console.print(f"  Name: {result.root_object_name}")
    console.print(f"  Direction: {direction}")
    console.print(f"  Max depth: {max_depth}")

    if result.nodes:
        table = Table("ID", "Type", "Name", "Depth", "Direction")
        for n in result.nodes:
            dir_label = "upstream" if any(
                e.direction == "upstream" and e.to_object_id == n.object_id
                for e in result.edges
            ) else "downstream"
            table.add_row(
                n.object_id,
                n.object_type,
                n.object_name or "—",
                str(n.depth),
                dir_label,
            )
        console.print(table)
    else:
        console.print("  No related objects found.")


@app.command()
@with_telemetry("impact")
def impact(
    object_id: str = typer.Argument(..., help="Object ID to analyze."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    depth: int = typer.Option(2, "--depth", help="Maximum traversal depth."),
    fmt: str = typer.Option("table", "--format", help="Output format: table, markdown, json."),
    output: Path | None = typer.Option(  # noqa: B008
        None, "--output", help="Write report to file (default: stdout)."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    group_by: str | None = typer.Option(
        None,
        "--group-by",
        help="Group output by: type, direction, relationship.",
    ),
    direction: str = typer.Option("both", "--direction", help="upstream, downstream, or both."),
) -> None:
    """Generate impact report for an object."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_impact_report(db_path, object_id, max_depth=depth, direction=direction)

    # Legacy --json flag takes precedence
    if json_output or fmt.lower() == "json":
        result: dict[str, Any] = {
            "root_object_id": report.root_object_id,
            "root_object_type": report.root_object_type,
            "affected_objects": [
                {
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "direction": o.direction,
                    "depth": o.depth,
                    "relationship_type": o.relationship_type,
                    "relationship_class": o.relationship_class,
                }
                for o in report.affected_objects
            ],
        }
        if group_by:
            result["grouped"] = _build_impact_grouping(report, group_by)
        content = json.dumps(result, indent=2, default=str)
    elif fmt.lower() == "markdown":
        from modelops_core.impact.impact_report import render_impact_report_markdown

        content = render_impact_report_markdown(report)
    else:
        # Default table output via Rich (not serialisable to string)
        if output is not None:
            console.print(
                "[yellow]--output requires --format markdown or --format json.[/yellow]"
            )
            raise typer.Exit(code=1)
        console.print(f"[bold]Impact Report for {object_id}[/bold]")
        console.print(f"  Type: {report.root_object_type or 'Unknown'}")
        console.print(f"  Affected objects: {len(report.affected_objects)}")
        if report.affected_objects:
            if group_by == "type":
                for obj_type, objs in sorted(report.grouped_by_type.items()):
                    console.print(f"\n[bold]{obj_type} ({len(objs)})[/bold]")
                    table = Table("Object ID", "Direction", "Depth")
                    for o in objs:
                        table.add_row(o.object_id, o.direction or "—", str(o.depth))
                    console.print(table)
            elif group_by == "direction":
                for direction in ("downstream", "upstream"):
                    objs = [
                        o for o in report.affected_objects if o.direction == direction
                    ]
                    if not objs:
                        continue
                    console.print(f"\n[bold]{direction.capitalize()} ({len(objs)})[/bold]")
                    table = Table("Object ID", "Type", "Depth")
                    for o in objs:
                        table.add_row(o.object_id, o.object_type or "—", str(o.depth))
                    console.print(table)
            elif group_by == "relationship":
                rel_groups: dict[str, list[Any]] = {}
                for o in report.affected_objects:
                    rel_groups.setdefault(o.relationship_type or "Unknown", []).append(o)
                for rel_type, objs in sorted(rel_groups.items()):
                    console.print(f"\n[bold]{rel_type} ({len(objs)})[/bold]")
                    table = Table("Object ID", "Type", "Direction", "Depth")
                    for o in objs:
                        table.add_row(
                            o.object_id, o.object_type or "—", o.direction or "—", str(o.depth)
                        )
                    console.print(table)
            else:
                table = Table("Object ID", "Type", "Direction", "Depth")
                for o in report.affected_objects:
                    table.add_row(
                        o.object_id, o.object_type or "—", o.direction or "—", str(o.depth)
                    )
                console.print(table)
        return

    if output is not None:
        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Report written to {output}[/green]")
    else:
        print(content)


@app.command()
@with_telemetry("propose-patch")
def propose_patch(
    note_file: Path = typer.Option(  # noqa: B008
        ..., "--from", help="Path to note file."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Create a PatchProposal from a structured note."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if not note_file.exists():
        console.print(f"[red]Note file not found: {note_file}[/red]")
        raise typer.Exit(code=1)

    note = note_file.read_text(encoding="utf-8")

    from modelops_core.ai.patch_proposal_service import build_patch_proposal_from_note

    result = build_patch_proposal_from_note(note, repo_root=repo_root)

    proposal = result.get("proposal")
    if proposal is None:
        if json_output:
            print(json.dumps(result, indent=2, default=str))
        else:
            console.print("[red]No proposal generated.[/red]")
        raise typer.Exit(code=1)

    path = write_patch_proposal(proposal, model_path)

    if json_output:
        print(json.dumps(result, indent=2, default=str))
        return

    if not result.get("is_safe"):
        console.print("[yellow]Proposal generated but failed validation.[/yellow]")

    console.print(f"[green]Patch proposal written to {path}[/green]")
    console.print(f"  ID:    {proposal['id']}")
    console.print(f"  Ops:   {len(proposal.get('operations', []))}")
    console.print(f"  Safe:  {result.get('is_safe')}")

    assumptions = result.get("assumptions", [])
    if assumptions:
        console.print("[bold]Assumptions:[/bold]")
        for a in assumptions:
            console.print(f"  • {a}")

    human_checks = result.get("human_checks", [])
    if human_checks:
        console.print("[bold]Human checks:[/bold]")
        for h in human_checks:
            console.print(f"  • {h}")

    service = AuditEventService(repo_root)
    changed_object_ids = [
        op.get("object_id", "") for op in proposal.get("operations", [])
    ]
    service.emit(
        create_audit_event(
            event_type="proposal_created",
            actor="system",
            status="success",
            command="propose-patch",
            proposal_id=proposal.get("id"),
            changed_object_ids=changed_object_ids,
            validation_status="valid" if result.get("is_safe") else "invalid",
            outputs={
                "proposal_id": proposal.get("id"),
                "operations_count": len(proposal.get("operations", [])),
                "is_safe": result.get("is_safe"),
            },
        )
    )


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
    proposal: str | None = typer.Option(
        None, "--proposal", help="PatchProposal ID to draft from."
    ),
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

    sources_selected = sum(
        bool(x) for x in (change_request, proposal, from_validation)
    )
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
        }
        print(json.dumps(result, indent=2, default=str))
    else:
        console.print(f"[green]ChangeRequest created: {path}[/green]")
        console.print(f"  ID:     {cr_id}")
        console.print(f"  Status: {status}")
        console.print(f"  Title:  {title}")

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
) -> None:
    """Update the status of a ChangeRequest."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    try:
        cr = update_change_request_status(model_path, cr_id, status)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(cr, indent=2, default=str))
    else:
        console.print(f"[green]ChangeRequest {cr_id} updated to '{status}'[/green]")

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
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Approve a ChangeRequest."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    try:
        cr = approve_change_request(model_path, cr_id, approver)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(cr, indent=2, default=str))
    else:
        console.print(f"[green]ChangeRequest {cr_id} approved by {approver}[/green]")
        if cr.get("approvals"):
            console.print(f"  Approvals: {len(cr['approvals'])}")

    service = AuditEventService(repo_root)
    service.emit(
        create_audit_event(
            event_type="change_request_approved",
            actor=approver,
            status="success",
            command="change-request approve",
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
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Reject a ChangeRequest."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    try:
        cr = reject_change_request(model_path, cr_id, approver)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(cr, indent=2, default=str))
    else:
        console.print(f"[yellow]ChangeRequest {cr_id} rejected by {approver}[/yellow]")

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
    proposal: str | None = typer.Option(
        None, "--proposal", help="PatchProposal ID to preview."
    ),
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
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
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
        decisions.append({
            "id": row[0],
            "status": row[1],
            "name": row[2],
            "title": row[3],
            "domain": row[4],
            "source_file": row[5],
        })

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
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
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
        console.print(
            "[yellow]No index found. Run `modelops build-index` first.[/yellow]"
        )
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
                {"category": c.category, "count": c.count}
                for c in report.category_breakdown
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
proposal_app = typer.Typer(
    name="proposal",
    help="Review and apply PatchProposals.",
)
app.add_typer(proposal_app, name="proposal")


@proposal_app.command("list")
def proposal_list(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    stale: bool = typer.Option(False, "--stale", help="Show only expired proposals."),
    status: str | None = typer.Option(
        None, "--status", help="Filter by status: pending_review, accepted, rejected, applied."
    ),
    reviewer: str | None = typer.Option(
        None, "--reviewer", help="Filter by reviewer identity."
    ),
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
    from datetime import UTC, datetime

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
        proposals.append({
            "id": fm.get("id", f.stem),
            "status": fm.get("status", ""),
            "applied": bool(fm.get("applied_at")),
            "expires_at": expires_at,
            "expired": is_expired,
            "reviewer": fm.get("reviewer"),
            "reviewed_at": fm.get("reviewed_at"),
        })

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

    if json_output:
        print(json.dumps(fm, indent=2, default=str))
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

    operations = fm.get("operations", [])
    if operations:
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
    reviewer: str | None = typer.Option(None, "--reviewer", help="Identity of the reviewer."),
    notes: str | None = typer.Option(None, "--notes", help="Reviewer notes."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Accept a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    transition_patch_proposal_status(
        proposal_path, "accepted", reviewer=reviewer, reviewer_notes=notes
    )

    if json_output:
        print(json.dumps({"proposal_id": proposal_id, "status": "accepted"}, indent=2))
        raise typer.Exit()

    console.print(f"[green]PatchProposal {proposal_id} accepted.[/green]")


@proposal_app.command("reject")
@with_telemetry("proposal-reject")
def proposal_reject(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    reviewer: str | None = typer.Option(None, "--reviewer", help="Identity of the reviewer."),
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

    transition_patch_proposal_status(
        proposal_path, "rejected", reviewer=reviewer, reviewer_notes=notes, rejection_reason=reason
    )

    if json_output:
        print(json.dumps({"proposal_id": proposal_id, "status": "rejected"}, indent=2))
        raise typer.Exit()

    console.print(f"[red]PatchProposal {proposal_id} rejected.[/red]")


@proposal_app.command("validate")
def proposal_validate(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run deterministic validation on a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}

    from modelops_core.patching.patch_validator import validate_patch_proposal

    results = validate_patch_proposal(fm)
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
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    operations = fm.get("operations", [])

    report = generate_proposal_impact_report(
        db_path, proposal_id, operations, max_depth=max_depth
    )

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
                if (
                    file_parsed.frontmatter
                    and file_parsed.frontmatter.get("id") == object_id
                ):
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
                if (
                    file_parsed.frontmatter
                    and file_parsed.frontmatter.get("id") == object_id
                ):
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

    console.print(f"[bold]Diff for {proposal_id}[/bold]")
    if not diffs:
        console.print("  No operations to diff.")
        raise typer.Exit()

    for d in diffs:
        op_type = d["op"]
        obj_id = d.get("object_id", "—")
        if op_type in ("create_object", "add_object"):
            console.print(f"\n  [green]{op_type}[/green] → {obj_id}")
            console.print(f"    New object: {d.get('after')}")
        elif op_type == "update_object":
            console.print(f"\n  [yellow]{op_type}[/yellow] → {obj_id}")
            console.print(f"    {d.get('target_path', '')}: {d.get('before')} → {d.get('after')}")
        elif op_type == "delete_object":
            console.print(f"\n  [red]{op_type}[/red] → {obj_id}")
            console.print(f"    Would remove: {d.get('before', {}).get('type', 'object')}")
        else:
            console.print(f"\n  [dim]{op_type}[/dim] → {obj_id}")
            console.print(f"    {d.get('reason')}")


@proposal_app.command("apply")
@with_telemetry("proposal-apply")
def proposal_apply(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview changes without applying."
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Apply the proposal to canonical files."
    ),
    force: bool = typer.Option(
        False, "--force", help="Skip approval gate (not recommended)."
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
    if risk.requires_approval and not force:
        approved_cr = find_approved_cr_for_proposal(model_path, proposal_id)
        if approved_cr is None:
            if json_output:
                print(json.dumps({
                    "error": "Approval required",
                    "proposal_id": proposal_id,
                    "risk_level": risk.risk_level,
                    "risk_reasons": risk.risk_reasons,
                }))
            else:
                console.print(
                    f"[red]Approval required for {proposal_id}. "
                    f"Risk level: {risk.risk_level}[/red]"
                )
                for reason in risk.risk_reasons:
                    console.print(f"  • {reason}")
                console.print(
                    "[yellow]Create an approved ChangeRequest linking to this proposal, "
                    "or use --force to override.[/yellow]"
                )
            raise typer.Exit(code=1)
        if not json_output:
            console.print(
                f"[green]Approved via ChangeRequest {approved_cr.get('id')}[/green]"
            )

    try:
        result = apply_patch_proposal(model_path, proposal_id)
    except (ValueError, FileNotFoundError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc), "proposal_id": proposal_id}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps({
            "proposal_id": proposal_id,
            "applied": True,
            "changed_files": result.changed_files,
            "audit_event_written": result.audit_event_written,
            "index_rebuilt": result.index_rebuilt,
        }, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[green]Applied {proposal_id}[/green]")
    console.print(f"  Changed files: {len(result.changed_files)}")
    for f in result.changed_files:
        console.print(f"    {f}")
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
    from datetime import UTC, datetime, timedelta

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

            proposals.append({
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
            })

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
                f"  Oldest stale: {oldest_stale['id']} "
                f"(expires_at: {oldest_stale['expires_at']})"
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
        table = Table(
            "ID", "Status", "Risk", "Ops", "Affected", "Stale", "Reviewer"
        )
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
    from datetime import UTC, datetime

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
        impact_risk = compute_proposal_risk(
            operations, model_path, impact_report=impact_report
        )
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
            "note": "No index found. Run `modelops build-index` first.",
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
        console.print(
            f"  Affected objects: {len(impact_section.get('affected_objects', []))}"
        )
        console.print(
            f"  Operations analyzed: {len(impact_section.get('operations', []))}"
        )
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


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(8000, "--port", help="Bind port."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
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

    uvicorn.run(api_app, host=host, port=port)


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
            "[red]The MCP server requires the 'mcp' package. "
            "Install it with: pip install mcp[/red]"
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
    if input_path.is_dir():
        proposal = import_model_sheet_csv(input_path, model_path)
    elif input_path.suffix.lower() == ".xlsx":
        proposal = import_model_sheet_xlsx(
            input_path, model_path, max_rows=limits.max_import_rows
        )
    else:
        console.print(
            "[red]Input must be a CSV directory or an .xlsx workbook.[/red]"
        )
        raise typer.Exit(code=1)

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


@app.command("export-model")
@with_telemetry("export-model")
def export_model(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    fmt: str = typer.Option("csv", "--format", help="Export format: csv, xlsx, or json."),
    business_review: bool = typer.Option(
        False, "--business-review", help="Styled XLSX for non-technical review."
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
            written = export_model_jsonl(
                model_path, max_objects=limits.max_export_objects
            )
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
            path = export_model_xlsx(
                model_path,
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
        console.print(
            f"  Period: {report.date_range['from']} to {report.date_range['to']}"
        )

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
        help="Output directory for generated docs.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate static Markdown documentation from the model index."""
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

    files = sorted(f.name for f in result.iterdir() if f.suffix == ".md")

    if json_output:
        print(
            json.dumps(
                {"output_dir": str(result), "files": files},
                indent=2,
                default=str,
            )
        )
        raise typer.Exit()

    console.print(f"[bold]Documentation generated[/bold] at {result}")
    console.print(f"  {len(files)} Markdown file(s):")
    for name in files:
        console.print(f"    - {name}")


@app.command("config-guard")
def config_guard(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Scan repository for secrets and configuration guardrail issues."""
    repo_root = _resolve_repo(repo)

    results = run_all_checks(repo_root)

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
                }
                for i in issues
            ]
        print(json.dumps(output, indent=2, default=str))
        if has_blocking_issues(results):
            raise typer.Exit(code=1)
        raise typer.Exit()

    total_issues = sum(len(v) for v in results.values())
    error_count = sum(
        1 for issues in results.values() for i in issues if i.severity == "ERROR"
    )
    warning_count = sum(
        1 for issues in results.values() for i in issues if i.severity == "WARNING"
    )

    console.print("[bold]Configuration Guardrails[/bold]")
    console.print(f"  Checks: {len(results)}")
    console.print(f"  Issues: {total_issues} ({error_count} errors, {warning_count} warnings)")

    for check_name, issues in results.items():
        if not issues:
            continue
        console.print(f"\n[bold]{check_name}[/bold] ({len(issues)} issues)")
        table = Table("Severity", "Code", "File", "Line", "Message")
        for i in issues:
            table.add_row(
                i.severity,
                i.code,
                i.file_path or "—",
                str(i.line_number) if i.line_number else "—",
                i.message,
            )
        console.print(table)

    if has_blocking_issues(results):
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
            console.print(
                f"  {obj.object_id} ({obj.object_type})"
            )
            table = Table("Field", "Old Value", "New Value")
            for fc in obj.field_changes:
                old_str = str(fc.old_value) if fc.old_value is not None else "—"
                new_str = str(fc.new_value) if fc.new_value is not None else "—"
                table.add_row(fc.field, old_str, new_str)
            console.print(table)


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query (keywords)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    object_type: str | None = typer.Option(
        None, "--type", help="Filter by object type."
    ),
    status: str | None = typer.Option(
        None, "--status", help="Filter by status."
    ),
    domain: str | None = typer.Option(
        None, "--domain", help="Filter by domain ID."
    ),
    tags: list[str] | None = typer.Option(  # noqa: B008
        None, "--tag", help="Filter by tag (repeatable)."
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum results."),
    offset: int = typer.Option(0, "--offset", help="Skip first N results."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Search indexed objects by keyword."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

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

    if json_output:
        output = {
            "results": [
                {
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
                for r in results
            ],
            "total_count": paginated.total_count,
        }
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
    object_type: str | None = typer.Option(
        None, "--type", help="Filter by object type."
    ),
    status: str | None = typer.Option(
        None, "--status", help="Filter by status."
    ),
    domain: str | None = typer.Option(
        None, "--domain", help="Filter by domain ID."
    ),
    name_like: str | None = typer.Option(
        None, "--name-like", help="Substring match on name."
    ),
    tags: list[str] | None = typer.Option(  # noqa: B008
        None, "--tag", help="Filter by tag (repeatable)."
    ),
    owner: str | None = typer.Option(
        None, "--owner", help="Filter by owner/steward/approver ID."
    ),
    sap_table: str | None = typer.Option(
        None, "--sap-table", help="Filter by SAP table name."
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum results."),
    offset: int = typer.Option(0, "--offset", help="Skip first N results."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run a structured query over the generated index."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

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
        False, "--dry-run", help="Preview changes without writing files."
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

        new_fm = migrate_object(fm)
        if new_fm is None:
            skipped_count += 1
            continue

        migrated_count += 1
        old_version = fm.get("schema_version", "none")
        migrated_files.append({
            "file": file_path.name,
            "old_version": old_version,
            "new_version": CURRENT_SCHEMA_VERSION,
        })
        if dry_run:
            if not json_output:
                console.print(
                    f"[yellow]Would migrate[/yellow] {file_path.name} "
                    f"({old_version} → {CURRENT_SCHEMA_VERSION})"
                )
            continue

        # Rewrite file with new frontmatter
        from modelops_core.repository import rewrite_frontmatter

        rewrite_frontmatter(file_path, new_fm)
        if not json_output:
            console.print(
                f"[green]Migrated[/green] {file_path.name} "
                f"({old_version} → {CURRENT_SCHEMA_VERSION})"
            )

    # Update repo config schema_version
    config_path = repo_root / "modelops.config.yaml"
    if not config_path.exists():
        config_path = repo_root / "modelops.config.yml"
    if config_path.exists():
        config = load_repo_config(repo_root)
        if config and config.schema_version != CURRENT_SCHEMA_VERSION:
            config_updated = True
            if dry_run:
                if not json_output:
                    console.print(
                        f"[yellow]Would update[/yellow] {config_path.name} "
                        f"({config.schema_version} → {CURRENT_SCHEMA_VERSION})"
                    )
            else:
                import yaml

                raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                raw["schema_version"] = CURRENT_SCHEMA_VERSION
                config_path.write_text(
                    yaml.safe_dump(raw, default_flow_style=False, sort_keys=False),
                    encoding="utf-8",
                )
                if not json_output:
                    console.print(
                        f"[green]Updated[/green] {config_path.name} "
                        f"({config.schema_version} → {CURRENT_SCHEMA_VERSION})"
                    )

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
                },
                indent=2,
                default=str,
            )
        )
        raise typer.Exit()

    console.print(
        f"\n[bold]Migration complete[/bold] — "
        f"{migrated_count} migrated, {skipped_count} skipped"
    )


if __name__ == "__main__":
    app()

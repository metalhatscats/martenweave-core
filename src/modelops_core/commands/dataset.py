from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.table import Table

from modelops_core.commands._common import (
    app,
    console,
    _check_and_warn_stale_index,
    _resolve_repo,
)
from modelops_core.config import (
    load_resource_limits,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.connectors.google_drive import GoogleDriveConnector
from modelops_core.gaps import detect_dataset_gaps
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
from modelops_core.imports.privacy import (
    DatasetPrivacyPolicy,
    apply_privacy_to_profile,
    apply_privacy_to_workbook,
    detect_high_risk_columns,
)
from modelops_core.index.dataset_profile_sync import link_dataset_profile_to_index
from modelops_core.reports.audit_service import AuditEventService, create_audit_event
from modelops_core.reports.source_registry_service import (
    SourceRegistryService,
    register_dataset_source,
)
from modelops_core.telemetry import with_telemetry


@app.command()
def profile_dataset(
    file: Path = typer.Argument(..., help="Path to CSV or XLSX file."),  # noqa: B008
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    dataset_id: str | None = typer.Option(
        None,
        "--dataset-id",
        help=(
            "Dataset object ID to link the profile to. "
            "Defaults to the file stem; falls back to matching by Dataset name."
        ),
    ),
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
    effective_dataset_id = dataset_id or file.stem
    suffix = file.suffix.lower()

    if suffix == ".csv":
        raw_profile = profile_csv(
            file,
            dataset_id=effective_dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )
    elif suffix in {".xlsx", ".xls"}:
        raw_profile = profile_xlsx(
            file,
            dataset_id=effective_dataset_id,
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
    output_path = profile_dir / f"{effective_dataset_id}.json"
    output_path.write_text(
        json.dumps(profile_dict, indent=2, default=str, sort_keys=True),
        encoding="utf-8",
    )

    # Register source
    src_service = SourceRegistryService(repo_root)
    register_dataset_source(
        src_service,
        dataset_id=effective_dataset_id,
        file_path=file,
        file_hash=profile_dict.get("file_hash", ""),
        row_count=profile_dict.get("row_count", 0),
        column_count=profile_dict.get("column_count", 0),
    )

    # Keep the disposable index in sync so health/scorecard reflect the profile.
    linked_id = link_dataset_profile_to_index(
        repo_root,
        dataset_id=effective_dataset_id,
        profile_path=output_path,
        file_name=file.name,
    )
    if linked_id is None and not json_output:
        console.print(
            "[yellow]No matching Dataset object found in the index. "
            "Run `martenweave build-index` if the index is missing or outdated.[/yellow]"
        )

    if json_output:
        print(json.dumps(profile_dict, indent=2, default=str, sort_keys=True))
    else:
        console.print(f"[green]Profile saved to {output_path}[/green]")
        if hasattr(profile, "sheet_names"):
            console.print(f"  Sheets: {len(profile.sheets)}")
            for sheet in profile.sheets:
                console.print(
                    f"    {sheet.sheet_name}: {sheet.row_count} rows, {sheet.column_count} cols"
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
    check_model: bool = typer.Option(False, "--check-model", help="Also check model-side gaps."),
    write: bool = typer.Option(
        False, "--write", help="Persist Issue or PatchProposal files created from gaps."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview intended changes without writing files."
    ),
) -> None:
    """Detect dataset-to-model gaps by comparing dataset columns against FieldEndpoints."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    model_path = resolve_model_path(repo_root)

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    stale = _check_and_warn_stale_index(repo_root, json_output)

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

    # Build report(s): single profile or workbook with multiple sheets
    from modelops_core.gaps.gap_detection import DatasetGapReport

    sheet_reports: list[DatasetGapReport] = []
    if isinstance(profile, WorkbookProfile):
        for sheet in profile.sheets:
            sheet_report = detect_dataset_gaps(sheet, db_path, sheet_name=sheet.sheet_name)
            # Annotate sheet name on matches for output
            for m in sheet_report.matches:
                m.sheet_name = sheet.sheet_name
            for g in sheet_report.gaps:
                g.sheet_name = sheet.sheet_name
            sheet_reports.append(sheet_report)
    else:
        sheet_reports.append(detect_dataset_gaps(profile, db_path))

    # Combine matches, gaps, coverage
    all_matches: list[Any] = []
    all_dataset_gaps: list[Any] = []
    total_columns = 0
    matched_columns = 0
    unmatched_columns = 0
    duplicate_columns = 0
    for sr in sheet_reports:
        all_matches.extend(sr.matches)
        all_dataset_gaps.extend(sr.gaps)
        if sr.coverage:
            total_columns += sr.coverage.total_columns
            matched_columns += sr.coverage.matched_columns
            unmatched_columns += sr.coverage.unmatched_columns
            duplicate_columns += sr.coverage.duplicate_columns

    match_rate = round(matched_columns / total_columns, 4) if total_columns > 0 else 0.0

    model_gaps: list[Any] = []
    if check_model:
        from modelops_core.gaps.gap_detection import detect_model_gaps

        model_gaps = detect_model_gaps(db_path)

    all_gaps = all_dataset_gaps + model_gaps

    coverage_data = {
        "total_columns": total_columns,
        "matched_columns": matched_columns,
        "unmatched_columns": unmatched_columns,
        "duplicate_columns": duplicate_columns,
        "match_rate": match_rate,
    }

    if json_output:
        result = {
            "stale_index_warning": stale,
            "dataset_id": dataset_id,
            "coverage": coverage_data,
            "matches": [
                {
                    "column_name": m.column_name,
                    "matched_endpoint_id": m.matched_endpoint_id,
                    "match_type": m.match_type,
                    "sheet_name": m.sheet_name,
                }
                for m in all_matches
            ],
            "gaps": [
                {
                    "gap_id": g.gap_id,
                    "column_name": g.column_name,
                    "gap_code": g.gap_code,
                    "severity": g.severity,
                    "message": g.message,
                    "evidence_ids": g.evidence_ids,
                    "source_dataset_metadata": g.source_dataset_metadata,
                    "recommended_proposal_op": g.recommended_proposal_op,
                    "sheet_name": g.sheet_name,
                }
                for g in all_gaps
            ],
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("\n[bold]Coverage[/bold]")
    console.print(f"  Total columns:      {total_columns}")
    console.print(f"  Matched columns:    {matched_columns}")
    console.print(f"  Unmatched columns:  {unmatched_columns}")
    console.print(f"  Duplicate columns:  {duplicate_columns}")
    console.print(f"  Match rate:         {match_rate:.1%}")

    if all_gaps:
        console.print(f"\n[bold]Gaps found for {dataset_id} ({len(all_gaps)})[/bold]")
        table = Table("Column", "Code", "Severity", "Message", "Sheet")
        for g in all_gaps:
            table.add_row(
                g.column_name,
                g.gap_code,
                g.severity,
                g.message,
                g.sheet_name or "—",
            )
        console.print(table)
    else:
        console.print(f"[green]No gaps found for {dataset_id}[/green]")

    if all_matches:
        console.print(f"\n[bold]Matches ({len(all_matches)})[/bold]")
        match_table = Table("Column", "Endpoint", "Match Type", "Sheet")
        for m in all_matches:
            match_table.add_row(
                m.column_name,
                m.matched_endpoint_id,
                m.match_type,
                m.sheet_name or "—",
            )
        console.print(match_table)

    if dry_run and write:
        console.print("[red]Cannot use both --dry-run and --write.[/red]")
        raise typer.Exit(code=1)

    if (create_issues and all_gaps) or (promote_to_proposal and all_dataset_gaps):
        if not write and not dry_run:
            console.print(
                "\n[yellow]Preview only: mutation flags were given but --write was not passed. "
                "Use --write to persist these changes.[/yellow]"
            )
            if create_issues and all_gaps:
                console.print(f"  Would create {len(all_gaps)} Issue(s):")
                for idx, g in enumerate(all_gaps, start=1):
                    issue_id = g.gap_id or f"ISSUE-GAP-{dataset_id.upper()}-{idx:03d}"
                    console.print(f"    {issue_id}.md")
            if promote_to_proposal and all_dataset_gaps:
                console.print(
                    f"  Would promote {len(all_dataset_gaps)} gap(s) to a draft PatchProposal."
                )
            raise typer.Exit()

    created_files: list[str] = []
    if create_issues and all_gaps:
        if dry_run:
            console.print(f"\n[yellow]Dry-run: would create {len(all_gaps)} Issue(s).[/yellow]")
        else:
            issues_dir = model_path / "issues"
            issues_dir.mkdir(parents=True, exist_ok=True)
            for idx, g in enumerate(all_gaps, start=1):
                issue_id = g.gap_id or f"ISSUE-GAP-{dataset_id.upper()}-{idx:03d}"
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
                    "source_gap_id": g.gap_id,
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
                created_files.append(str(issue_path.resolve()))
                console.print(f"[green]Created {issue_path.name}[/green]")

    if promote_to_proposal and all_dataset_gaps:
        if dry_run:
            console.print(
                f"\n[yellow]Dry-run: would promote {len(all_dataset_gaps)} gap(s) "
                "to a draft PatchProposal.[/yellow]"
            )
        else:
            from modelops_core.gaps.gap_detection import (
                DatasetGapReport,
                promote_gaps_to_proposal,
            )

            combined_report = DatasetGapReport(
                dataset_id=dataset_id,
                matches=all_matches,
                gaps=all_dataset_gaps,
            )
            proposal_path = promote_gaps_to_proposal(combined_report, model_path)
            created_files.append(str(proposal_path.resolve()))
            console.print(f"[green]Created PatchProposal {proposal_path.name}[/green]")

    if created_files:
        service = AuditEventService(repo_root)
        event = create_audit_event(
            event_type="gap_mutation_applied",
            actor="system",
            status="success",
            command=("gaps --create-issues" if create_issues else "gaps --promote-to-proposal"),
            changed_object_ids=[Path(f).stem for f in created_files],
            outputs={"created_files": created_files},
        )
        service.emit(event)
        console.print("  Audit event written")


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
                    f"    {sheet.sheet_name}: {sheet.row_count} rows, {sheet.column_count} cols"
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
            console.print(f"    ... and {len(proposal['warnings']) - 5} more warnings")
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
        {
            k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v)
            for k, v in r.model_dump().items()
        }
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

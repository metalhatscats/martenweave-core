from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.table import Table

from modelops_core.commands._common import _resolve_repo, app, console
from modelops_core.config import (
    load_repo_config,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.docs.static_doc_generator import generate_static_docs
from modelops_core.guardrails.config_guard import (
    ConfigGuardMode,
    has_blocking_issues,
    run_all_checks,
)
from modelops_core.index import build_index as _build_index
from modelops_core.reports.audit_service import (
    AuditEventService,
    filter_audit_events,
)
from modelops_core.reports.diagnostics_bundle import write_diagnostics_bundle
from modelops_core.reports.usage_report_service import generate_usage_report
from modelops_core.repository import parse_file, scan_repository
from modelops_core.schemas.migration import can_migrate_from, migrate_object, needs_migration
from modelops_core.schemas.versioning import CURRENT_SCHEMA_VERSION
from modelops_core.telemetry import with_telemetry
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

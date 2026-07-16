from __future__ import annotations

import json
from pathlib import Path

import typer

from modelops_core import __version__
from modelops_core.commands._common import (
    _print_validation_summary,
    _resolve_repo,
    app,
    console,
)
from modelops_core.config import (
    load_repo_config,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.index import build_index as _build_index
from modelops_core.reports.index_freshness import check_index_freshness
from modelops_core.repository import parse_file, scan_repository
from modelops_core.schemas.versioning import validate_repo_schema_version
from modelops_core.telemetry import record_object_count, with_telemetry
from modelops_core.validation import validate_objects


@app.command()
@with_telemetry("validate")
def validate(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    check_decisions: bool = typer.Option(
        False, "--check-decisions", help="Run extended Decision evidence validation."
    ),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 2 if any warnings exist."),
    suppress_methodology_warnings: bool = typer.Option(
        False,
        "--suppress-methodology-warnings",
        help=(
            "Suppress methodology warnings "
            "(FLAT_MODEL_STRUCTURE, FIELD_ENDPOINT_MISSING_ENRICHMENT, etc.)."
        ),
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

    if suppress_methodology_warnings:
        from modelops_core.validation.result import METHODOLOGY_WARNING_CODES

        summary.results = [r for r in summary.results if r.code not in METHODOLOGY_WARNING_CODES]

    if json_output:
        result = {
            "is_valid": summary.is_valid,
            "error_count": summary.error_count,
            "warning_count": summary.warning_count,
            "info_count": summary.info_count,
            "summary_by_code": summary.summary_by_code,
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
            "errors": [r.model_dump(mode="json") for r in summary.results if r.severity == "ERROR"],
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
                report.newest_source_mtime.isoformat() if report.newest_source_mtime else None
            ),
            "reason": report.reason,
            "stale_sources": report.stale_sources,
            "stored_source_hash": report.stored_source_hash,
            "current_source_hash": report.current_source_hash,
            "hash_mismatch": report.hash_mismatch,
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
    if report.stored_source_hash and report.current_source_hash:
        console.print(f"  Stored hash:   {report.stored_source_hash}")
        console.print(f"  Current hash:  {report.current_source_hash}")
    if report.reason:
        console.print(f"  Reason: {report.reason}")
    if report.stale_sources:
        if report.fresh:
            # Content hash still matches; mtime differences are diagnostic only.
            console.print(
                f"  Sources newer than index: {len(report.stale_sources)} file(s) "
                "(content hash matches; no rebuild needed)"
            )
            for src in report.stale_sources[:10]:
                console.print(f"    [dim]{src}[/dim]")
            if len(report.stale_sources) > 10:
                console.print(f"    ... and {len(report.stale_sources) - 10} more")
        else:
            console.print(f"  Stale sources: {len(report.stale_sources)} file(s)")
            for src in report.stale_sources[:10]:
                console.print(f"    [dim]{src}[/dim]")
            if len(report.stale_sources) > 10:
                console.print(f"    ... and {len(report.stale_sources) - 10} more")

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from modelops_core.commands._common import app, console, _resolve_repo
from modelops_core.config import resolve_model_path
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.run import (
    generate_dataset_readiness_report,
    generate_migration_assessment,
    write_readiness_report,
)
from modelops_core.pilot.preflight import run_preflight
from modelops_core.telemetry import with_telemetry


run_app = typer.Typer(
    name="run",
    help="Run end-to-end model governance workflows.",
)
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

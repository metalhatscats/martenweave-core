"""Typer CLI for ModelOps MDM Core."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from modelops_core import __version__
from modelops_core.config import (
    RepoConfig,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.imports import (
    dataset_profile_to_dict,
    infer_model_from_profile,
    profile_csv,
    profile_xlsx,
)
from modelops_core.index import build_index as _build_index
from modelops_core.patching.patch_proposal_service import (
    write_patch_proposal,
)
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation import validate_objects

app = typer.Typer(
    name="modelops",
    help="ModelOps MDM Core — backend-first model registry CLI.",
    no_args_is_help=True,
)
console = Console()


def _resolve_repo(repo: str | None) -> Path:
    if repo is None:
        return Path.cwd()
    return Path(repo).resolve()


def _print_validation_summary(summary: Any) -> None:
    console.print("[bold]Validation Results:[/bold]")
    console.print(f"  Errors:   {summary.error_count}")
    console.print(f"  Warnings: {summary.warning_count}")
    console.print(f"  Info:     {summary.info_count}")
    console.print(f"  Valid:    {summary.is_valid}")
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
        console.print(table)


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
) -> None:
    pass


@app.command()
def init(
    path: Path = typer.Argument(  # noqa: B008
        ..., help="Directory to scaffold the model repository."
    ),
    name: str = typer.Option("My Model Repository", help="Repository name."),
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
        yaml.safe_dump(config.model_dump(), default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    # Create a minimal example domain object
    example_md = model_dir / "DOMAIN-EXAMPLE.md"
    example_md.write_text(
        "---\n"
        "id: DOMAIN-EXAMPLE\n"
        "type: MasterDataDomain\n"
        "status: draft\n"
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
) -> None:
    """Profile a dataset file (CSV or XLSX) and save the profile."""
    repo_root = _resolve_repo(repo)
    generated_path = resolve_generated_path(repo_root)
    profile_dir = generated_path / "dataset_profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)

    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(code=1)

    dataset_id = file.stem
    suffix = file.suffix.lower()

    if suffix == ".csv":
        profile = profile_csv(file, dataset_id=dataset_id)
    elif suffix in {".xlsx", ".xls"}:
        profile = profile_xlsx(file, dataset_id=dataset_id)
    else:
        console.print(f"[red]Unsupported file format: {suffix}[/red]")
        raise typer.Exit(code=1)

    profile_dict = dataset_profile_to_dict(profile)
    output_path = profile_dir / f"{dataset_id}.json"
    output_path.write_text(
        json.dumps(profile_dict, indent=2, default=str, sort_keys=True),
        encoding="utf-8",
    )

    if json_output:
        console.print(json.dumps(profile_dict, indent=2, default=str, sort_keys=True))
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
            console.print(f"  Status: {'OK' if profile.status.success else 'TRUNCATED'}")


@app.command()
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
        console.print(json.dumps(proposal, indent=2, default=str, sort_keys=True))
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
def validate(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run deterministic validation on canonical files."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if not model_path.exists():
        console.print(f"[red]Model path does not exist: {model_path}[/red]")
        raise typer.Exit(code=1)

    files = scan_repository(model_path)
    parsed_objects = [parse_file(f) for f in files]
    summary = validate_objects(parsed_objects)

    if json_output:
        result = {
            "is_valid": summary.is_valid,
            "error_count": summary.error_count,
            "warning_count": summary.warning_count,
            "info_count": summary.info_count,
            "results": [r.model_dump() for r in summary.results],
        }
        console.print(json.dumps(result, indent=2, default=str))
    else:
        _print_validation_summary(summary)

    if not summary.is_valid:
        raise typer.Exit(code=1)


@app.command()
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
) -> None:
    """Build SQLite index from canonical files."""
    repo_root = _resolve_repo(repo)
    db_path = Path(db).resolve() if db else None

    try:
        summary = _build_index(
            repo_root=repo_root,
            db_path=db_path,
            allow_invalid=allow_invalid,
            export_jsonl=jsonl,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if db_path is None:
        db_path = resolve_generated_path(repo_root) / "modelops.db"

    console.print(f"[green]Index built at {db_path}[/green]")
    console.print(f"  Objects: {len(scan_repository(resolve_model_path(repo_root)))}")
    console.print(f"  Valid:   {summary.is_valid}")

    if jsonl:
        gen = resolve_generated_path(repo_root)
        console.print(f"  JSONL:   {gen / 'search_documents.jsonl'}")
        console.print(f"  JSONL:   {gen / 'lineage_edges.jsonl'}")


@app.command()
def health(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Show repository health report."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_repository_health(db_path)
    console.print("[bold]Repository Health[/bold]")
    console.print(f"  Total objects: {report.object_count}")
    console.print(f"  Index fresh:   {report.index_fresh}")
    if report.coverage_gaps:
        console.print(f"  Missing name:        {report.coverage_gaps.objects_without_name}")
        console.print(f"  Missing description: {report.coverage_gaps.objects_without_description}")
    if report.type_counts:
        table = Table("Type", "Count")
        for t, c in sorted(report.type_counts.items()):
            table.add_row(t, str(c))
        console.print(table)


@app.command()
def impact(
    object_id: str = typer.Argument(..., help="Object ID to analyze."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    depth: int = typer.Option(2, "--depth", help="Maximum traversal depth."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate impact report for an object."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_impact_report(db_path, object_id, max_depth=depth)

    if json_output:
        result = {
            "root_object_id": report.root_object_id,
            "root_object_type": report.root_object_type,
            "affected_objects": [
                {
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "direction": o.direction,
                    "depth": o.depth,
                }
                for o in report.affected_objects
            ],
        }
        console.print(json.dumps(result, indent=2, default=str))
    else:
        console.print(f"[bold]Impact Report for {object_id}[/bold]")
        console.print(f"  Type: {report.root_object_type or 'Unknown'}")
        console.print(f"  Affected objects: {len(report.affected_objects)}")
        if report.affected_objects:
            table = Table("Object ID", "Type", "Direction", "Depth")
            for o in report.affected_objects:
                table.add_row(o.object_id, o.object_type or "—", o.direction or "—", str(o.depth))
            console.print(table)


@app.command()
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

    result = build_patch_proposal_from_note(note)

    if json_output:
        console.print(json.dumps(result, indent=2, default=str))
        return

    if not result.get("is_safe"):
        console.print("[yellow]Proposal generated but failed validation.[/yellow]")

    proposal = result.get("proposal")
    if proposal is None:
        console.print("[red]No proposal generated.[/red]")
        raise typer.Exit(code=1)

    path = write_patch_proposal(proposal, model_path)
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


if __name__ == "__main__":
    app()

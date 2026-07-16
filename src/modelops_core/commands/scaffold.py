from __future__ import annotations

import json
from pathlib import Path

import typer

from modelops_core.commands._common import app, console
from modelops_core.pilot.bootstrap import BootstrapAssessmentError, bootstrap_assessment


@app.command()
def init(
    path: Path = typer.Argument(  # noqa: B008
        ..., help="Directory to scaffold the model repository."
    ),
    name: str = typer.Option("My Model Repository", help="Repository name."),
    template: str | None = typer.Option(
        None,
        "--template",
        help=(
            "Model spine template to copy "
            "(business_partner, generic_large_object, "
            "sap_bp_customer_migration, ams_field_dictionary)."
        ),
    ),
) -> None:
    """Scaffold a new model repository."""
    from modelops_core.repository.scaffold import init_repository

    try:
        target = init_repository(path, name=name, template=template)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Initialized model repository at {target}[/green]")
    if template:
        console.print(f"  Template: {template}")
    console.print(f"  Config:   {target / 'modelops.config.yaml'}")
    console.print(f"  Model:    {target / 'model'}")
    console.print(f"  Generated: {target / 'generated'}")


@app.command("bootstrap-assessment")
def bootstrap_assessment_command(
    mapping: Path = typer.Option(..., "--mapping", help="SAP mapping workbook (.xlsx)."),  # noqa: B008
    name: str = typer.Option(..., "--name", help="Name for the new pilot repository."),  # noqa: B008
    out_repo: Path = typer.Option(  # noqa: B008
        ..., "--out-repo", help="Empty directory for the new local pilot repository."
    ),
    dataset: Path | None = typer.Option(  # noqa: B008
        None, "--dataset", help="Optional local CSV/XLSX sample dataset to profile."
    ),
    json_output: bool = typer.Option(  # noqa: B008
        False, "--json", help="Output bootstrap metadata as JSON."
    ),
) -> None:
    """Start a pilot from a workbook while keeping all inferred model content proposal-only."""
    try:
        result = bootstrap_assessment(mapping, name, out_repo, dataset)
    except BootstrapAssessmentError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    payload = {
        "repo": str(result.repo_root),
        "proposal_id": result.proposal_id,
        "proposal": str(result.proposal_path),
        "report_json": str(result.report_json_path),
        "report_markdown": str(result.report_markdown_path),
    }
    if json_output:
        print(json.dumps(payload, indent=2))
        return
    console.print(f"[green]Pilot repository created:[/green] {result.repo_root}")
    console.print(f"  Draft proposal: {result.proposal_path}")
    console.print(f"  Bootstrap report: {result.report_markdown_path}")
    console.print("  No inferred canonical object has been applied.")

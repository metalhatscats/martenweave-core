from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.table import Table

from modelops_core.commands._common import console
from modelops_core.domain_packs.catalog import (
    build_builtin_domain_pack,
    diff_domain_pack_repos,
    generated_artifact_exists,
    resolve_domain_pack_reference,
    validate_domain_pack_repo,
)

domain_pack_app = typer.Typer(
    name="domain-pack",
    help="Build, validate, and diff built-in domain-pack reference repositories.",
)


@domain_pack_app.command("build")
def build_domain_pack(
    pack_id: str = typer.Argument(..., help="Built-in domain-pack identifier."),  # noqa: B008
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Empty directory where the built domain-pack repo will be written."
    ),
    include_generated: bool = typer.Option(
        False,
        "--include-generated",
        help="Copy disposable generated artifacts from the built-in reference repo.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Build a local domain-pack repository from a built-in synthetic reference pack."""
    try:
        result = build_builtin_domain_pack(pack_id, out, include_generated=include_generated)
    except ValueError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    payload = {
        "pack_id": result.pack.pack_id,
        "title": result.pack.title,
        "description": result.pack.description,
        "source_repo": str(result.pack.source_repo),
        "output_repo": str(result.output_repo),
        "include_generated": result.include_generated,
        "generated_artifacts_copied": generated_artifact_exists(result.output_repo),
    }
    if json_output:
        print(json.dumps(payload, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[green]Domain pack built:[/green] {result.output_repo}")
    console.print(f"  Pack: {result.pack.pack_id}")
    console.print(f"  Source: {result.pack.source_repo}")
    console.print(f"  Include generated: {'yes' if include_generated else 'no'}")


@domain_pack_app.command("validate")
def validate_domain_pack(
    pack: str = typer.Argument(  # noqa: B008
        ..., help="Built-in domain-pack identifier or local domain-pack repository path."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Validate a domain-pack repository with its enabled domain-pack rules."""
    try:
        pack_id, repo_root = resolve_domain_pack_reference(pack)
        result = validate_domain_pack_repo(repo_root)
    except ValueError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    payload = {
        "pack_id": pack_id,
        "repo_root": str(result.repo_root),
        "object_count": result.object_count,
        "enabled_domain_packs": result.enabled_domain_packs,
        "is_valid": result.summary.is_valid,
        "error_count": result.summary.error_count,
        "warning_count": result.summary.warning_count,
        "info_count": result.summary.info_count,
        "summary_by_code": result.summary.summary_by_code,
    }
    if json_output:
        print(json.dumps(payload, indent=2, default=str))
        raise typer.Exit()

    status_color = "green" if result.summary.is_valid else "red"
    console.print(
        f"[bold]Domain-pack validation:[/bold] [{status_color}]"
        f"{'valid' if result.summary.is_valid else 'invalid'}[/{status_color}]"
    )
    console.print(f"  Repository: {result.repo_root}")
    console.print(f"  Objects: {result.object_count}")
    console.print(
        "  Enabled packs: "
        + (", ".join(result.enabled_domain_packs) if result.enabled_domain_packs else "none")
    )
    console.print(f"  Errors: {result.summary.error_count}")
    console.print(f"  Warnings: {result.summary.warning_count}")
    if result.summary.summary_by_code:
        table = Table("Code", "Severity", "Count")
        for code, info in result.summary.summary_by_code.items():
            table.add_row(code, info["severity"], str(info["count"]))
        console.print(table)
    if not result.summary.is_valid:
        raise typer.Exit(code=1)


@domain_pack_app.command("diff")
def diff_domain_pack(
    old: str = typer.Argument(  # noqa: B008
        ..., help="Base built-in domain-pack identifier or local repository path."
    ),
    new: str = typer.Argument(  # noqa: B008
        ..., help="Head built-in domain-pack identifier or local repository path."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Compare two domain-pack repositories and show canonical model differences."""
    try:
        old_pack_id, old_repo = resolve_domain_pack_reference(old)
        new_pack_id, new_repo = resolve_domain_pack_reference(new)
        result = diff_domain_pack_repos(old_repo, new_repo)
    except ValueError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    payload = {
        "old_pack_id": old_pack_id,
        "new_pack_id": new_pack_id,
        "old_repo": str(old_repo),
        "new_repo": str(new_repo),
        "has_changes": result.has_changes,
        "base_count": result.base_count,
        "head_count": result.head_count,
        "added": result.added,
        "removed": result.removed,
        "changed": [
            {
                "object_id": changed.object_id,
                "object_type": changed.object_type,
                "object_name": changed.object_name,
                "field_changes": [
                    {
                        "field": field.field,
                        "old_value": field.old_value,
                        "new_value": field.new_value,
                    }
                    for field in changed.field_changes
                ],
            }
            for changed in result.changed
        ],
    }
    if json_output:
        print(json.dumps(payload, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Domain-pack diff[/bold]")
    console.print(f"  Base repo: {old_repo}")
    console.print(f"  Head repo: {new_repo}")
    console.print(f"  Base objects: {result.base_count}")
    console.print(f"  Head objects: {result.head_count}")
    if not result.has_changes:
        console.print("[green]No differences found.[/green]")
        raise typer.Exit()

    if result.added:
        console.print(f"[bold green]Added:[/bold green] {len(result.added)}")
    if result.removed:
        console.print(f"[bold red]Removed:[/bold red] {len(result.removed)}")
    if result.changed:
        console.print(f"[bold yellow]Changed:[/bold yellow] {len(result.changed)}")

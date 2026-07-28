from __future__ import annotations

import json
from pathlib import Path

import typer

from modelops_core.commands._common import _resolve_repo, console
from modelops_core.package_service import create_package, inspect_package, verify_package

package_app = typer.Typer(name="package", help="Create and verify portable local model packages.")
_OUTPUT_OPTION = typer.Option(..., "--output", help="Output package archive path.")


@package_app.command("create")
def create(repo: str | None = typer.Option(None, "--repo"), output: Path = _OUTPUT_OPTION) -> None:
    try:
        manifest = create_package(_resolve_repo(repo), output.resolve())
    except (ValueError, OSError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Created package:[/green] {output}")
    console.print(f"  Canonical files: {len(manifest['files'])}")


@package_app.command("inspect")
def inspect(package: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        manifest = inspect_package(package)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    if json_output:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        console.print(f"Package: {manifest['repository']['name']}")
        console.print(f"Format: {manifest['package_format_version']}")
        console.print(f"Files: {len(manifest['files'])}")


@package_app.command("verify")
def verify(package: Path) -> None:
    try:
        result = verify_package(package)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Package verified:[/green] {result['file_count']} files")

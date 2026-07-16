from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from modelops_core.commands._common import (
    _build_impact_grouping,
    _check_and_warn_stale_index,
    _resolve_repo,
    app,
    console,
)
from modelops_core.config import resolve_generated_path
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.telemetry import with_telemetry
from modelops_core.trace import trace_object


@app.command("trace")
@with_telemetry("trace")
def trace(
    object_id: str = typer.Argument(..., help="Object ID to trace from."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    direction: str = typer.Option("both", "--direction", help="upstream, downstream, or both."),
    max_depth: int = typer.Option(5, "--max-depth", help="Maximum traversal depth."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    relationship_class: str | None = typer.Option(
        None,
        "--relationship-class",
        help="Filter by relationship class (e.g. core_dependency, mapping, governance).",
    ),
) -> None:
    """Trace upstream and downstream relationships for an object."""
    import json

    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    stale = _check_and_warn_stale_index(repo_root, json_output)

    result = trace_object(
        db_path,
        object_id,
        max_depth=max_depth,
        direction=direction,
        relationship_class=relationship_class,
    )

    if result.root_object_type is None:
        if json_output:
            print(
                json.dumps(
                    {
                        "stale_index_warning": stale,
                        "error": f"Object not found: {object_id}",
                    },
                    indent=2,
                    default=str,
                )
            )
        else:
            console.print(f"[red]Object not found: {object_id}[/red]")
        raise typer.Exit(code=1)

    if json_output:
        data = {
            "stale_index_warning": stale,
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
                    "relationship_class": e.relationship_class,
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
            dir_label = (
                "upstream"
                if any(
                    e.direction == "upstream" and e.to_object_id == n.object_id
                    for e in result.edges
                )
                else "downstream"
            )
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
    relationship_class: str | None = typer.Option(
        None,
        "--relationship-class",
        help="Filter by relationship class (e.g. core_dependency, mapping, governance).",
    ),
) -> None:
    """Generate impact report for an object."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    stale = _check_and_warn_stale_index(repo_root, json_output or fmt.lower() == "json")

    report = generate_impact_report(
        db_path,
        object_id,
        max_depth=depth,
        direction=direction,
        relationship_class=relationship_class,
    )

    if report.root_object_type is None:
        if json_output or fmt.lower() == "json":
            content = json.dumps(
                {"stale_index_warning": stale, "error": f"Object not found: {object_id}"},
                indent=2,
                default=str,
            )
            if output is not None:
                output.write_text(content, encoding="utf-8")
                console.print(f"[green]Report written to {output}[/green]")
            else:
                print(content)
        else:
            console.print(f"[red]Object not found: {object_id}[/red]")
        raise typer.Exit(code=1)

    # Legacy --json flag takes precedence
    if json_output or fmt.lower() == "json":
        result: dict[str, Any] = {
            "stale_index_warning": stale,
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
            console.print("[yellow]--output requires --format markdown or --format json.[/yellow]")
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
                    objs = [o for o in report.affected_objects if o.direction == direction]
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

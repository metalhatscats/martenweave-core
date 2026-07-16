from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from modelops_core import __version__
from modelops_core.reports.index_freshness import check_index_freshness

app = typer.Typer(
    help="Martenweave Core — backend-first model governance pipeline CLI.",
    no_args_is_help=True,
)
_base_console = Console()


class _ConsoleProxy:
    """Stable import-time handle whose target can be rebound at runtime.

    Commands import ``console`` from this module. Because rebinding a module
    global does not affect existing references held by importing modules, we
    use a proxy object whose internal target is updated when CLI options such
    as ``--quiet`` or ``--no-color`` are processed.
    """

    def __init__(self, target: Console) -> None:
        self._target = target

    def print(self, *args: Any, **kwargs: Any) -> None:
        self._target.print(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


console = _ConsoleProxy(_base_console)

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


def _check_and_warn_stale_index(repo_root: Path, json_output: bool = False) -> bool:
    """Check index freshness and emit a warning when stale.

    Returns True if the index is stale, False if fresh.
    For human output, prints a yellow warning when stale.
    For JSON output, callers should include the returned value.
    """
    freshness = check_index_freshness(repo_root)
    is_stale = not freshness.fresh
    if is_stale and not json_output:
        console.print(
            "[yellow]Warning: index may be stale. "
            "Run `martenweave build-index` to refresh.[/yellow]"
        )
    return is_stale


def _build_impact_grouping(report: Any, group_by: str) -> dict[str, Any]:
    from modelops_core.impact.impact_report import ImpactReport

    assert isinstance(report, ImpactReport)
    if group_by == "type":
        return {
            obj_type: [
                {"object_id": o.object_id, "direction": o.direction, "depth": o.depth} for o in objs
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
    if summary.summary_by_code:
        target.print("\n[bold]By code:[/bold]")
        code_table = Table("Code", "Severity", "Count")
        for code, info in summary.summary_by_code.items():
            code_table.add_row(code, info["severity"], str(info["count"]))
        target.print(code_table)
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
        console.print(f"martenweave-core {__version__}")
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
    global _quiet, _no_color, _unwrapped_console
    _quiet = quiet
    _no_color = no_color

    if no_color:
        _unwrapped_console = Console(color_system=None)
    else:
        _unwrapped_console = _base_console

    if quiet:
        console._target = _QuietConsole(_unwrapped_console)
    else:
        console._target = _unwrapped_console

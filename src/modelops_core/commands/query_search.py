from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from modelops_core.commands._common import (
    _check_and_warn_stale_index,
    app,
    console,
    _resolve_repo,
)
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.diff import diff_repositories
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.index.query_service import (
    PaginatedResult,
    SearchResult,
    query_objects,
    search_objects,
    semantic_search_objects,
)


@app.command("diff")
def diff(
    base: Path = typer.Argument(  # noqa: B008
        ..., help="Path to base model repository."
    ),
    head: Path = typer.Argument(  # noqa: B008
        ..., help="Path to head model repository."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Compare two model repositories and show differences."""
    base_model = resolve_model_path(base.resolve())
    head_model = resolve_model_path(head.resolve())

    if not base_model.exists():
        console.print(f"[red]Base model path does not exist: {base_model}[/red]")
        raise typer.Exit(code=1)
    if not head_model.exists():
        console.print(f"[red]Head model path does not exist: {head_model}[/red]")
        raise typer.Exit(code=1)

    result = diff_repositories(base_model, head_model)

    if json_output:
        output = {
            "has_changes": result.has_changes,
            "base_count": result.base_count,
            "head_count": result.head_count,
            "added": result.added,
            "removed": result.removed,
            "changed": [
                {
                    "object_id": c.object_id,
                    "object_type": c.object_type,
                    "object_name": c.object_name,
                    "field_changes": [
                        {
                            "field": fc.field,
                            "old_value": fc.old_value,
                            "new_value": fc.new_value,
                        }
                        for fc in c.field_changes
                    ],
                }
                for c in result.changed
            ],
        }
        print(json.dumps(output, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Model Diff[/bold]")
    console.print(f"  Base objects: {result.base_count}")
    console.print(f"  Head objects: {result.head_count}")

    if not result.has_changes:
        console.print("[green]No differences found.[/green]")
        raise typer.Exit()

    if result.added:
        console.print(f"\n[bold green]Added ({len(result.added)})[/bold green]")
        table = Table("Object ID", "Type", "Name")
        for obj in result.added:
            table.add_row(
                obj["object_id"],
                obj.get("object_type") or "—",
                obj.get("object_name") or "—",
            )
        console.print(table)

    if result.removed:
        console.print(f"\n[bold red]Removed ({len(result.removed)})[/bold red]")
        table = Table("Object ID", "Type", "Name")
        for obj in result.removed:
            table.add_row(
                obj["object_id"],
                obj.get("object_type") or "—",
                obj.get("object_name") or "—",
            )
        console.print(table)

    if result.changed:
        console.print(f"\n[bold yellow]Changed ({len(result.changed)})[/bold yellow]")
        for obj in result.changed:
            console.print(f"  {obj.object_id} ({obj.object_type})")
            table = Table("Field", "Old Value", "New Value")
            for fc in obj.field_changes:
                old_str = str(fc.old_value) if fc.old_value is not None else "—"
                new_str = str(fc.new_value) if fc.new_value is not None else "—"
                table.add_row(fc.field, old_str, new_str)
            console.print(table)


def _filter_semantic_ids(
    db_path: Path,
    semantic_results: list[Any],
    object_type: str | None,
    status: str | None,
    domain: str | None,
    tags: list[str] | None,
) -> set[str]:
    """Return semantic result IDs that pass the same filters as keyword search."""
    if not semantic_results:
        return set()
    object_ids = [r.object_id for r in semantic_results]
    conditions: list[str] = [f"id IN ({', '.join('?' for _ in object_ids)})"]
    params: list[Any] = list(object_ids)
    if object_type:
        conditions.append("type = ?")
        params.append(object_type)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if domain:
        conditions.append("domain = ?")
        params.append(domain)
    if tags:
        placeholders = ", ".join("?" for _ in tags)
        conditions.append(f"id IN (SELECT object_id FROM tags WHERE tag IN ({placeholders}))")
        params.extend(tags)
    sql = "SELECT id FROM objects WHERE " + " AND ".join(conditions)
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return {row[0] for row in rows}


def _load_search_results_for_ids(db_path: Path, object_ids: set[str]) -> dict[str, SearchResult]:
    """Load SearchResult metadata for a set of object IDs."""
    if not object_ids:
        return {}
    placeholders = ", ".join("?" for _ in object_ids)
    sql = f"SELECT * FROM objects WHERE id IN ({placeholders})"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, list(object_ids)).fetchall()
    finally:
        conn.close()
    return {
        row["id"]: SearchResult(
            object_id=row["id"],
            object_type=row["type"],
            status=row["status"],
            name=row["name"],
            title=row["title"],
            domain=row["domain"],
            description=row["description"],
            source_file=row["source_file"],
        )
        for row in rows
    }


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query (keywords)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    object_type: str | None = typer.Option(None, "--type", help="Filter by object type."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    domain: str | None = typer.Option(None, "--domain", help="Filter by domain ID."),
    tags: list[str] | None = typer.Option(  # noqa: B008
        None, "--tag", help="Filter by tag (repeatable)."
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum results."),
    offset: int = typer.Option(0, "--offset", help="Skip first N results."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
    semantic: bool = typer.Option(
        False,
        "--semantic",
        help=(
            "Rerank keyword results by local semantic similarity and surface "
            "additional semantically related objects."
        ),
    ),
    semantic_expand: bool = typer.Option(
        False, "--semantic-expand", help="Expand query with one-hop related object terms."
    ),
) -> None:
    """Search indexed objects by keyword."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    stale = _check_and_warn_stale_index(repo_root, json_output)

    paginated = search_objects(
        db_path=db_path,
        query=query,
        object_type=object_type,
        status=status,
        domain=domain,
        tags=tags,
        limit=limit,
        offset=offset,
    )
    results = paginated.results
    total_count = paginated.total_count
    semantic_error: str | None = None

    if semantic:
        keyword_by_id = {r.object_id: r for r in results}
        keyword_ids = set(keyword_by_id)
        # Search the full semantic index so related objects are surfaced even when
        # they do not contain the literal query terms.
        try:
            semantic_results = semantic_search_objects(
                db_path=db_path,
                query=query,
                candidate_ids=None,
                expand=semantic_expand,
                limit=limit + offset,
                expand_candidate_ids=keyword_ids,
                repo_root=repo_root,
            )
            allowed_ids = _filter_semantic_ids(
                db_path,
                semantic_results,
                object_type=object_type,
                status=status,
                domain=domain,
                tags=tags,
            )
            semantic_by_id = {
                r.object_id: r for r in semantic_results if r.object_id in allowed_ids
            }

            # Fetch metadata for semantic results that keyword search missed.
            semantic_only_ids = set(semantic_by_id) - keyword_ids
            metadata = _load_search_results_for_ids(db_path, semantic_only_ids)

            merged: dict[str, SearchResult] = {}
            for obj_id, sr in semantic_by_id.items():
                result = keyword_by_id.get(obj_id) or metadata.get(obj_id)
                if result is None:
                    continue
                result.score = sr.semantic_score
                result.matched_fields = result.matched_fields + [
                    "semantic:" + t for t in sr.matched_terms
                ]
                merged[obj_id] = result

            # Include keyword-only results with a zero semantic score so the ranking
            # stays on a single float scale and keyword-only matches do not outrank
            # real semantic matches.
            for r in results:
                if r.object_id not in merged:
                    r.score = 0.0
                    merged[r.object_id] = r

            results = sorted(merged.values(), key=lambda r: r.score, reverse=True)
            results = results[offset : offset + limit]
            total_count = len(merged)
            paginated = PaginatedResult(results=results, total_count=total_count)
        except ResourceLimitExceeded as exc:
            semantic_error = str(exc)
            if not json_output:
                console.print(f"[yellow]Semantic search disabled: {semantic_error}[/yellow]")
        except Exception as exc:  # noqa: BLE001
            semantic_error = f"Semantic search failed: {exc}"
            if not json_output:
                console.print(f"[yellow]{semantic_error}[/yellow]")

    if json_output:
        output: dict[str, Any] = {
            "stale_index_warning": stale,
            "results": [],
            "total_count": total_count,
        }
        if semantic and semantic_error is not None:
            output["semantic_error"] = semantic_error
        for r in results:
            result_obj = {
                "object_id": r.object_id,
                "object_type": r.object_type,
                "status": r.status,
                "name": r.name,
                "title": r.title,
                "domain": r.domain,
                "source_file": r.source_file,
                "score": r.score,
                "matched_fields": r.matched_fields,
            }
            if semantic:
                result_obj["semantic_score"] = r.score
                result_obj["semantic_matched_terms"] = [
                    f.removeprefix("semantic:")
                    for f in r.matched_fields
                    if f.startswith("semantic:")
                ]
            output["results"].append(result_obj)
        print(json.dumps(output, indent=2, default=str))
        raise typer.Exit()

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        raise typer.Exit()

    console.print(f"[bold]Search Results ({paginated.total_count})[/bold]")
    table = Table("ID", "Type", "Name", "Status", "Score", "Matched")
    for r in results:
        table.add_row(
            r.object_id,
            r.object_type,
            r.name or r.title or "—",
            r.status,
            str(r.score),
            ", ".join(r.matched_fields) or "—",
        )
    console.print(table)


@app.command("query")
def query(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    object_type: str | None = typer.Option(None, "--type", help="Filter by object type."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    domain: str | None = typer.Option(None, "--domain", help="Filter by domain ID."),
    name_like: str | None = typer.Option(None, "--name-like", help="Substring match on name."),
    tags: list[str] | None = typer.Option(  # noqa: B008
        None, "--tag", help="Filter by tag (repeatable)."
    ),
    owner: str | None = typer.Option(None, "--owner", help="Filter by owner/steward/approver ID."),
    sap_table: str | None = typer.Option(None, "--sap-table", help="Filter by SAP table name."),
    limit: int = typer.Option(50, "--limit", help="Maximum results."),
    offset: int = typer.Option(0, "--offset", help="Skip first N results."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run a structured query over the generated index."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    stale = _check_and_warn_stale_index(repo_root, json_output)

    paginated = query_objects(
        db_path=db_path,
        object_type=object_type,
        status=status,
        domain=domain,
        name_like=name_like,
        tags=tags,
        owner=owner,
        sap_table=sap_table,
        limit=limit,
        offset=offset,
    )
    results = paginated.results

    if json_output:
        output = {
            "stale_index_warning": stale,
            "results": [
                {
                    "object_id": r.object_id,
                    "object_type": r.object_type,
                    "status": r.status,
                    "name": r.name,
                    "title": r.title,
                    "domain": r.domain,
                    "source_file": r.source_file,
                }
                for r in results
            ],
            "total_count": paginated.total_count,
        }
        print(json.dumps(output, indent=2, default=str))
        raise typer.Exit()

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        raise typer.Exit()

    console.print(f"[bold]Query Results ({paginated.total_count})[/bold]")
    table = Table("ID", "Type", "Name", "Status", "Domain")
    for r in results:
        table.add_row(
            r.object_id,
            r.object_type,
            r.name or r.title or "—",
            r.status,
            r.domain or "—",
        )
    console.print(table)

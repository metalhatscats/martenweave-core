from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from modelops_core.bundle import create_git_bundle
from modelops_core.commands._common import app, console, _resolve_repo
from modelops_core.config import (
    load_resource_limits,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.exports import export_model_csv, export_model_jsonl, export_model_xlsx
from modelops_core.exports.github_publish_service import (
    publish_issue_from_draft,
    publish_pr_from_bundle,
)
from modelops_core.exports.google_sheets_export import export_to_google_sheets
from modelops_core.exports.schema_export_service import export_schemas, write_schema_export
from modelops_core.imports.model_sheet_import_service import (
    SpreadsheetImportError,
    import_model_sheet_csv,
    import_model_sheet_xlsx,
)
from modelops_core.patching.patch_proposal_service import render_patch_proposal_markdown
from modelops_core.reports.audit_service import AuditEventService, create_audit_event
from modelops_core.reports.source_registry_service import (
    SourceRegistryService,
    register_import_source,
)
from modelops_core.telemetry import with_telemetry


@app.command("import-model-sheet")
def import_model_sheet(
    input_path: Path = typer.Argument(  # noqa: B008
        ..., help="Path to CSV folder or XLSX workbook."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Import spreadsheet edits and generate a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if not input_path.exists():
        console.print(f"[red]Input not found: {input_path}[/red]")
        raise typer.Exit(code=1)

    limits = load_resource_limits(repo_root)
    try:
        if input_path.is_dir():
            proposal = import_model_sheet_csv(input_path, model_path)
        elif input_path.suffix.lower() == ".xlsx":
            proposal = import_model_sheet_xlsx(
                input_path, model_path, max_rows=limits.max_import_rows
            )
        else:
            console.print("[red]Input must be a CSV directory or an .xlsx workbook.[/red]")
            raise typer.Exit(code=1)
    except SpreadsheetImportError as exc:
        console.print(f"[red]Review import rejected: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    service = AuditEventService(repo_root)
    changed_object_ids = [op.get("object_id", "") for op in proposal.get("operations", [])]
    service.emit(
        create_audit_event(
            event_type="model_import",
            actor="system",
            status="success",
            command="import-model-sheet",
            changed_object_ids=changed_object_ids,
            proposal_id=proposal.get("id"),
            outputs={
                "proposal_id": proposal.get("id"),
                "operations_count": len(proposal.get("operations", [])),
                "warnings_count": len(proposal.get("warnings", [])),
            },
        )
    )

    # Register source
    src_service = SourceRegistryService(repo_root)
    register_import_source(
        src_service,
        proposal_id=proposal.get("id", ""),
        source_path=input_path,
        operations_count=len(proposal.get("operations", [])),
        warnings_count=len(proposal.get("warnings", [])),
    )

    if json_output:
        print(json.dumps(proposal, indent=2, default=str))
    else:
        console.print(f"[bold]PatchProposal: {proposal['id']}[/bold]")
        console.print(f"  Operations: {len(proposal['operations'])}")
        console.print(f"  Warnings: {len(proposal.get('warnings', []))}")
        for w in proposal.get("warnings", []):
            console.print(f"    [yellow]{w}[/yellow]")
        if proposal["operations"]:
            table = Table("Op", "Object", "Type", "Target")
            for op in proposal["operations"][:20]:
                table.add_row(
                    op.get("op", "—"),
                    op.get("object_id", "—"),
                    op.get("object_type", "—"),
                    op.get("target_path", "—"),
                )
            console.print(table)
            if len(proposal["operations"]) > 20:
                console.print(f"  ... and {len(proposal['operations']) - 20} more")


@app.command("import-excel-review")
def import_excel_review(
    input_path: Path = typer.Option(..., "--from", help="Reviewed XLSX workbook to import."),  # noqa: B008
    output: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Path for the generated PatchProposal Markdown."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Create a reviewable PatchProposal from a business-review XLSX workbook.

    This command writes only the requested proposal artifact. It never edits the
    canonical model; use the proposal review and approval workflow to apply an
    accepted proposal later.
    """
    repo_root = _resolve_repo(repo)
    if not input_path.is_file() or input_path.suffix.lower() != ".xlsx":
        console.print("[red]--from must point to an existing .xlsx workbook.[/red]")
        raise typer.Exit(code=1)

    try:
        proposal = import_model_sheet_xlsx(
            input_path,
            resolve_model_path(repo_root),
            max_rows=load_resource_limits(repo_root).max_import_rows,
            require_stable_ids=True,
        )
    except SpreadsheetImportError as exc:
        console.print(f"[red]Review import rejected: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_patch_proposal_markdown(proposal), encoding="utf-8")
    console.print(f"[green]PatchProposal written:[/green] {output}")
    console.print(f"  ID: {proposal['id']}")
    console.print(f"  Operations: {len(proposal['operations'])}")
    console.print("  Canonical model files were not changed.")


@app.command("export-model")
@with_telemetry("export-model")
def export_model(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    fmt: str = typer.Option("csv", "--format", help="Export format: csv, xlsx, or json."),
    business_review: bool = typer.Option(
        False, "--business-review", help="Styled XLSX for non-technical review."
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None, "--out", help="Output path for a single XLSX export."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Export canonical model objects to CSV or XLSX."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    limits = load_resource_limits(repo_root)
    try:
        if fmt.lower() == "csv":
            written = export_model_csv(model_path, max_objects=limits.max_export_objects)
            if json_output:
                print(
                    json.dumps(
                        {
                            "format": "csv",
                            "files": [str(f) for f in written],
                            "business_review": business_review,
                        },
                        indent=2,
                        default=str,
                    )
                )
                raise typer.Exit()
            console.print(f"[green]Exported {len(written)} CSV files[/green]")
            for f in written:
                console.print(f"  {f}")
            path = written[0] if written else None
        elif fmt.lower() == "json":
            written = export_model_jsonl(model_path, max_objects=limits.max_export_objects)
            if json_output:
                print(
                    json.dumps(
                        {
                            "format": "json",
                            "files": [str(f) for f in written],
                            "business_review": business_review,
                        },
                        indent=2,
                        default=str,
                    )
                )
                raise typer.Exit()
            console.print(f"[green]Exported {len(written)} JSONL files[/green]")
            for f in written:
                console.print(f"  {f}")
            path = written[0] if written else None
        elif fmt.lower() == "xlsx":
            if output is not None and output.suffix.lower() != ".xlsx":
                console.print(
                    "[red]--out must use an .xlsx filename when --format xlsx is selected.[/red]"
                )
                raise typer.Exit(code=1)
            path = export_model_xlsx(
                model_path,
                output_path=output,
                max_objects=limits.max_export_objects,
                business_review=business_review,
            )
            if json_output:
                print(
                    json.dumps(
                        {
                            "format": "xlsx",
                            "file": str(path),
                            "business_review": business_review,
                        },
                        indent=2,
                        default=str,
                    )
                )
                raise typer.Exit()
            label = "business-review XLSX workbook" if business_review else "XLSX workbook"
            console.print(f"[green]Exported {label}[/green]")
            console.print(f"  {path}")
        else:
            if json_output:
                print(json.dumps({"error": f"Unknown format: {fmt}"}))
            else:
                console.print(f"[red]Unknown format: {fmt}. Use 'csv', 'xlsx', or 'json'.[/red]")
            raise typer.Exit(code=1)
    except ResourceLimitExceeded as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    is_list_format = fmt.lower() in ("csv", "json")
    changed_files = [str(f) for f in (written if is_list_format else [path])]
    service = AuditEventService(repo_root)
    service.emit(
        create_audit_event(
            event_type="model_export",
            actor="system",
            status="success",
            command=f"export-model --format {fmt}",
            changed_files=changed_files,
            outputs={
                "format": fmt,
                "file_count": len(written) if is_list_format else 1,
            },
        )
    )


@app.command("export-schema")
@with_telemetry("export-schema")
def export_schema(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    type: str = typer.Option(
        "all", "--type", help="Object type to export. Use 'all' for every type."
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None, "--output", help="Output file path."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Export JSON Schema for canonical object types."""
    repo_root = _resolve_repo(repo)

    if output is None:
        output = resolve_generated_path(repo_root) / "schemas" / "canonical_objects.json"

    try:
        result = export_schemas(type_filter=type)
    except ValueError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    output_path = write_schema_export(output, type_filter=type)

    if json_output:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        raise typer.Exit()

    console.print(f"[green]Exported {result['type_count']} JSON Schema(s) to {output_path}[/green]")


@app.command("export-sheets")
def export_sheets(
    spreadsheet_id: str = typer.Argument(..., help="Google Sheets spreadsheet ID."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Export canonical model objects to Google Sheets.

    Requires google-api-python-client. Install with:
    pip install modelops_core[google]
    """
    repo_root = _resolve_repo(repo)

    limits = load_resource_limits(repo_root)
    try:
        result = export_to_google_sheets(
            repo_root,
            spreadsheet_id,
            max_objects=limits.max_export_objects,
        )
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[red]Export failed: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print("[green]Exported to Google Sheets[/green]")
    console.print(f"  URL: {result.spreadsheet_url}")
    console.print(f"  Sheets: {', '.join(result.sheet_names)}")
    console.print(f"  Total objects: {sum(result.object_counts.values())}")


@app.command("git-bundle")
def git_bundle(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID to bundle."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate a GitHub-ready change bundle from a PatchProposal."""
    repo_root = _resolve_repo(repo)

    try:
        result = create_git_bundle(repo_root, proposal_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        output = {
            "bundle_dir": str(result.bundle_dir),
            "proposal_id": result.proposal_id,
            "affected_objects": result.affected_objects,
            "commit_message": result.commit_message,
            "files": {
                "bundle_json": str(result.bundle_json_path),
                "readme": str(result.readme_path),
                "pr_body": str(result.pr_body_path),
                "changed_files_dir": str(result.changed_files_dir),
            },
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        console.print(f"[green]Bundle created for {proposal_id}[/green]")
        console.print(f"  Directory: {result.bundle_dir}")
        console.print(f"  Affected objects: {len(result.affected_objects)}")
        console.print(f"  README: {result.readme_path}")
        console.print(f"  PR body: {result.pr_body_path}")
        console.print(f"  Commit message: {result.pr_body_path.parent / 'COMMIT_MESSAGE.txt'}")


@app.command("publish-issue")
def publish_issue(
    draft: Path = typer.Argument(  # noqa: B008
        ..., help="Path to issue draft Markdown file."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    github_repo: str = typer.Option(  # noqa: B008
        ..., "--github-repo", help="Target GitHub repo (owner/name)."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating."),
    label: list[str] | None = typer.Option(  # noqa: B008
        None, "--label", help="GitHub labels."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Publish an issue draft to GitHub.

    Requires requests. Install with: pip install modelops_core[github]
    """
    repo_root = _resolve_repo(repo)

    try:
        result = publish_issue_from_draft(
            repo_root=repo_root,
            github_repo=github_repo,
            draft_path=draft,
            labels=label if label else None,
            dry_run=dry_run,
        )
    except Exception as exc:
        console.print(f"[red]Failed to publish issue: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        if dry_run:
            console.print("[yellow]Dry-run preview:[/yellow]")
            console.print(f"  Title: {result['title']}")
            console.print(f"  Repo: {result['repo']}")
            console.print(f"  Labels: {', '.join(result['labels'])}")
            console.print(f"  Body preview: {result['body']}")
        else:
            console.print("[green]Issue published[/green]")
            console.print(f"  URL: {result['issue_url']}")
            console.print(f"  Number: {result['issue_number']}")


@app.command("publish-pr")
def publish_pr(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID to publish."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    github_repo: str = typer.Option(..., "--github-repo", help="Target GitHub repo (owner/name)."),
    head: str = typer.Option(..., "--head", help="Branch with changes."),
    base: str = typer.Option("main", "--base", help="Branch to merge into."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Publish a git bundle as a GitHub pull request.

    Requires requests. Install with: pip install modelops_core[github]
    """
    repo_root = _resolve_repo(repo)

    try:
        result = publish_pr_from_bundle(
            repo_root=repo_root,
            github_repo=github_repo,
            proposal_id=proposal_id,
            head_branch=head,
            base_branch=base,
            dry_run=dry_run,
        )
    except Exception as exc:
        console.print(f"[red]Failed to publish PR: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        if dry_run:
            console.print("[yellow]Dry-run preview:[/yellow]")
            console.print(f"  Title: {result['title']}")
            console.print(f"  Repo: {result['repo']}")
            console.print(f"  Head: {result['head']} -> Base: {result['base']}")
            console.print(f"  Affected objects: {len(result['affected_objects'])}")
            console.print(f"  Body preview: {result['body']}")
        else:
            console.print("[green]Pull request published[/green]")
            console.print(f"  URL: {result['pr_url']}")
            console.print(f"  Number: {result['pr_number']}")

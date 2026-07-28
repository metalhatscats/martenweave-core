from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.table import Table

from modelops_core.commands._common import _resolve_repo, console
from modelops_core.config import resolve_model_path
from modelops_core.imports.schema_comparison import compare_schema_files
from modelops_core.imports.schema_import_service import (
    inspect_to_proposal,
    register_schema_import_source,
    write_schema_proposal,
)
from modelops_core.imports.schema_inspection import SchemaInspectionError, inspect_schema_file
from modelops_core.reports.source_registry_service import SourceRegistryService
from modelops_core.telemetry import with_telemetry

schema_app = typer.Typer(
    name="schema",
    help="Inspect external machine-readable schema evidence.",
)
_SCHEMA_INPUT_ARGUMENT = typer.Argument(
    ...,
    help=(
        "Path to a local JSON Schema, sample JSON/XML/IDoc payload, CDS metadata export, "
        "CSV/XLSX field catalogue, SAP mapping, WE60 HTML documentation, or Migration "
        "Cockpit workbook template, OpenAPI, OData EDMX, WSDL, XML Schema, Integration "
        "Suite `.iflw`, or Integration Suite artifact ZIP file."
    ),
)


@schema_app.command("inspect")
@with_telemetry("schema_inspect")
def inspect_schema(
    input_path: Path = _SCHEMA_INPUT_ARGUMENT,
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Inspect a local machine-readable schema or payload evidence file."""
    try:
        document = inspect_schema_file(input_path)
    except SchemaInspectionError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(document.to_dict(), indent=2, default=str, sort_keys=True))
        raise typer.Exit()

    console.print(f"[bold]Schema inspection:[/bold] {input_path.name}")
    console.print(f"  Format:      {document.source_format}")
    console.print(f"  Identity:    {document.source_identity}")
    console.print(f"  Version:     {document.source_version or '—'}")
    console.print(f"  Namespace:   {document.namespace or '—'}")
    console.print(f"  Entities:    {len(document.entities)}")
    console.print(f"  Fields:      {len(document.fields)}")
    console.print(f"  Operations:  {len(document.operations)}")
    console.print(f"  Warnings:    {len(document.warnings)}")

    if document.entities:
        entity_table = Table("Entity", "Kind", "Source")
        for entity in document.entities[:10]:
            entity_table.add_row(entity.name, entity.kind, entity.source_evidence)
        console.print(entity_table)

    if document.fields:
        field_table = Table("Field", "Type", "Required", "Cardinality", "Evidence")
        for field in document.fields[:15]:
            field_table.add_row(
                field.field_path,
                field.data_type or "—",
                "yes" if field.required else "no" if field.required is not None else "—",
                field.cardinality or "—",
                field.source_evidence,
            )
        console.print(field_table)

    if document.operations:
        op_table = Table("Operation", "Method", "Path", "Protocol")
        for operation in document.operations[:10]:
            op_table.add_row(
                operation.operation_id,
                operation.method,
                operation.path,
                operation.protocol,
            )
        console.print(op_table)

    for warning in document.warnings[:10]:
        console.print(f"[yellow]Warning:[/yellow] {warning}")


@schema_app.command("compare")
@with_telemetry("schema_compare")
def compare_schema(
    base: Path = typer.Argument(..., help="Earlier local schema evidence file."),  # noqa: B008
    candidate: Path = typer.Argument(..., help="Candidate local schema evidence file."),  # noqa: B008
    json_output: bool = typer.Option(False, "--json", help="Output stable JSON."),
) -> None:
    """Compare two local normalized contracts without fetching or mutating anything."""
    try:
        report = compare_schema_files(str(base), str(candidate))
    except SchemaInspectionError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    if json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    console.print("[bold]Schema comparison[/bold]")
    console.print("Potential-breaking results are deterministic review signals, not a guarantee.")
    for item in report["differences"]:
        marker = "potential-breaking" if item["breaking"] else "review"
        console.print(f"  {item['change']}: {item['kind']} {item['id']} ({marker})")
    if not report["differences"]:
        console.print("  No deterministic differences.")


@schema_app.command("import")
@with_telemetry("schema_import")
def import_schema(
    input_path: Path = _SCHEMA_INPUT_ARGUMENT,
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    as_proposal: bool = typer.Option(
        False,
        "--as-proposal",
        help="Write a reviewable PatchProposal artifact instead of previewing only.",
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None,
        "--out",
        help="Optional output path for the proposal Markdown artifact.",
    ),
    source_url: str | None = typer.Option(
        None,
        "--source-url",
        help="Optional official or upstream source URL for provenance capture.",
    ),
    license_note: str | None = typer.Option(
        None,
        "--license-note",
        help="Optional license or redistribution note to store with the source entry.",
    ),
    usage_note: str | None = typer.Option(
        None,
        "--usage-note",
        help="Optional usage or handling note to store with the source entry.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Turn inspected schema evidence into a reviewable PatchProposal artifact."""
    try:
        result = inspect_to_proposal(input_path)
    except SchemaInspectionError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    proposal_path: str | None = None
    if as_proposal:
        repo_root = _resolve_repo(repo)
        model_path = resolve_model_path(repo_root)
        written = write_schema_proposal(result, repo_model_path=model_path, output_path=output)
        register_schema_import_source(
            SourceRegistryService(repo_root),
            result,
            source_url=source_url,
            license_note=license_note,
            usage_note=usage_note,
        )
        proposal_path = str(written)

    payload = {
        "proposal_id": result.proposal["id"],
        "source_id": result.source_id,
        "source_format": result.inspected.source_format,
        "source_version": result.inspected.source_version,
        "namespace": result.inspected.namespace,
        "parser_version": result.inspected.parser_version,
        "checksum": result.inspected.checksum,
        "source_url": source_url,
        "license_note": license_note,
        "usage_note": usage_note,
        "entity_count": len(result.inspected.entities),
        "field_count": len(result.inspected.fields),
        "operation_count": len(result.inspected.operations),
        "validation_status": result.proposal["validation_status"],
        "validation_errors": result.validation_errors,
        "validation_warnings": result.validation_warnings,
        "proposal_path": proposal_path,
    }

    if json_output:
        print(
            json.dumps(
                payload | {"proposal": result.proposal},
                indent=2,
                default=str,
                sort_keys=True,
            )
        )
        raise typer.Exit()

    console.print(f"[bold]Schema import preview:[/bold] {input_path.name}")
    console.print(f"  Proposal:   {result.proposal['id']}")
    console.print(f"  Format:     {result.inspected.source_format}")
    console.print(f"  Version:    {result.inspected.source_version or '—'}")
    console.print(f"  Namespace:  {result.inspected.namespace or '—'}")
    console.print(f"  Entities:   {len(result.inspected.entities)}")
    console.print(f"  Fields:     {len(result.inspected.fields)}")
    console.print(f"  Operations: {len(result.inspected.operations)}")
    console.print(f"  Validation: {result.proposal['validation_status']}")
    console.print(f"  Errors:     {result.validation_errors}")
    console.print(f"  Warnings:   {result.validation_warnings}")
    if proposal_path:
        console.print(f"[green]Proposal written:[/green] {proposal_path}")
    else:
        console.print(
            "[yellow]Preview only:[/yellow] pass `--as-proposal` to write a proposal artifact."
        )

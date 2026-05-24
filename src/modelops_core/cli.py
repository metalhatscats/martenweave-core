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
    load_repo_config,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.exports import export_model_csv, export_model_xlsx
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.impact.proposal_impact_service import generate_proposal_impact_report
from modelops_core.imports import (
    dataset_profile_to_dict,
    infer_model_from_profile,
    profile_csv,
    profile_xlsx,
)
from modelops_core.imports.model_sheet_import_service import (
    import_model_sheet_csv,
    import_model_sheet_xlsx,
)
from modelops_core.index import build_index as _build_index
from modelops_core.patching.apply_service import (
    apply_patch_proposal,
    dry_run_patch_proposal,
)
from modelops_core.patching.patch_proposal_service import (
    write_patch_proposal,
)
from modelops_core.reports.analysis_service import generate_analysis_report
from modelops_core.reports.audit_service import (
    AuditEventService,
    create_audit_event,
    filter_audit_events,
)
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.repository import parse_file, scan_repository
from modelops_core.trace import trace_object
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
    config = load_repo_config(repo_root)
    enabled_packs = config.enabled_domain_packs if config else None
    summary = validate_objects(parsed_objects, enabled_packs)

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
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show repository health report."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_repository_health(db_path)

    if json_output:
        result = {
            "object_count": report.object_count,
            "index_fresh": report.index_fresh,
            "coverage_gaps": {
                "objects_without_name": report.coverage_gaps.objects_without_name
                if report.coverage_gaps
                else 0,
                "objects_without_description": report.coverage_gaps.objects_without_description
                if report.coverage_gaps
                else 0,
            },
            "ownership_coverage": report.ownership_coverage.__dict__
            if report.ownership_coverage
            else {},
            "data_quality_coverage": report.data_quality_coverage.__dict__
            if report.data_quality_coverage
            else {},
            "coverage_gaps_list": [
                {
                    "object_id": g.object_id,
                    "object_type": g.object_type,
                    "object_name": g.object_name,
                    "gap_type": g.gap_type,
                    "suggested_action": g.suggested_action,
                }
                for g in report.coverage_gaps_list
            ],
            "type_counts": report.type_counts,
        }
        console.print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Repository Health[/bold]")
    console.print(f"  Total objects: {report.object_count}")
    console.print(f"  Index fresh:   {report.index_fresh}")
    if report.coverage_gaps:
        console.print(f"  Missing name:        {report.coverage_gaps.objects_without_name}")
        console.print(f"  Missing description: {report.coverage_gaps.objects_without_description}")
    if report.ownership_coverage:
        oc = report.ownership_coverage
        console.print(
            f"  Ownership coverage:  {oc.with_owner}/{oc.total_eligible} "
            f"({oc.percentage}%)"
        )
    if report.data_quality_coverage:
        dq = report.data_quality_coverage
        console.print("\n[bold]Data Quality Coverage[/bold]")
        console.print(
            f"  Attributes with rules:    "
            f"{dq.attributes_with_rules}/{dq.active_attributes} "
            f"({dq.attribute_rule_coverage_percent}%)"
        )
        console.print(
            f"  Endpoints with LoV:       "
            f"{dq.endpoints_with_lov}/{dq.active_field_endpoints} "
            f"({dq.endpoint_lov_coverage_percent}%)"
        )
        console.print(
            f"  Mappings with value map:  "
            f"{dq.mappings_with_value_mapping}/{dq.active_mappings} "
            f"({dq.mapping_logic_coverage_percent}%)"
        )
        console.print(
            f"  Datasets with profile:    "
            f"{dq.datasets_with_profile}/{dq.active_datasets} "
            f"({dq.dataset_profile_coverage_percent}%)"
        )
        console.print(
            f"  Active objects with owner: "
            f"{dq.objects_with_owner}/{dq.active_objects} ({dq.ownership_coverage_percent}%)"
        )
    if report.coverage_gaps_list:
        console.print(f"\n[bold]Coverage Gaps ({len(report.coverage_gaps_list)})[/bold]")
        table = Table("Object ID", "Type", "Gap", "Suggested Action")
        for g in report.coverage_gaps_list[:20]:
            table.add_row(
                g.object_id,
                g.object_type,
                g.gap_type,
                g.suggested_action,
            )
        console.print(table)
        if len(report.coverage_gaps_list) > 20:
            console.print(f"  ... and {len(report.coverage_gaps_list) - 20} more gaps")
    if report.type_counts:
        table = Table("Type", "Count")
        for t, c in sorted(report.type_counts.items()):
            table.add_row(t, str(c))
        console.print(table)


@app.command()
def analyze(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Analyze model completeness, risk, and readiness."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_analysis_report(db_path, repo_root)

    if json_output:
        result = {
            "object_count": report.object_count,
            "type_counts": report.type_counts,
            "orphan_fields": {
                "field_endpoints_without_attribute": (
                    report.orphan_fields.field_endpoints_without_attribute
                    if report.orphan_fields
                    else []
                ),
            },
            "attribute_coverage": {
                "attributes_without_fields": (
                    report.attribute_coverage.attributes_without_fields
                    if report.attribute_coverage
                    else []
                ),
            },
            "ownership_gaps": report.ownership_gaps,
            "validation_coverage": report.validation_coverage,
            "lov_coverage": report.lov_coverage,
            "mapping_coverage": report.mapping_coverage,
            "risk_report": {
                "issue_count": report.risk_report.issue_count
                if report.risk_report
                else 0,
                "risk_count": report.risk_report.risk_count
                if report.risk_report
                else 0,
                "open_issues": report.risk_report.open_issues
                if report.risk_report
                else [],
            },
            "change_activity": {
                "event_count": report.change_activity.event_count
                if report.change_activity
                else 0,
                "recent_events": report.change_activity.recent_events
                if report.change_activity
                else [],
            },
        }
        console.print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Model Analysis[/bold]")
    console.print(f"  Objects: {report.object_count}")

    if report.orphan_fields and report.orphan_fields.field_endpoints_without_attribute:
        console.print(
            f"\n[bold]Orphan Fields[/bold] "
            f"({len(report.orphan_fields.field_endpoints_without_attribute)})"
        )
        table = Table("Field Endpoint", "Name", "Reason")
        for item in report.orphan_fields.field_endpoints_without_attribute[:10]:
            table.add_row(
                item["object_id"],
                item.get("object_name") or "—",
                item["reason"],
            )
        console.print(table)

    if report.attribute_coverage and report.attribute_coverage.attributes_without_fields:
        console.print(
            f"\n[bold]Attributes without Fields[/bold] "
            f"({len(report.attribute_coverage.attributes_without_fields)})"
        )
        table = Table("Attribute", "Name", "Reason")
        for item in report.attribute_coverage.attributes_without_fields[:10]:
            table.add_row(
                item["object_id"],
                item.get("object_name") or "—",
                item["reason"],
            )
        console.print(table)

    if report.ownership_gaps:
        console.print(f"\n[bold]Ownership Gaps[/bold] ({len(report.ownership_gaps)})")
        table = Table("Object ID", "Type", "Name")
        for item in report.ownership_gaps[:10]:
            table.add_row(
                item["object_id"],
                item["object_type"],
                item.get("object_name") or "—",
            )
        console.print(table)

    if report.risk_report and (report.risk_report.issue_count or report.risk_report.risk_count):
        console.print(
            f"\n[bold]Risk Report[/bold]"
            f" — Issues: {report.risk_report.issue_count}"
            f", Risks: {report.risk_report.risk_count}"
        )

    if report.change_activity and report.change_activity.recent_events:
        console.print(
            f"\n[bold]Recent Activity[/bold] "
            f"({len(report.change_activity.recent_events)} of "
            f"{report.change_activity.event_count} events)"
        )
        table = Table("Event Type", "Timestamp", "Status", "Proposal")
        for item in report.change_activity.recent_events[:10]:
            table.add_row(
                item["event_type"],
                item["timestamp"],
                item["status"],
                item.get("proposal_id") or "—",
            )
        console.print(table)


@app.command("trace")
def trace(
    object_id: str = typer.Argument(..., help="Object ID to trace from."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    direction: str = typer.Option("both", "--direction", help="upstream, downstream, or both."),
    max_depth: int = typer.Option(5, "--max-depth", help="Maximum traversal depth."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Trace upstream and downstream relationships for an object."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    result = trace_object(db_path, object_id, max_depth=max_depth, direction=direction)

    if json_output:
        import json

        data = {
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
                }
                for e in result.edges
            ],
        }
        console.print(json.dumps(data, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Trace: {object_id}[/bold]")
    if result.root_object_name:
        console.print(f"  Name: {result.root_object_name}")
    console.print(f"  Direction: {direction}")
    console.print(f"  Max depth: {max_depth}")

    if result.nodes:
        table = Table("ID", "Type", "Name", "Depth", "Direction")
        for n in result.nodes:
            dir_label = "upstream" if any(
                e.direction == "upstream" and e.to_object_id == n.object_id
                for e in result.edges
            ) else "downstream"
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

    service = AuditEventService(repo_root)
    changed_object_ids = [
        op.get("object_id", "") for op in proposal.get("operations", [])
    ]
    service.emit(
        create_audit_event(
            event_type="proposal_created",
            actor="system",
            status="success",
            command="propose-patch",
            proposal_id=proposal.get("id"),
            changed_object_ids=changed_object_ids,
            validation_status="valid" if result.get("is_safe") else "invalid",
            outputs={
                "proposal_id": proposal.get("id"),
                "operations_count": len(proposal.get("operations", [])),
                "is_safe": result.get("is_safe"),
            },
        )
    )


# ---------------------------------------------------------------------------
# Proposal subcommands
# ---------------------------------------------------------------------------
proposal_app = typer.Typer(
    name="proposal",
    help="Review and apply PatchProposals.",
)
app.add_typer(proposal_app, name="proposal")


@proposal_app.command("list")
def proposal_list(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """List all PatchProposals in the repository."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposals_dir = model_path / "patch-proposals"

    if not proposals_dir.exists():
        console.print("[yellow]No patch-proposals directory found.[/yellow]")
        raise typer.Exit()

    files = sorted(proposals_dir.glob("PP-*.md"))
    if not files:
        console.print("[yellow]No PatchProposals found.[/yellow]")
        raise typer.Exit()

    table = Table("ID", "Status", "Applied")
    for f in files:
        parsed = parse_file(f)
        fm = parsed.frontmatter or {}
        status = fm.get("status", "—")
        applied = "yes" if fm.get("applied_at") else "no"
        table.add_row(fm.get("id", f.stem), status, applied)
    console.print(table)


@proposal_app.command("show")
def proposal_show(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Show details of a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}

    console.print(f"[bold]PatchProposal: {proposal_id}[/bold]")
    console.print(f"  Status: {fm.get('status', '—')}")
    console.print(f"  Validation: {fm.get('validation_status', '—')}")
    console.print(f"  Operations: {len(fm.get('operations', []))}")
    if fm.get("applied_at"):
        console.print(f"  Applied at: {fm['applied_at']}")
        console.print(f"  Changed files: {fm.get('applied_changed_files', [])}")

    operations = fm.get("operations", [])
    if operations:
        table = Table("Op", "Object ID", "Type", "Target")
        for op in operations:
            table.add_row(
                op.get("op", "—"),
                op.get("object_id", "—"),
                op.get("object_type", "—"),
                op.get("target_path", "—"),
            )
        console.print(table)


@proposal_app.command("validate")
def proposal_validate(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Run deterministic validation on a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"

    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}

    from modelops_core.patching.patch_validator import validate_patch_proposal

    results = validate_patch_proposal(fm)
    error_count = sum(1 for r in results if r.severity == "ERROR")
    warning_count = sum(1 for r in results if r.severity == "WARNING")

    console.print(f"[bold]Validation for {proposal_id}[/bold]")
    console.print(f"  Errors: {error_count}")
    console.print(f"  Warnings: {warning_count}")

    if results:
        table = Table("Severity", "Code", "Message", "Fix")
        for r in results:
            table.add_row(
                str(r.severity),
                r.code,
                r.message,
                r.suggested_fix or "—",
            )
        console.print(table)

    service = AuditEventService(repo_root)
    service.emit(
        create_audit_event(
            event_type="proposal_validated",
            actor="system",
            status="success" if error_count == 0 else "failed",
            command="proposal validate",
            proposal_id=proposal_id,
            validation_status="valid" if error_count == 0 else "invalid",
            outputs={
                "error_count": error_count,
                "warning_count": warning_count,
            },
        )
    )

    if error_count > 0:
        raise typer.Exit(code=1)


@proposal_app.command("impact")
def proposal_impact(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    max_depth: int = typer.Option(2, "--max-depth", help="Maximum impact traversal depth."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show impact analysis for a PatchProposal's operations."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `modelops build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        console.print(f"[red]PatchProposal not found: {proposal_id}[/red]")
        raise typer.Exit(code=1)

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    operations = fm.get("operations", [])

    report = generate_proposal_impact_report(
        db_path, proposal_id, operations, max_depth=max_depth
    )

    if json_output:
        result = {
            "proposal_id": report.proposal_id,
            "high_risk": report.high_risk,
            "affected_objects": [
                {
                    "object_id": obj.object_id,
                    "object_type": obj.object_type,
                    "object_name": obj.object_name,
                    "relationship_type": obj.relationship_type,
                    "direction": obj.direction,
                    "depth": obj.depth,
                }
                for obj in report.all_affected_objects
            ],
            "operations": [
                {
                    "op": op_report.op,
                    "object_id": op_report.object_id,
                    "object_type": op_report.object_type,
                    "affected_count": len(op_report.impact_report.affected_objects)
                    + len(op_report.synthetic_affected),
                }
                for op_report in report.operation_reports
            ],
        }
        console.print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Impact Report for {proposal_id}[/bold]")
    if report.high_risk:
        console.print("[red]  ⚠ High-risk proposal[/red]")
    console.print(f"  Operations analyzed: {len(report.operation_reports)}")

    for op_report in report.operation_reports:
        console.print(
            f"\n  [bold]{op_report.op}[/bold] → {op_report.object_id}"
            f" ({op_report.object_type or 'Unknown'})"
        )
        all_affected = op_report.impact_report.affected_objects + op_report.synthetic_affected
        if all_affected:
            table = Table("Object ID", "Type", "Direction", "Depth", "Relationship")
            for obj in all_affected:
                table.add_row(
                    obj.object_id,
                    obj.object_type or "—",
                    obj.direction or "—",
                    str(obj.depth),
                    obj.relationship_type or "—",
                )
            console.print(table)
        else:
            console.print("    No affected objects found.")


@proposal_app.command("apply")
def proposal_apply(
    proposal_id: str = typer.Argument(..., help="PatchProposal ID (e.g. PP-001)."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview changes without applying."
    ),
) -> None:
    """Apply an accepted PatchProposal to canonical files."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if dry_run:
        result = dry_run_patch_proposal(model_path, proposal_id)
        if result.error:
            console.print(f"[red]{result.error}[/red]")
            raise typer.Exit(code=1)

        console.print(f"[bold]Dry-run for {proposal_id}[/bold]")
        console.print(f"  Would change: {result.would_change}")
        if result.operations_preview:
            table = Table("Op", "Object", "Status", "Details")
            for p in result.operations_preview:
                details = p.get("file", "") or p.get("reason", "")
                table.add_row(
                    p.get("op", "—"),
                    p.get("object_id", "—"),
                    p.get("status", "—"),
                    details,
                )
            console.print(table)

        # Show impact summary
        db_path = resolve_generated_path(repo_root) / "modelops.db"
        if db_path.exists():
            parsed = parse_file(model_path / "patch-proposals" / f"{proposal_id}.md")
            fm = parsed.frontmatter or {}
            operations = fm.get("operations", [])
            impact_report = generate_proposal_impact_report(
                db_path, proposal_id, operations, max_depth=2
            )
            console.print("\n[bold]Impact Summary[/bold]")
            if impact_report.high_risk:
                console.print("[red]  ⚠ High-risk proposal[/red]")
            affected = impact_report.all_affected_objects
            console.print(f"  Affected objects: {len(affected)}")
            if affected:
                table = Table("Object ID", "Type", "Direction", "Depth")
                for obj in affected[:10]:
                    table.add_row(
                        obj.object_id,
                        obj.object_type or "—",
                        obj.direction or "—",
                        str(obj.depth),
                    )
                console.print(table)
                if len(affected) > 10:
                    console.print(f"  ... and {len(affected) - 10} more")
        raise typer.Exit()

    try:
        result = apply_patch_proposal(model_path, proposal_id)
    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Applied {proposal_id}[/green]")
    console.print(f"  Changed files: {len(result.changed_files)}")
    for f in result.changed_files:
        console.print(f"    {f}")
    if result.audit_event_written:
        console.print("  Audit event written")
    if result.index_rebuilt:
        console.print("  Index rebuilt")


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(8000, "--port", help="Bind port."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Start the local API server."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print(
            "[red]uvicorn is required for the API server. "
            "Install it with: pip install uvicorn[/red]"
        )
        raise typer.Exit(code=1) from exc

    repo_root = _resolve_repo(repo)
    console.print(f"[green]Starting API server at http://{host}:{port}[/green]")
    console.print(f"  Repository: {repo_root}")

    from modelops_core.api.app import app as api_app

    uvicorn.run(api_app, host=host, port=port)


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

    if input_path.is_dir():
        proposal = import_model_sheet_csv(input_path, model_path)
    elif input_path.suffix.lower() == ".xlsx":
        proposal = import_model_sheet_xlsx(input_path, model_path)
    else:
        console.print(
            "[red]Input must be a CSV directory or an .xlsx workbook.[/red]"
        )
        raise typer.Exit(code=1)

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

    if json_output:
        console.print(json.dumps(proposal, indent=2, default=str))
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


@app.command("export-model")
def export_model(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    fmt: str = typer.Option("csv", "--format", help="Export format: csv or xlsx."),
) -> None:
    """Export canonical model objects to CSV or XLSX."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if fmt.lower() == "csv":
        written = export_model_csv(model_path)
        console.print(f"[green]Exported {len(written)} CSV files[/green]")
        for f in written:
            console.print(f"  {f}")
    elif fmt.lower() == "xlsx":
        path = export_model_xlsx(model_path)
        console.print("[green]Exported XLSX workbook[/green]")
        console.print(f"  {path}")
    else:
        console.print(f"[red]Unknown format: {fmt}. Use 'csv' or 'xlsx'.[/red]")
        raise typer.Exit(code=1)

    service = AuditEventService(repo_root)
    service.emit(
        create_audit_event(
            event_type="model_export",
            actor="system",
            status="success",
            command=f"export-model --format {fmt}",
            changed_files=[str(f) for f in (written if fmt.lower() == "csv" else [path])],
            outputs={"format": fmt, "file_count": len(written) if fmt.lower() == "csv" else 1},
        )
    )


@app.command("audit-log")
def audit_log(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    object_id: str | None = typer.Option(None, "--object-id", help="Filter by changed object ID."),
    proposal_id: str | None = typer.Option(None, "--proposal-id", help="Filter by proposal ID."),
    event_type: str | None = typer.Option(None, "--event-type", help="Filter by event type."),
    date_from: str | None = typer.Option(None, "--date-from", help="Filter from date (ISO)."),
    date_to: str | None = typer.Option(None, "--date-to", help="Filter to date (ISO)."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Query the append-only audit log."""
    repo_root = _resolve_repo(repo)
    service = AuditEventService(repo_root)
    events = service.read_events()

    if not events:
        console.print("[yellow]No audit events found.[/yellow]")
        raise typer.Exit()

    filtered = filter_audit_events(
        events,
        object_id=object_id,
        proposal_id=proposal_id,
        event_type=event_type,
        date_from=date_from,
        date_to=date_to,
    )

    if json_output:
        console.print(json.dumps([e.to_dict() for e in filtered], indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Audit Log ({len(filtered)} events)[/bold]")
    if not filtered:
        console.print("  No events match the filters.")
        raise typer.Exit()

    table = Table("Event ID", "Type", "Timestamp", "Status", "Command", "Proposal")
    for e in filtered:
        table.add_row(
            e.event_id,
            e.event_type,
            e.timestamp,
            e.status,
            e.command or "—",
            e.proposal_id or "—",
        )
    console.print(table)


if __name__ == "__main__":
    app()

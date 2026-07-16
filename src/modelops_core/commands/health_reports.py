from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from modelops_core import __version__
from modelops_core.assessment.assessment_service import (
    generate_review_pack,
    generate_risk_report,
)
from modelops_core.commands._common import (
    _check_and_warn_stale_index,
    _resolve_repo,
    app,
    console,
)
from modelops_core.commands.assessment import _run_readiness_cli
from modelops_core.config import (
    load_repo_config,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.reports.analysis_service import generate_analysis_report
from modelops_core.reports.gap_summary import generate_gap_summary_report
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.reports.index_freshness import check_index_freshness
from modelops_core.reports.model_summary_service import (
    generate_model_summary,
    model_summary_to_dict,
    model_summary_to_markdown,
)
from modelops_core.reports.object_card_service import (
    generate_object_card,
    object_card_to_dict,
)
from modelops_core.reports.ownership_report import generate_ownership_report
from modelops_core.reports.scorecard_service import generate_scorecard
from modelops_core.repository import parse_file, scan_repository
from modelops_core.telemetry import with_telemetry
from modelops_core.validation import validate_objects


@app.command()
@with_telemetry("health")
def health(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show repository health report."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    stale = _check_and_warn_stale_index(repo_root, json_output)

    report = generate_repository_health(db_path)

    if json_output:
        result = {
            "stale_index_warning": stale,
            "martenweave_version": __version__,
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
        print(json.dumps(result, indent=2, default=str))
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
            f"  Ownership coverage:  {oc.with_owner}/{oc.total_eligible} ({oc.percentage}%)"
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


@app.command("doctor")
@with_telemetry("doctor")
def doctor(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run diagnostics: version, config, paths, index freshness, validation."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    generated_path = resolve_generated_path(repo_root)
    db_path = generated_path / "modelops.db"
    config_path = repo_root / "modelops.config.yaml"

    config = load_repo_config(repo_root)
    config_present = config_path.exists()
    model_path_exists = model_path.exists()
    generated_path_exists = generated_path.exists()
    index_exists = db_path.exists()

    freshness = check_index_freshness(repo_root)
    index_fresh = freshness.fresh if index_exists else None
    index_stale_reason = freshness.reason if index_exists else None

    validation_summary: dict[str, Any] = {
        "ran": False,
        "is_valid": None,
        "error_count": None,
        "warning_count": None,
    }
    if model_path_exists:
        files = scan_repository(model_path)
        parsed_objects = [parse_file(f) for f in files]
        enabled_packs = config.enabled_domain_packs if config else None
        summary = validate_objects(parsed_objects, enabled_packs)
        validation_summary = {
            "ran": True,
            "is_valid": summary.is_valid,
            "error_count": summary.error_count,
            "warning_count": summary.warning_count,
        }

    if json_output:
        result = {
            "martenweave_version": __version__,
            "repo_root": str(repo_root),
            "config_present": config_present,
            "model_path_exists": model_path_exists,
            "generated_path_exists": generated_path_exists,
            "index_exists": index_exists,
            "index_fresh": index_fresh,
            "index_stale_reason": index_stale_reason,
            "validation": validation_summary,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Doctor Report[/bold]")
    console.print(f"  Package version:     {__version__}")
    console.print(f"  Repository:          {repo_root}")
    console.print(f"  Config present:      {config_present}")
    console.print(f"  Model path exists:   {model_path_exists}")
    console.print(f"  Generated path exists: {generated_path_exists}")
    console.print(f"  Index exists:        {index_exists}")
    if index_exists:
        fresh_label = "[green]fresh[/green]" if index_fresh else "[red]stale[/red]"
        console.print(f"  Index freshness:     {fresh_label}")
        if index_stale_reason:
            console.print(f"  Stale reason:        {index_stale_reason}")
    if validation_summary["ran"]:
        valid_label = (
            "[green]valid[/green]" if validation_summary["is_valid"] else "[red]invalid[/red]"
        )
        console.print(f"  Validation:          {valid_label}")
        console.print(f"  Errors:              {validation_summary['error_count']}")
        console.print(f"  Warnings:            {validation_summary['warning_count']}")
    else:
        console.print("  [yellow]Validation skipped (no model path)[/yellow]")


@app.command()
@with_telemetry("scorecard")
def scorecard(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show a compact governance scorecard with readiness metrics."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_scorecard(db_path, repo_root)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "repo_name": report.repo_name,
            "generated_at": report.generated_at,
            "readiness_level": report.readiness_level,
            "object_count": report.object_count,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "target": m.target,
                    "status": m.status,
                    "explanation": m.explanation,
                    "suggested_action": m.suggested_action,
                }
                for m in report.metrics
            ],
            "gaps": [
                {
                    "object_id": g.object_id,
                    "object_type": g.object_type,
                    "gap_type": g.gap_type,
                    "suggested_action": g.suggested_action,
                }
                for g in report.gaps
            ],
            "summary": report.summary,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Scorecard: {report.repo_name}[/bold]")
    console.print(f"  Readiness: {report.readiness_level}")
    console.print(f"  Objects:   {report.object_count}")
    console.print(f"  Generated: {report.generated_at}")
    console.print("")

    table = Table("Metric", "Value", "Target", "Status", "Explanation")
    for m in report.metrics:
        status_color = {
            "pass": "[green]",
            "warning": "[yellow]",
            "fail": "[red]",
        }.get(m.status, "")
        table.add_row(
            m.name,
            str(m.value),
            str(m.target),
            f"{status_color}{m.status}[/]",
            m.explanation,
        )
    console.print(table)

    if report.gaps:
        console.print("")
        console.print(f"[bold]Top Gaps ({len(report.gaps)} shown)[/bold]")
        gap_table = Table("Object ID", "Type", "Gap", "Suggested Action")
        for g in report.gaps:
            gap_table.add_row(
                g.object_id or "—",
                g.object_type or "—",
                g.gap_type,
                g.suggested_action,
            )
        console.print(gap_table)

    console.print("")
    console.print(f"[italic]{report.summary}[/italic]")


@app.command("readiness")
@with_telemetry("readiness")
def readiness(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    profile: str = typer.Option(
        "pilot",
        "--profile",
        help="Readiness profile: demo, pilot, release.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview intended changes without writing files.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run pilot/demo/release readiness gates and show blockers."""
    repo_root = _resolve_repo(repo)
    _run_readiness_cli(repo_root, profile, dry_run, json_output)


@app.command("object-card")
@with_telemetry("object_card")
def object_card(
    object_id: str = typer.Argument(..., help="Stable ID of the model object."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show a compact context card for one canonical object."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    card = generate_object_card(repo_root, object_id, db_path=db_path)

    if card.object_type == "Unknown":
        console.print(f"[red]Object '{object_id}' not found in index.[/red]")
        raise typer.Exit(code=1)

    if card.stale_index:
        console.print(
            f"[yellow]Warning: generated index is stale ({card.stale_reason}). "
            f"Run `martenweave build-index` for up-to-date results.[/yellow]"
        )

    if json_output:
        print(json.dumps(object_card_to_dict(card), indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]{card.object_id}[/bold] ({card.object_type})")
    console.print(f"  Status: {card.status}")
    if card.name:
        console.print(f"  Name: {card.name}")
    if card.title:
        console.print(f"  Title: {card.title}")
    if card.domain:
        console.print(f"  Domain: {card.domain}")
    if card.description:
        console.print(f"  Description: {card.description}")
    console.print(f"  Source: {card.source_file}")

    if card.evidence:
        console.print("\n[bold]Evidence[/bold]")
        for item in card.evidence:
            console.print(f"  - {item}")

    if card.validation_results:
        console.print("\n[bold]Validation results[/bold]")
        table = Table("Severity", "Code", "Message")
        for v in card.validation_results:
            table.add_row(v["severity"], v["code"], v["message"])
        console.print(table)

    def _print_relationships(label: str, rels: dict[str, list[dict[str, Any]]]) -> None:
        if not rels:
            console.print(f"\n[bold]{label}[/bold]: none")
            return
        console.print(f"\n[bold]{label}[/bold]")
        table = Table("Relationship", "Object ID", "Type", "Name")
        for rel_type, targets in sorted(rels.items()):
            for target in targets:
                table.add_row(
                    rel_type,
                    target.get("object_id", "—"),
                    target.get("type", "—"),
                    target.get("name") or "—",
                )
        console.print(table)

    _print_relationships("Incoming relationships", card.incoming)
    _print_relationships("Outgoing relationships", card.outgoing)

    if card.open_issues:
        console.print("\n[bold]Open issues[/bold]")
        table = Table("ID", "Severity", "Name")
        for issue in card.open_issues:
            table.add_row(
                issue.get("object_id", "—"),
                issue.get("severity") or "—",
                issue.get("name") or "—",
            )
        console.print(table)
    else:
        console.print("\n[bold]Open issues[/bold]: none")

    if card.decisions:
        console.print("\n[bold]Decisions[/bold]")
        table = Table("ID", "Name", "Evidence")
        for decision in card.decisions:
            table.add_row(
                decision.get("object_id", "—"),
                decision.get("name") or "—",
                decision.get("evidence") or "—",
            )
        console.print(table)
    else:
        console.print("\n[bold]Decisions[/bold]: none")

    console.print("\n[bold]Impact summary[/bold]")
    console.print(f"  Affected objects: {card.impact.get('affected_object_count', 0)}")
    console.print(f"  Downstream: {card.impact.get('downstream_count', 0)}")
    console.print(f"  Upstream: {card.impact.get('upstream_count', 0)}")

    console.print("\n[bold]Trace summary[/bold]")
    upstream = card.trace.get("upstream_ids", [])
    downstream = card.trace.get("downstream_ids", [])
    console.print(f"  Upstream IDs: {', '.join(upstream) if upstream else '—'}")
    console.print(f"  Downstream IDs: {', '.join(downstream) if downstream else '—'}")


@app.command("model-summary")
@with_telemetry("model_summary")
def model_summary(
    domain: str | None = typer.Option(
        None, "--domain", help="Stable ID of the MasterDataDomain to summarize."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    out: Path | None = typer.Option(  # noqa: B008
        None, "--out", help="Path to write the Markdown report."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate a compact Markdown summary for a domain or the whole repository."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_model_summary(repo_root, domain_id=domain, db_path=db_path)

    if json_output:
        print(json.dumps(model_summary_to_dict(report), indent=2, default=str))
        raise typer.Exit()

    markdown = model_summary_to_markdown(report)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8")
        console.print(f"[bold]Model summary written to[/bold] {out}")
    else:
        console.print(markdown)


@app.command("owners")
@with_telemetry("owners")
def owners(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Show ownership coverage and steward workload."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_ownership_report(db_path, repo_root)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "owners": [
                {
                    "owner_id": o.owner_id,
                    "role": o.role,
                    "object_count": o.object_count,
                    "object_types": o.object_types,
                }
                for o in report.owners
            ],
            "orphaned_objects": [
                {
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "object_name": o.object_name,
                }
                for o in report.orphaned_objects
            ],
            "coverage_percent": report.coverage_percent,
            "total_eligible": report.total_eligible,
            "total_with_owner": report.total_with_owner,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Ownership Report[/bold]")
    console.print(f"  Coverage: {report.coverage_percent}%")
    console.print(f"  Eligible objects: {report.total_eligible}")
    console.print(f"  With owner: {report.total_with_owner}")
    console.print(f"  Orphaned: {len(report.orphaned_objects)}")
    console.print("")

    if report.owners:
        table = Table("Owner", "Role", "Objects", "Type Breakdown")
        for o in report.owners:
            type_breakdown = ", ".join(f"{k}: {v}" for k, v in o.object_types.items())
            table.add_row(o.owner_id, o.role, str(o.object_count), type_breakdown)
        console.print(table)
    else:
        console.print("[yellow]No owners found.[/yellow]")

    if report.orphaned_objects:
        console.print("")
        console.print("[bold]Orphaned Objects[/bold]")
        orphan_table = Table("Object ID", "Type", "Name")
        for o in report.orphaned_objects:
            orphan_table.add_row(o.object_id, o.object_type, o.object_name or "—")
        console.print(orphan_table)


@app.command()
def analyze(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Analyze model completeness, risk, and readiness."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
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
                "issue_count": report.risk_report.issue_count if report.risk_report else 0,
                "risk_count": report.risk_report.risk_count if report.risk_report else 0,
                "open_issues": report.risk_report.open_issues if report.risk_report else [],
            },
            "change_activity": {
                "event_count": report.change_activity.event_count if report.change_activity else 0,
                "recent_events": report.change_activity.recent_events
                if report.change_activity
                else [],
            },
            "lifecycle_summary": (
                {
                    "proposed": report.lifecycle_summary.proposed,
                    "draft": report.lifecycle_summary.draft,
                    "active": report.lifecycle_summary.active,
                    "under_review": report.lifecycle_summary.under_review,
                    "deprecated": report.lifecycle_summary.deprecated,
                    "retired": report.lifecycle_summary.retired,
                    "blocked": report.lifecycle_summary.blocked,
                    "planned": report.lifecycle_summary.planned,
                    "implemented": report.lifecycle_summary.implemented,
                    "other": report.lifecycle_summary.other,
                    "with_target_release": report.lifecycle_summary.with_target_release,
                    "with_roadmap_priority": report.lifecycle_summary.with_roadmap_priority,
                }
                if report.lifecycle_summary
                else {}
            ),
            "martenweave_version": __version__,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Model Analysis[/bold]")
    console.print(f"  Objects: {report.object_count}")

    if report.lifecycle_summary:
        ls = report.lifecycle_summary
        console.print("\n[bold]Lifecycle Summary[/bold]")
        counts = []
        if ls.proposed:
            counts.append(f"proposed: {ls.proposed}")
        if ls.draft:
            counts.append(f"draft: {ls.draft}")
        if ls.active:
            counts.append(f"active: {ls.active}")
        if ls.under_review:
            counts.append(f"under_review: {ls.under_review}")
        if ls.deprecated:
            counts.append(f"deprecated: {ls.deprecated}")
        if ls.retired:
            counts.append(f"retired: {ls.retired}")
        if ls.blocked:
            counts.append(f"blocked: {ls.blocked}")
        if ls.planned:
            counts.append(f"planned: {ls.planned}")
        if ls.implemented:
            counts.append(f"implemented: {ls.implemented}")
        if ls.other:
            counts.append(f"other: {ls.other}")
        if counts:
            console.print("  " + ", ".join(counts))
        if ls.with_target_release:
            console.print(f"  with_target_release: {ls.with_target_release}")
        if ls.with_roadmap_priority:
            console.print(f"  with_roadmap_priority: {ls.with_roadmap_priority}")

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


@app.command("risk-report")
@with_telemetry("risk_report")
def risk_report(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    out: Path | None = typer.Option(  # noqa: B008
        None, "--out", help="Output file path. Prints to stdout if omitted."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate a standalone high-risk fields report for a repository."""
    repo_root = _resolve_repo(repo)

    try:
        content = generate_risk_report(repo_root)
    except (ValueError, RuntimeError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        from datetime import UTC, datetime

        repo_name_match = re.search(r"\*\*Repository\*\*: ([^\n]+)", content)
        total_match = re.search(r"\*\*Total High Risk Items\*\*: (\d+)", content)
        rows: list[dict[str, Any]] = []
        # Extract table rows from the risk register section.
        in_table = False
        for line in content.splitlines():
            if line.startswith("| Object ID |"):
                in_table = True
                continue
            if in_table and line.startswith("|`"):
                cells = [c.strip().strip("`") for c in line.split("|") if c.strip()]
                if len(cells) >= 5:
                    rows.append(
                        {
                            "object_id": cells[0],
                            "object_type": cells[1],
                            "object_name": cells[2],
                            "severity": cells[3],
                            "reasons": [r.strip() for r in cells[4].split(";") if r.strip()],
                        }
                    )
        result = {
            "repo_name": repo_name_match.group(1) if repo_name_match else repo_root.name,
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "total_high_risk_items": int(total_match.group(1)) if total_match else len(rows),
            "risk_items": rows,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        console.print(f"[bold]Risk report written to {out}[/bold]")
    else:
        console.print(content)


# ---------------------------------------------------------------------------
# Review pack subcommands
# ---------------------------------------------------------------------------
review_pack_app = typer.Typer(
    name="review-pack",
    help="Generate a client-reviewable business pack.",
)
app.add_typer(review_pack_app, name="review-pack")


@review_pack_app.command("create")
@with_telemetry("review_pack_create")
def review_pack_create(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for the review pack."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON metadata."),
) -> None:
    """Generate a business-reviewable pack for stakeholders."""
    repo_root = _resolve_repo(repo)

    try:
        artifacts = generate_review_pack(repo_root, out)
    except (ValueError, RuntimeError, ResourceLimitExceeded) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        result = {
            "martenweave_version": __version__,
            "repo_name": repo_root.name,
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "artifact_count": len(artifacts),
            "artifacts": [
                {
                    "path": str(a.path),
                    "description": a.description,
                }
                for a in artifacts
            ],
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Review pack generated[/bold]")
    console.print(f"  Output: {out}")
    console.print(f"  Artifacts: {len(artifacts)}")
    for a in artifacts:
        console.print(f"  {a.path.name} — {a.description}")


@app.command("gap-report")
@with_telemetry("gap-report")
def gap_report(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate a consolidated gap summary report."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Run `martenweave build-index` first.[/yellow]")
        raise typer.Exit(code=1)

    report = generate_gap_summary_report(db_path, repo_root)

    if json_output:
        result = {
            "martenweave_version": __version__,
            "gaps_by_type": {
                key: {
                    "count": summary.count,
                    "sample_object_ids": summary.sample_object_ids,
                }
                for key, summary in report.gaps_by_type.items()
            },
            "total_gap_count": report.total_gap_count,
            "gap_score": report.gap_score,
            "top_objects": report.top_objects,
            "total_objects": report.total_objects,
            "sources_checked": report.sources_checked,
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print("[bold]Gap Summary Report[/bold]")
    console.print(f"  Total objects: {report.total_objects}")
    console.print(f"  Total gaps: {report.total_gap_count}")
    console.print(f"  Gap score: {report.gap_score}")
    console.print(f"  Sources checked: {', '.join(report.sources_checked)}")

    if report.gaps_by_type:
        console.print("")
        table = Table("Gap Type", "Count", "Sample Objects")
        for gap_type, summary in report.gaps_by_type.items():
            samples = ", ".join(summary.sample_object_ids) or "—"
            table.add_row(gap_type, str(summary.count), samples)
        console.print(table)

    if report.top_objects:
        console.print("")
        console.print("[bold]Top affected objects[/bold]")
        for obj_id in report.top_objects:
            console.print(f"  {obj_id}")

    if not report.gaps_by_type:
        console.print("[green]No gaps found.[/green]")

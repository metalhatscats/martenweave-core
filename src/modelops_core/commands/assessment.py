from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.table import Table

from modelops_core import __version__
from modelops_core.agents import (
    ProductOwnerAgent,
    ProductOwnerInput,
    ReadinessAgent,
    ReadinessInput,
)
from modelops_core.assessment.assessment_service import (
    generate_assessment_package,
)
from modelops_core.assessment.comparison import (
    AssessmentComparisonError,
    compare_assessments,
    write_assessment_comparison,
)
from modelops_core.commands._common import _resolve_repo, app, console
from modelops_core.config import load_repo_config, resolve_generated_path, resolve_model_path
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.index import build_index as _build_index
from modelops_core.issue_draft import (
    create_draft_from_change_request,
    create_draft_from_proposal,
    create_draft_from_validation,
    write_draft,
)
from modelops_core.pilot import demo_bundle as demo_bundle_service
from modelops_core.pilot import review as assessment_review_service
from modelops_core.pilot.sanitize import sanitize_assessment
from modelops_core.telemetry import with_telemetry

evidence_app = typer.Typer(
    name="evidence",
    help="Create reviewable proposals from local project evidence.",
)
app.add_typer(evidence_app, name="evidence")


@evidence_app.command("ingest")
@with_telemetry("evidence-ingest")
def evidence_ingest(
    source: Path = typer.Option(  # noqa: B008
        ..., "--from", help="Markdown/text note or CSV/XLSX validation report."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Explicit output path for the reviewable PatchProposal Markdown file."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output proposal metadata as JSON."),
) -> None:
    """Extract deterministic candidate Issues into a proposal without mutating canonical files."""
    from modelops_core.evidence_ingestion import (
        EvidenceIngestionError,
        ingest_evidence,
        write_evidence_proposal,
    )

    repo_root = _resolve_repo(repo)
    try:
        result = ingest_evidence(source, resolve_model_path(repo_root))
        output_path = write_evidence_proposal(result, out)
    except EvidenceIngestionError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            console.print(f"[red]Evidence ingestion failed: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    payload = {
        "proposal_id": result.proposal["id"],
        "path": str(output_path),
        "finding_count": result.finding_count,
        "source_sha256": result.source_sha256,
        "validation_status": "valid",
        "canonical_files_changed": False,
    }
    if json_output:
        print(json.dumps(payload, indent=2))
        return
    console.print(f"[green]Review proposal written: {output_path}[/green]")
    console.print(f"  Candidate findings: {result.finding_count}")
    console.print("  Canonical files changed: no")


# ---------------------------------------------------------------------------
# Issue-draft subcommands


draft_app = typer.Typer(
    name="issue-draft",
    help="Generate GitHub-ready issue drafts from model artifacts.",
)
app.add_typer(draft_app, name="issue-draft")


@draft_app.command("create")
def draft_create(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    change_request: str | None = typer.Option(
        None, "--change-request", help="ChangeRequest ID to draft from."
    ),
    proposal: str | None = typer.Option(None, "--proposal", help="PatchProposal ID to draft from."),
    from_validation: bool = typer.Option(
        False, "--from-validation", help="Draft from current validation results."
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None, "--output", help="Output file path (default: generated/issues/<id>.md)."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Generate a GitHub issue draft Markdown file."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    generated_path = resolve_generated_path(repo_root)

    sources_selected = sum(bool(x) for x in (change_request, proposal, from_validation))
    if sources_selected == 0:
        console.print(
            "[red]Specify one source: --change-request, --proposal, or --from-validation[/red]"
        )
        raise typer.Exit(code=1)
    if sources_selected > 1:
        console.print("[red]Specify only one source at a time.[/red]")
        raise typer.Exit(code=1)

    try:
        if change_request:
            draft = create_draft_from_change_request(model_path, change_request)
        elif proposal:
            draft = create_draft_from_proposal(model_path, generated_path, proposal)
        elif from_validation:
            draft = create_draft_from_validation(repo_root)
        else:
            # unreachable
            raise typer.Exit(code=1)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    path = write_draft(repo_root, draft, output_path=output)

    if json_output:
        result = {
            "title": draft.title,
            "body": draft.body,
            "source_type": draft.source_type,
            "source_id": draft.source_id,
            "labels": draft.labels,
            "suggested_assignees": draft.suggested_assignees,
            "path": str(path),
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[green]Draft written to {path}[/green]")
    console.print(f"  Title: {draft.title}")
    console.print(f"  Labels: {', '.join(draft.labels)}")
    if draft.suggested_assignees:
        console.print(f"  Suggested assignees: {', '.join(draft.suggested_assignees)}")


assessment_review_app = typer.Typer(
    name="assessment-review",
    help="Human disposition workflow for assessment findings.",
)
app.add_typer(assessment_review_app, name="assessment-review")


@assessment_review_app.command("set")
def assessment_review_set(
    assessment: Path = typer.Option(  # noqa: B008
        ..., "--assessment", help="Path to assessment manifest.json."
    ),
    finding_id: str = typer.Option(  # noqa: B008
        ..., "--finding-id", help="Stable finding ID from findings.json."
    ),
    disposition: str = typer.Option(  # noqa: B008
        ...,
        "--disposition",
        help=("Disposition: confirmed, false_positive, accepted_risk, deferred, resolved."),
    ),
    reviewer: str = typer.Option(  # noqa: B008
        ..., "--reviewer", help="Name or identifier of the reviewer."
    ),
    note: str | None = typer.Option(  # noqa: B008
        None, "--note", help="Optional review note."
    ),
) -> None:
    """Record a human disposition for a single assessment finding."""
    assessment_dir = assessment.resolve().parent
    try:
        record = assessment_review_service.set_review(
            assessment_dir=assessment_dir,
            finding_id=finding_id,
            disposition=disposition,
            reviewer=reviewer,
            note=note,
        )
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Review recorded for {finding_id}[/green]")
    console.print(f"  Disposition: {record['disposition']}")
    console.print(f"  Reviewer:    {record['reviewer']}")


@assessment_review_app.command("summary")
def assessment_review_summary(
    assessment: Path = typer.Option(  # noqa: B008
        ..., "--assessment", help="Path to assessment manifest.json."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Summarize current review state for an assessment."""
    assessment_dir = assessment.resolve().parent
    try:
        summary = assessment_review_service.summarize_reviews(assessment_dir)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        print(json.dumps(summary, indent=2, default=str, sort_keys=True))
        raise typer.Exit()

    console.print("[bold]Assessment Review Summary[/bold]")
    console.print(f"  Total findings:   {summary['total_findings']}")
    console.print(f"  Reviewed:         {summary['reviewed_count']}")
    console.print(f"  Unreviewed:       {summary['unreviewed_count']}")
    if summary["by_disposition"]:
        console.print("\n[bold]By disposition:[/bold]")
        for disp, count in sorted(summary["by_disposition"].items()):
            console.print(f"  {disp}: {count}")
    if summary["by_severity"]:
        console.print("\n[bold]By severity:[/bold]")
        for sev, count in sorted(summary["by_severity"].items()):
            console.print(f"  {sev}: {count}")
    if summary["by_category"]:
        console.print("\n[bold]By category:[/bold]")
        for cat, count in sorted(summary["by_category"].items()):
            console.print(f"  {cat}: {count}")
    if summary["unreviewed"]:
        console.print("\n[bold]Unreviewed findings:[/bold]")
        for fid in summary["unreviewed"][:20]:
            console.print(f"  - {fid}")
        if len(summary["unreviewed"]) > 20:
            console.print(f"  ... and {len(summary['unreviewed']) - 20} more")


@assessment_review_app.command("promote")
def assessment_review_promote(
    assessment: Path = typer.Option(  # noqa: B008
        ..., "--assessment", help="Path to assessment manifest.json."
    ),
    finding_id: str = typer.Option(  # noqa: B008
        ..., "--finding-id", help="Stable finding ID to promote."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
) -> None:
    """Promote a confirmed finding to a PatchProposal for human approval."""
    assessment_dir = assessment.resolve().parent
    repo_root = _resolve_repo(repo)
    try:
        proposal_path = assessment_review_service.promote_finding(
            assessment_dir=assessment_dir,
            repo_root=repo_root,
            finding_id=finding_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Promoted {finding_id} to PatchProposal[/green]")
    console.print(f"  {proposal_path}")


# ---------------------------------------------------------------------------
# Demo bundle subcommands


demo_bundle_app = typer.Typer(
    name="demo-bundle",
    help="Build deterministic, sanitized demo bundles for public sharing.",
)
app.add_typer(demo_bundle_app, name="demo-bundle")


@demo_bundle_app.command("build")
@with_telemetry("demo_bundle_build")
def demo_bundle_build(
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for the demo bundle."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    mapping: Path | None = typer.Option(  # noqa: B008
        None, "--mapping", help="Path to the synthetic mapping workbook."
    ),
    generated_at: str | None = typer.Option(
        None,
        "--generated-at",
        help="Optional ISO timestamp for deterministic output.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw manifest JSON."),
) -> None:
    """Build a deterministic, sanitized demo bundle from the golden assessment."""
    repo_root = _resolve_repo(repo) if repo else None
    mapping_path = mapping

    try:
        bundle = demo_bundle_service.build_demo_bundle(
            out_dir=out,
            repo_root=repo_root,
            mapping_path=mapping_path,
            generated_at=generated_at,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
            raise typer.Exit(code=1) from exc
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    validation_errors = demo_bundle_service.validate_demo_bundle(bundle.bundle_dir)

    if json_output:
        print(json.dumps(bundle.manifest, indent=2, sort_keys=True))
        raise typer.Exit()

    console.print("[bold]Demo bundle complete[/bold]")
    console.print(f"  Output: {bundle.bundle_dir}")
    console.print(f"  Artifacts: {bundle.manifest['artifact_count']}")
    if validation_errors:
        console.print("[yellow]Validation warnings:[/yellow]")
        for error in validation_errors:
            console.print(f"  - {error}")
    else:
        console.print("[green]Bundle validation passed[/green]")


# ---------------------------------------------------------------------------
# Assessment subcommands


assessment_app = typer.Typer(
    name="assessment",
    help="Migration Model Readiness Assessment.",
)
app.add_typer(assessment_app, name="assessment")


@assessment_app.command("run")
@with_telemetry("assessment_run")
def assessment_run(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for assessment package."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON metadata."),
) -> None:
    """Run a full migration readiness assessment and write the output package."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        console.print("[yellow]No index found. Building index first...[/yellow]")
        try:
            _build_index(repo_root=repo_root, allow_invalid=True)
        except (ValueError, ResourceLimitExceeded) as exc:
            if json_output:
                print(json.dumps({"error": str(exc)}, indent=2))
                raise typer.Exit(code=1) from exc
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc

    try:
        package = generate_assessment_package(repo_root, out)
    except (ValueError, ResourceLimitExceeded, RuntimeError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
            raise typer.Exit(code=1) from exc
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_output:
        result = {
            "martenweave_version": __version__,
            "repo_name": package.repo_name,
            "generated_at": package.generated_at,
            "readiness_level": package.readiness_level,
            "object_count": package.object_count,
            "gap_score": package.gap_score,
            "high_risk_count": package.high_risk_count,
            "artifacts": [
                {
                    "path": str(a.path),
                    "description": a.description,
                }
                for a in package.artifacts
            ],
        }
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    console.print(f"[bold]Assessment complete: {package.repo_name}[/bold]")
    console.print(f"  Readiness level: {package.readiness_level}")
    console.print(f"  Objects:         {package.object_count}")
    console.print(f"  Gap score:       {package.gap_score}")
    console.print(f"  High risk items: {package.high_risk_count}")
    console.print(f"  Output:          {out}")
    console.print("\n[bold]Artifacts generated[/bold]")
    for a in package.artifacts:
        console.print(f"  {a.path.name} — {a.description}")


@assessment_app.command("compare")
def assessment_compare(
    base_manifest: Path = typer.Argument(  # noqa: B008
        ..., help="Earlier assessment manifest.json."
    ),
    head_manifest: Path = typer.Argument(  # noqa: B008
        ..., help="Later assessment manifest.json."
    ),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Directory for Markdown and JSON comparison reports."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print the comparison JSON to stdout."),
) -> None:
    """Compare two assessment runs using stable finding IDs and input fingerprints."""
    try:
        report = compare_assessments(base_manifest, head_manifest)
        json_path, markdown_path = write_assessment_comparison(report, out)
    except AssessmentComparisonError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    payload = report.to_dict()
    payload["artifacts"] = {"json": str(json_path), "markdown": str(markdown_path)}
    if json_output:
        print(json.dumps(payload, indent=2))
        return
    counts = payload["counts"]
    console.print(
        f"[bold]Assessment comparison: {report.base_run_id} → {report.head_run_id}[/bold]"
    )
    console.print("  " + ", ".join(f"{kind}: {count}" for kind, count in sorted(counts.items())))
    console.print(f"  JSON: {json_path}")
    console.print(f"  Markdown: {markdown_path}")


@assessment_app.command("sanitize")
@with_telemetry("assessment_sanitize")
def assessment_sanitize(
    input_dir: Path = typer.Option(  # noqa: B008
        ..., "--input", help="Input assessment directory to sanitize."
    ),
    out: Path = typer.Option(  # noqa: B008
        ..., "--out", help="Output directory for the sanitized package."
    ),
    include_raw_datasets: bool = typer.Option(
        False,
        "--include-raw-datasets",
        help="Include raw dataset files from dataset_readiness/ (default: excluded).",
    ),
) -> None:
    """Create a sanitized, shareable copy of an assessment package."""
    if not input_dir.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/red]")
        raise typer.Exit(code=1)

    try:
        manifest = sanitize_assessment(
            input_dir,
            out,
            exclude_raw_datasets=not include_raw_datasets,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Sanitized package written to {out}[/green]")
    console.print(f"  Included: {len(manifest['included_files'])}")
    console.print(f"  Excluded: {len(manifest['excluded_files'])}")
    console.print(f"  Redacted: {len(manifest['redactions'])}")


# ---------------------------------------------------------------------------
# Agent subcommands


agent_app = typer.Typer(
    name="agent",
    help="Agentic workflow orchestrators.",
)
app.add_typer(agent_app, name="agent")


@agent_app.command("product-owner")
@with_telemetry("agent_product_owner")
def agent_product_owner(
    source: Path = typer.Argument(  # noqa: B008
        ..., help="Path to a note/issue Markdown file or a ChangeRequest ID."
    ),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    source_type: str = typer.Option(
        "auto",
        "--source-type",
        help="Input type: auto, issue, note, change_request.",
    ),
    max_iterations: int = typer.Option(
        3,
        "--max-iterations",
        help="Maximum proposal refinement iterations.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview intended changes without writing files.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Run the ProductOwner agent loop on a product input."""
    from modelops_core.config import load_repo_config

    repo_root = _resolve_repo(repo)
    config = load_repo_config(repo_root)
    if config is None:
        if json_output:
            print(json.dumps({"error": "No modelops.config.yaml found."}, indent=2))
        else:
            console.print("[red]No modelops.config.yaml found.[/red]")
        raise typer.Exit(code=1)

    inferred_type = source_type
    raw_text = ""
    source_id: str | None = None

    if inferred_type == "auto":
        if source.suffix.lower() in {".md", ".txt"}:
            inferred_type = "issue" if "issue" in source.name.lower() else "note"
        else:
            inferred_type = "change_request"

    if inferred_type == "change_request":
        source_id = source.name
        cr_path = resolve_model_path(repo_root) / "change-requests" / f"{source_id}.md"
        if not cr_path.exists():
            if json_output:
                print(json.dumps({"error": f"ChangeRequest not found: {source_id}"}, indent=2))
            else:
                console.print(f"[red]ChangeRequest not found: {source_id}[/red]")
            raise typer.Exit(code=1)
        raw_text = cr_path.read_text(encoding="utf-8")
    else:
        if not source.exists():
            if json_output:
                print(json.dumps({"error": f"File not found: {source}"}, indent=2))
            else:
                console.print(f"[red]File not found: {source}[/red]")
            raise typer.Exit(code=1)
        raw_text = source.read_text(encoding="utf-8")
        source_id = source.stem

    agent = ProductOwnerAgent(dry_run=dry_run, max_iterations=max_iterations)
    result = agent.run(
        ProductOwnerInput(
            source_type=inferred_type,
            raw_text=raw_text,
            source_id=source_id,
            repo_root=repo_root,
        )
    )

    if json_output:
        print(
            json.dumps(
                {
                    "success": result.success,
                    "iterations": result.iterations,
                    "proposal_id": result.proposal_id,
                    "proposal_path": str(result.proposal_path) if result.proposal_path else None,
                    "change_request_id": result.change_request_id,
                    "change_request_path": (
                        str(result.change_request_path) if result.change_request_path else None
                    ),
                    "validation_status": result.validation_status,
                    "impact_summary": result.impact_summary,
                    "draft_issue_path": (
                        str(result.draft_issue_path) if result.draft_issue_path else None
                    ),
                    "notification_event_ids": result.notification_event_ids,
                    "assumptions": result.assumptions,
                    "human_checks": result.human_checks,
                    "error_message": result.error_message,
                },
                indent=2,
                default=str,
            )
        )
        raise typer.Exit(code=0 if result.success else 1)

    if result.success:
        console.print(
            f"[green]ProductOwner loop completed in {result.iterations} iteration(s)[/green]"
        )
    else:
        console.print(
            f"[yellow]ProductOwner loop finished in {result.iterations} iteration(s) "
            "but did not produce a valid proposal.[/yellow]"
        )

    console.print(f"  Proposal:       {result.proposal_id or '—'}")
    console.print(f"  Validation:     {result.validation_status or '—'}")
    if result.proposal_path:
        console.print(f"  Proposal path:  {result.proposal_path}")
    if result.change_request_id:
        console.print(f"  ChangeRequest:  {result.change_request_id}")
    if result.draft_issue_path:
        console.print(f"  Issue draft:    {result.draft_issue_path}")
    if result.impact_summary:
        affected = result.impact_summary.get("affected_object_count")
        if affected is not None:
            console.print(f"  Affected objects: {affected}")

    if result.assumptions:
        console.print("\n[bold]Assumptions[/bold]")
        for assumption in result.assumptions:
            console.print(f"  - {assumption}")

    if result.human_checks:
        console.print("\n[bold]Human checks[/bold]")
        for check in result.human_checks:
            console.print(f"  - {check}")

    if result.error_message:
        console.print(f"\n[red]Error: {result.error_message}[/red]")
        raise typer.Exit(code=1)


def _run_readiness_cli(
    repo_root: Path,
    profile: str,
    dry_run: bool,
    json_output: bool,
    require_config: bool = True,
) -> None:
    """Shared implementation for the readiness CLI commands."""
    if require_config:
        config = load_repo_config(repo_root)
        if config is None:
            if json_output:
                print(json.dumps({"error": "No modelops.config.yaml found."}, indent=2))
            else:
                console.print("[red]No modelops.config.yaml found.[/red]")
            raise typer.Exit(code=1)

    agent = ReadinessAgent(dry_run=dry_run)
    result = agent.run(ReadinessInput(repo_root=repo_root, profile=profile))

    if json_output:
        print(
            json.dumps(
                {
                    "ready": result.ready,
                    "profile": result.profile,
                    "gate_count": result.gate_count,
                    "failed_gates": result.failed_gates,
                    "blockers": [
                        {
                            "gate": b.gate,
                            "severity": b.severity,
                            "message": b.message,
                            "object_id": b.object_id,
                            "issue_id": b.issue_id,
                        }
                        for b in result.blockers
                    ],
                    "issues_created": result.issues_created,
                    "proposal_created": result.proposal_created,
                    "draft_issue_path": (
                        str(result.draft_issue_path) if result.draft_issue_path else None
                    ),
                    "notification_event_ids": result.notification_event_ids,
                },
                indent=2,
                default=str,
            )
        )
        raise typer.Exit(code=0 if result.ready else 1)

    if result.ready:
        console.print(
            f"[green]Repository is ready for {result.profile}: "
            f"{result.gate_count}/{result.gate_count} gates passed[/green]"
        )
    else:
        console.print(
            f"[yellow]Repository is not ready for {result.profile}: "
            f"{len(result.failed_gates)} gate(s) failed[/yellow]"
        )

    console.print(f"\n[bold]Gates checked:[/bold] {result.gate_count}")
    if result.failed_gates:
        console.print(f"[bold]Failed gates:[/bold] {', '.join(result.failed_gates)}")
    if result.issues_created:
        console.print(f"[bold]Issues created:[/bold] {len(result.issues_created)}")
        for issue_id in result.issues_created:
            console.print(f"  - {issue_id}")
    if result.proposal_created:
        console.print(f"[bold]Proposal created:[/bold] {result.proposal_created}")
    if result.draft_issue_path:
        console.print(f"[bold]Draft issue:[/bold] {result.draft_issue_path}")
    if result.notification_event_ids:
        console.print(f"[bold]Notifications:[/bold] {len(result.notification_event_ids)}")

    if result.blockers:
        table = Table("Gate", "Severity", "Object", "Message")
        for b in result.blockers:
            table.add_row(b.gate, b.severity, b.object_id or "—", b.message)
        console.print("\n[bold]Blockers[/bold]")
        console.print(table)

    raise typer.Exit(code=0 if result.ready else 1)


@agent_app.command("readiness")
@with_telemetry("agent_readiness")
def agent_readiness(
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
    """Run readiness gates and create Issue/Proposal artifacts for blockers."""
    repo_root = _resolve_repo(repo)
    _run_readiness_cli(repo_root, profile, dry_run, json_output, require_config=True)

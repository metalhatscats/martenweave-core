"""First-value local workspace command."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer

from modelops_core.commands._common import app, console
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.imports import infer_model_from_profile
from modelops_core.patching.patch_proposal_service import write_patch_proposal
from modelops_core.patching.patch_validator import validate_patch_proposal
from modelops_core.repository.scaffold import init_repository
from modelops_core.run import generate_dataset_readiness_report, write_readiness_report

_SUPPORTED_SUFFIXES = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".xml": "xml",
    ".json": "json",
}


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _proposal_from_profile(
    profile: dict[str, Any], model_path: Path, dataset_id: str
) -> Path | None:
    """Write a draft-only inference proposal without touching canonical model objects."""
    proposal = infer_model_from_profile(profile, dataset_id=dataset_id)
    operations = proposal.get("operations", [])
    if not operations:
        return None
    validation = validate_patch_proposal(proposal)
    proposal["validation_status"] = (
        "invalid" if any(result.severity == "ERROR" for result in validation) else "valid"
    )
    proposal["validation_results"] = [result.model_dump(mode="json") for result in validation]
    return write_patch_proposal(proposal, model_path)


def _default_workspace(input_path: Path) -> Path:
    return input_path.parent / f"{input_path.stem}-martenweave-workspace"


@app.command()
def start(
    input_file: Path = typer.Argument(..., help="Local CSV, XLSX, XML, or JSON file to assess."),  # noqa: B008
    out: Path | None = typer.Option(  # noqa: B008
        None, "--out", help="New local workspace directory (default: next to the input)."
    ),
    name: str | None = typer.Option(None, "--name", help="Optional workspace name."),
    open_browser: bool = typer.Option(
        False,
        "--open/--no-open",
        help="Open the Workbench URL after preparation (default: print the URL only).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print the start manifest as JSON."),
) -> None:
    """Create a local workspace and deterministic readiness result from one file.

    This command never applies inferred objects.  It creates a minimal local
    workspace, writes disposable profile/readiness artifacts, and records any
    inferred model changes as a draft PatchProposal for human review.
    """
    if not input_file.is_file():
        console.print(f"[red]Input file not found: {input_file}[/red]")
        raise typer.Exit(code=1)
    format_name = _SUPPORTED_SUFFIXES.get(input_file.suffix.lower())
    if format_name is None:
        supported = ", ".join(sorted(_SUPPORTED_SUFFIXES))
        console.print(
            f"[red]Unsupported input format '{input_file.suffix}'. Supported: {supported}.[/red]"
        )
        raise typer.Exit(code=1)

    workspace = (out or _default_workspace(input_file)).resolve()
    if workspace.exists() and any(workspace.iterdir()):
        console.print(f"[red]Workspace is not empty: {workspace}[/red]")
        raise typer.Exit(code=1)

    init_repository(workspace, name=name or f"{input_file.stem} readiness workspace")
    generated_root = resolve_generated_path(workspace)
    reports_dir = generated_root / "readiness"
    report = generate_dataset_readiness_report(
        repo_root=workspace,
        dataset_path=input_file.resolve(),
        check_model=True,
    )
    readiness_json, readiness_markdown = write_readiness_report(report, reports_dir)
    profile_path = generated_root / "dataset_profiles" / f"{input_file.stem}.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(report.dataset_profile, indent=2, sort_keys=True), encoding="utf-8"
    )
    proposal_path = _proposal_from_profile(
        report.dataset_profile, resolve_model_path(workspace), input_file.stem
    )

    manifest = {
        "schema_version": "1.0",
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input": {
            "path": str(input_file.resolve()),
            "format": format_name,
            "sha256": _sha256(input_file),
        },
        "workspace": str(workspace),
        "readiness": {
            "verdict": report.verdict,
            "dataset_gaps": len(report.dataset_gaps),
            "model_gaps": len(report.model_gaps),
            "validation_errors": report.validation["error_count"],
            "validation_warnings": report.validation["warning_count"],
        },
        "checks": {
            "unmapped_columns": "evaluated",
            "ownership_gaps": "evaluated through canonical validation",
            "invalid_values": "not_assessed_without_governed_value_lists",
            "transformation_risks": "represented by deterministic dataset/model gaps",
        },
        "generated_outputs": {
            "profile": str(profile_path.relative_to(workspace)),
            "readiness_json": str(readiness_json.relative_to(workspace)),
            "readiness_markdown": str(readiness_markdown.relative_to(workspace)),
            "draft_proposal": str(proposal_path.relative_to(workspace)) if proposal_path else None,
        },
        "canonical_model": {
            "created_workspace_seed_only": True,
            "input_never_overwrote_canonical_files": True,
            "draft_proposal_requires_validation_and_human_review": True,
        },
        "ai": {
            "configured": False,
            "message": "No AI provider is required for profiling, readiness, or draft inference.",
        },
        "workbench": {
            "url": "http://127.0.0.1:8000",
            "command": f"martenweave workbench --repo {workspace}",
        },
    }
    manifest_path = generated_root / "start_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    if open_browser:
        import webbrowser

        webbrowser.open(manifest["workbench"]["url"])
    if json_output:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return
    console.print(f"[green]Local readiness workspace created:[/green] {workspace}")
    console.print(f"  Detected input: {format_name}")
    console.print(f"  Readiness: {report.verdict}")
    console.print(f"  Report: {readiness_markdown}")
    if proposal_path:
        console.print(f"  Draft proposal (not applied): {proposal_path}")
    console.print(f"  Manifest: {manifest_path}")
    console.print(f"  Workbench: {manifest['workbench']['url']}")
    console.print(f"  Start it with: {manifest['workbench']['command']}")

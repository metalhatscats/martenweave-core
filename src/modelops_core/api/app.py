"""FastAPI application for Martenweave local API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from modelops_core.config import load_repo_config, resolve_generated_path, resolve_model_path
from modelops_core.exports import export_model_csv, export_model_xlsx
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.patching.apply_service import apply_patch_proposal, dry_run_patch_proposal
from modelops_core.patching.patch_validator import validate_patch_proposal
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation import validate_objects

app = FastAPI(
    title="Martenweave API",
    description="Lightweight local API for the agentic data model registry.",
    version="0.1.0",
)


def _resolve_repo(repo: str | None) -> Path:
    return Path(repo).resolve() if repo else Path.cwd().resolve()


@app.get("/health")
def health(repo: str | None = Query(None, description="Path to model repository")) -> dict:
    """Repository health summary."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not db_path.exists():
        return {"status": "no_index", "message": "Run build-index first."}

    # Basic health: count objects in index
    # For MVP, return object count and index presence
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)
    return {
        "status": "healthy",
        "repository": str(repo_root),
        "indexed": True,
        "canonical_files": len(files),
    }


@app.get("/objects")
def list_objects(
    repo: str | None = Query(None, description="Path to model repository"),
    obj_type: str | None = Query(None, alias="type", description="Filter by object type"),
) -> list[dict[str, Any]]:
    """List canonical objects, optionally filtered by type."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)
    results: list[dict[str, Any]] = []

    for file_path in files:
        parsed = parse_file(file_path)
        if parsed.parser_error or not parsed.frontmatter:
            continue
        fm = dict(parsed.frontmatter)
        if obj_type and str(fm.get("type", "")) != obj_type:
            continue
        fm["source_file"] = Path(parsed.source_path).name
        results.append(fm)

    return results


@app.get("/objects/{obj_id}")
def get_object(
    obj_id: str,
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Get a single canonical object by ID."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)

    for file_path in files:
        parsed = parse_file(file_path)
        if parsed.parser_error or not parsed.frontmatter:
            continue
        if str(parsed.frontmatter.get("id", "")) == obj_id:
            result = dict(parsed.frontmatter)
            result["source_file"] = Path(parsed.source_path).name
            result["body"] = parsed.body
            return result

    raise HTTPException(status_code=404, detail=f"Object {obj_id} not found")


@app.get("/validate")
def validate(
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Run deterministic validation on the repository."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)
    parsed_objects = [parse_file(f) for f in files]
    config = load_repo_config(repo_root)
    enabled_packs = config.enabled_domain_packs if config else None
    summary = validate_objects(parsed_objects, enabled_packs)
    return {
        "is_valid": summary.is_valid,
        "error_count": summary.error_count,
        "warning_count": summary.warning_count,
        "results": [
            {
                "severity": str(r.severity),
                "code": r.code,
                "message": r.message,
                "object_id": r.object_id,
                "suggested_fix": r.suggested_fix,
            }
            for r in summary.results
        ],
    }


@app.get("/impact/{obj_id}")
def impact(
    obj_id: str,
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Generate impact report for an object."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not db_path.exists():
        raise HTTPException(status_code=400, detail="Index not found. Run build-index first.")

    report = generate_impact_report(db_path, obj_id)
    return {
        "object_id": obj_id,
        "upstream": report.upstream,
        "downstream": report.downstream,
        "total_affected": len(report.upstream) + len(report.downstream),
    }


@app.get("/proposals")
def list_proposals(
    repo: str | None = Query(None, description="Path to model repository"),
) -> list[dict[str, Any]]:
    """List all PatchProposals in the repository."""
    repo_root = _resolve_repo(repo)
    proposals_dir = resolve_model_path(repo_root) / "patch-proposals"
    if not proposals_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for f in sorted(proposals_dir.glob("PP-*.md")):
        parsed = parse_file(f)
        fm = parsed.frontmatter or {}
        results.append(
            {
                "id": fm.get("id", f.stem),
                "status": fm.get("status", "pending_review"),
                "validation_status": fm.get("validation_status", "pending"),
                "applied_at": fm.get("applied_at"),
            }
        )
    return results


@app.get("/proposals/{proposal_id}")
def get_proposal(
    proposal_id: str,
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Get a PatchProposal by ID."""
    repo_root = _resolve_repo(repo)
    proposal_path = resolve_model_path(repo_root) / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    return dict(fm)


@app.post("/proposals/{proposal_id}/validate")
def validate_proposal(
    proposal_id: str,
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Validate a PatchProposal."""
    repo_root = _resolve_repo(repo)
    proposal_path = resolve_model_path(repo_root) / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    parsed = parse_file(proposal_path)
    fm = parsed.frontmatter or {}
    results = validate_patch_proposal(fm)
    return {
        "proposal_id": proposal_id,
        "valid": all(r.severity != "ERROR" for r in results),
        "errors": sum(1 for r in results if r.severity == "ERROR"),
        "warnings": sum(1 for r in results if r.severity == "WARNING"),
        "results": [
            {
                "severity": str(r.severity),
                "code": r.code,
                "message": r.message,
                "suggested_fix": r.suggested_fix,
            }
            for r in results
        ],
    }


@app.post("/proposals/{proposal_id}/dry-run")
def dry_run_proposal(
    proposal_id: str,
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Dry-run apply a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    try:
        result = dry_run_patch_proposal(model_path, proposal_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "proposal_id": proposal_id,
        "would_change": result.would_change,
        "operations_preview": result.operations_preview,
        "error": result.error,
    }


@app.post("/proposals/{proposal_id}/apply")
def apply_proposal(
    proposal_id: str,
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Apply an accepted PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    try:
        result = apply_patch_proposal(model_path, proposal_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "proposal_id": proposal_id,
        "changed_files": result.changed_files,
        "audit_event_written": result.audit_event_written,
        "index_rebuilt": result.index_rebuilt,
    }


@app.post("/export")
def export(
    repo: str | None = Query(None, description="Path to model repository"),
    format: str = Query("csv", alias="format", description="Export format: csv or xlsx"),
) -> dict[str, Any]:
    """Export canonical model to CSV or XLSX."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)

    if format.lower() == "csv":
        written = export_model_csv(model_path)
        return {"format": "csv", "files": [str(f) for f in written]}
    elif format.lower() == "xlsx":
        path = export_model_xlsx(model_path)
        return {"format": "xlsx", "file": str(path)}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {format}")

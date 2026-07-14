"""FastAPI application for Martenweave local API."""

# FastAPI dependencies are intentionally used as argument defaults.
# ruff: noqa: B008

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query

from modelops_core import __version__
from modelops_core.api.workspace import (
    WorkspaceContext,
    _is_safe_path,
    _redact_path,
    get_workspace,
    require_write_access,
    workspace_name,
)
from modelops_core.approval.risk_service import compute_proposal_risk
from modelops_core.change_request.service import find_approved_cr_for_proposal
from modelops_core.config import load_repo_config
from modelops_core.exports import export_model_csv, export_model_xlsx
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.patching.apply_service import apply_patch_proposal, dry_run_patch_proposal
from modelops_core.patching.patch_validator import validate_patch_proposal
from modelops_core.repository import parse_file, scan_repository
from modelops_core.run import generate_dataset_readiness_report
from modelops_core.trace import trace_object
from modelops_core.validation import validate_objects


def init_app(workspace: WorkspaceContext) -> FastAPI:
    """Create a FastAPI app bound to a single workspace."""
    ws_dep = get_workspace(workspace)
    write_dep = require_write_access(workspace)

    app = FastAPI(
        title="Martenweave API",
        description="Lightweight local API for the agentic data model registry.",
        version=__version__,
    )

    @app.get("/capabilities")
    def capabilities(ws: WorkspaceContext = Depends(ws_dep)) -> dict[str, Any]:
        """Return workspace metadata and mutation permissions."""
        return {
            "workspace_name": workspace_name(ws),
            "version": __version__,
            "read_only": ws.read_only,
            "allow_mutations": not ws.read_only,
            "session_required": True,
            "allowed_origins": ws.allowed_origins,
        }

    @app.get("/health")
    def health(ws: WorkspaceContext = Depends(ws_dep)) -> dict[str, Any]:
        """Repository health summary."""
        db_path = ws.generated_path / "modelops.db"
        if not db_path.exists():
            return {"status": "no_index", "message": "Run build-index first."}

        files = scan_repository(ws.model_path)
        return {
            "status": "healthy",
            "repository": str(ws.repo_root),
            "indexed": True,
            "canonical_files": len(files),
        }

    @app.get("/objects")
    def list_objects(
        obj_type: str | None = Query(None, alias="type", description="Filter by object type"),
        ws: WorkspaceContext = Depends(ws_dep),
    ) -> list[dict[str, Any]]:
        """List canonical objects, optionally filtered by type."""
        files = scan_repository(ws.model_path)
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
    def get_object(obj_id: str, ws: WorkspaceContext = Depends(ws_dep)) -> dict[str, Any]:
        """Get a single canonical object by ID."""
        files = scan_repository(ws.model_path)

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
    def validate(ws: WorkspaceContext = Depends(ws_dep)) -> dict[str, Any]:
        """Run deterministic validation on the repository."""
        files = scan_repository(ws.model_path)
        parsed_objects = [parse_file(f) for f in files]
        config = load_repo_config(ws.repo_root)
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

    @app.get("/trace/{obj_id}")
    def trace(
        obj_id: str,
        direction: str = Query("both", description="upstream, downstream, or both"),
        max_depth: int = Query(5, description="Maximum traversal depth"),
        ws: WorkspaceContext = Depends(ws_dep),
    ) -> dict[str, Any]:
        """Trace upstream and downstream relationships for an object."""
        db_path = ws.generated_path / "modelops.db"
        if not db_path.exists():
            raise HTTPException(status_code=400, detail="Index not found. Run build-index first.")

        result = trace_object(db_path, obj_id, max_depth=max_depth, direction=direction)
        if result.root_object_type is None:
            raise HTTPException(status_code=404, detail=f"Object {obj_id} not found")

        return {
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

    @app.get("/impact/{obj_id}")
    def impact(obj_id: str, ws: WorkspaceContext = Depends(ws_dep)) -> dict[str, Any]:
        """Generate impact report for an object."""
        db_path = ws.generated_path / "modelops.db"
        if not db_path.exists():
            raise HTTPException(status_code=400, detail="Index not found. Run build-index first.")

        report = generate_impact_report(db_path, obj_id)
        if report.root_object_type is None:
            raise HTTPException(status_code=404, detail=f"Object {obj_id} not found")

        return {
            "object_id": report.root_object_id,
            "root_object_type": report.root_object_type,
            "root_object_name": report.root_object_name,
            "upstream": [
                {
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "object_name": o.object_name,
                    "relationship_type": o.relationship_type,
                    "depth": o.depth,
                }
                for o in report.upstream_objects
            ],
            "downstream": [
                {
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "object_name": o.object_name,
                    "relationship_type": o.relationship_type,
                    "depth": o.depth,
                }
                for o in report.downstream_objects
            ],
            "total_affected": len(report.affected_objects),
        }

    @app.get("/proposals")
    def list_proposals(ws: WorkspaceContext = Depends(ws_dep)) -> list[dict[str, Any]]:
        """List all PatchProposals in the repository."""
        proposals_dir = ws.model_path / "patch-proposals"
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
    def get_proposal(proposal_id: str, ws: WorkspaceContext = Depends(ws_dep)) -> dict[str, Any]:
        """Get a PatchProposal by ID."""
        proposal_path = ws.model_path / "patch-proposals" / f"{proposal_id}.md"
        if not proposal_path.exists():
            raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

        parsed = parse_file(proposal_path)
        fm = parsed.frontmatter or {}
        return dict(fm)

    @app.post("/proposals/{proposal_id}/validate")
    def validate_proposal(
        proposal_id: str,
        ws: WorkspaceContext = Depends(ws_dep),
        _writable: WorkspaceContext = Depends(write_dep),
    ) -> dict[str, Any]:
        """Validate a PatchProposal."""
        proposal_path = ws.model_path / "patch-proposals" / f"{proposal_id}.md"
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
        ws: WorkspaceContext = Depends(ws_dep),
        _writable: WorkspaceContext = Depends(write_dep),
    ) -> dict[str, Any]:
        """Dry-run apply a PatchProposal."""
        try:
            result = dry_run_patch_proposal(ws.model_path, proposal_id)
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
        skip_risk_check: bool = Query(
            False, description="Skip high-risk proposal blocking (not recommended)"
        ),
        ws: WorkspaceContext = Depends(ws_dep),
        _writable: WorkspaceContext = Depends(write_dep),
    ) -> dict[str, Any]:
        """Apply an accepted PatchProposal."""
        proposal_path = ws.model_path / "patch-proposals" / f"{proposal_id}.md"
        if not proposal_path.exists():
            raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

        parsed = parse_file(proposal_path)
        fm = parsed.frontmatter or {}
        operations = fm.get("operations", [])

        risk = compute_proposal_risk(operations, ws.model_path)
        approved_change_request_id: str | None = None
        if risk.risk_level == "high":
            # High-risk proposals always require an approved ChangeRequest, even when
            # skip_risk_check is requested.
            approved_cr = find_approved_cr_for_proposal(ws.model_path, proposal_id)
            if approved_cr is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"High-risk proposal {proposal_id} requires an approved "
                        "ChangeRequest. skip_risk_check cannot bypass this gate."
                    ),
                )
            approved_change_request_id = approved_cr.get("id")
        elif risk.requires_approval and not skip_risk_check:
            approved_cr = find_approved_cr_for_proposal(ws.model_path, proposal_id)
            if approved_cr is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Approval required for {proposal_id}. Risk level: {risk.risk_level}. "
                        "Link an approved ChangeRequest or use skip_risk_check."
                    ),
                )
            approved_change_request_id = approved_cr.get("id")

        try:
            result = apply_patch_proposal(
                ws.model_path,
                proposal_id,
                skip_risk_check=approved_change_request_id is not None,
                approved_change_request_id=approved_change_request_id,
            )
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "proposal_id": proposal_id,
            "changed_files": [_redact_path(Path(f), ws.repo_root) for f in result.changed_files],
            "audit_event_written": result.audit_event_written,
            "index_rebuilt": result.index_rebuilt,
        }

    @app.post("/export")
    def export(
        format: str = Query("csv", alias="format", description="Export format: csv or xlsx"),
        ws: WorkspaceContext = Depends(ws_dep),
        _writable: WorkspaceContext = Depends(write_dep),
    ) -> dict[str, Any]:
        """Export canonical model to CSV or XLSX."""
        if format.lower() == "csv":
            written = export_model_csv(ws.model_path)
            return {
                "format": "csv",
                "files": [_redact_path(f, ws.repo_root) for f in written],
            }
        elif format.lower() == "xlsx":
            path = export_model_xlsx(ws.model_path)
            return {"format": "xlsx", "file": _redact_path(path, ws.repo_root)}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {format}")

    def _resolve_dataset(dataset: str, ws: WorkspaceContext) -> Path:
        """Resolve and validate a user-supplied dataset path."""
        dataset_path = Path(dataset)
        if not _is_safe_path(dataset_path, ws.allowed_roots):
            raise HTTPException(
                status_code=400,
                detail=f"Dataset path is outside the workspace: {dataset}",
            )
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset}")
        return dataset_path

    @app.post("/gaps")
    def gaps(
        dataset: str = Query(..., description="Path to CSV or XLSX dataset file"),
        check_model: bool = Query(False, description="Also include model-side gaps"),
        ws: WorkspaceContext = Depends(ws_dep),
        _writable: WorkspaceContext = Depends(write_dep),
    ) -> dict[str, Any]:
        """Detect dataset-to-model gaps for a CSV or XLSX file.

        The endpoint builds (or refreshes) the SQLite index for the repository so
        the report reflects the current canonical files.
        """
        dataset_path = _resolve_dataset(dataset, ws)

        try:
            report = generate_dataset_readiness_report(
                repo_root=ws.repo_root,
                dataset_path=dataset_path,
                check_model=check_model,
                dry_run=True,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "dataset_id": dataset_path.stem,
            "verdict": report.verdict,
            "coverage": report.coverage,
            "matches": report.matches,
            "dataset_gaps": report.dataset_gaps,
            "model_gaps": report.model_gaps,
        }

    @app.post("/dataset-readiness")
    def dataset_readiness(
        dataset: str = Query(..., description="Path to CSV or XLSX dataset file"),
        check_model: bool = Query(False, description="Also include model-side gaps"),
        promote_to_proposal: bool = Query(
            False, description="Promote dataset gaps to a draft PatchProposal"
        ),
        issue_draft: bool = Query(False, description="Generate a GitHub-ready issue draft"),
        ws: WorkspaceContext = Depends(ws_dep),
        _writable: WorkspaceContext = Depends(write_dep),
    ) -> dict[str, Any]:
        """Run the full dataset-readiness workflow.

        By default this returns a read-only readiness report. Pass
        ``promote_to_proposal`` or ``issue_draft`` to persist artifacts for human
        review, following the same AI-proposes/human-approves model as the CLI.
        """
        dataset_path = _resolve_dataset(dataset, ws)

        try:
            report = generate_dataset_readiness_report(
                repo_root=ws.repo_root,
                dataset_path=dataset_path,
                check_model=check_model,
                promote_to_proposal=promote_to_proposal,
                issue_draft=issue_draft,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return report.__dict__

    return app

"""Versioned v1 API router for the Martenweave local API."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from modelops_core import __version__
from modelops_core.api.models import (
    ActivityEventItem,
    ActivityResponse,
    ApiCapabilities,
    AssessmentManifestItem,
    AssessmentManifestResponse,
    CapabilityEntry,
    ChangedObjectItem,
    DiffResultResponse,
    ExportResponse,
    FieldChangeItem,
    FindingItem,
    FindingPromoteRequest,
    FindingPromoteResponse,
    FindingResponse,
    FindingReviewRequest,
    FindingReviewResponse,
    ImportPreviewResponse,
    ImportProfileResponse,
    ImportProposeResponse,
    ImportValidateResponse,
    ObjectDetailResponse,
    PaginatedSearchResponse,
    RecoveryActionEntry,
    RecoveryResponse,
    RecoveryStateEntry,
    RelatedObjectItem,
    ReportArtifactItem,
    ReportArtifactResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    SearchResultItem,
    WorkspaceCreateRequest,
    WorkspaceSummary,
    WorkspaceValidateRequest,
    WorkspaceValidateResponse,
)
from modelops_core.api.recovery import (
    AI_UNAVAILABLE_ACTION,
    BUILD_INDEX,
    INSPECT_READ_ONLY,
    workspace_recovery_states,
)
from modelops_core.api.workspace import (
    configure_workspace,
    current_mutation_token,
    mutation_enabled,
    require_mutation_token,
    resolve_workspace,
    resolve_workspace_input,
    workspace_is_bound,
    workspace_label,
)
from modelops_core.assessment.assessment_service import generate_review_pack, generate_risk_report
from modelops_core.assessment.comparison import AssessmentComparisonError, compare_assessments
from modelops_core.assessment.finding_contract import AssessmentFinding
from modelops_core.config import load_repo_config, resolve_generated_path, resolve_model_path
from modelops_core.diff.diff_service import diff_repositories
from modelops_core.exports.export_service import export_model_csv, export_model_xlsx
from modelops_core.imports.dataset_profiler import (
    dataset_profile_to_dict,
    profile_csv,
    profile_xlsx,
)
from modelops_core.imports.model_sheet_import_service import (
    _detect_formulas,
    _load_existing_objects,
    _read_xlsx,
    _validate_import,
    import_model_sheet_xlsx,
)
from modelops_core.index import build_index
from modelops_core.index.query_service import (
    get_object_by_id,
    list_related_objects,
    search_objects,
)
from modelops_core.patching.patch_proposal_service import write_patch_proposal
from modelops_core.pilot.outcome import generate_pilot_outcome, write_pilot_outcome
from modelops_core.pilot.review import promote_finding, set_review
from modelops_core.reports.audit_service import AuditEventService
from modelops_core.reports.gap_summary import generate_gap_summary_report
from modelops_core.reports.model_summary_service import (
    generate_model_summary,
    model_summary_to_markdown,
)
from modelops_core.reports.scorecard_service import generate_scorecard
from modelops_core.repository import scan_repository
from modelops_core.repository.scaffold import available_templates, init_repository

router = APIRouter(prefix="/api/v1")


def _workspace_summary(repo_root: Path) -> dict[str, Any]:
    """Return a safe workspace summary for the given repository root."""
    generated_root = resolve_generated_path(repo_root)
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path) if model_path.exists() else []
    return {
        "repository_label": workspace_label() if workspace_is_bound() else str(repo_root),
        "version": __version__,
        "api_version": "v1",
        "indexed": (generated_root / "modelops.db").exists(),
        "canonical_files": len(files),
        "read_only": not os.access(repo_root, os.W_OK),
    }


def _validate_repository_path(repo_root: Path) -> dict[str, Any]:
    """Check that a directory looks like a usable model repository."""
    errors: list[str] = []
    warnings: list[str] = []

    if not repo_root.is_absolute():
        errors.append("Repository path must be absolute.")
    if not repo_root.exists():
        errors.append(f"Directory does not exist: {repo_root}")
    elif not repo_root.is_dir():
        errors.append(f"Path is not a directory: {repo_root}")

    if repo_root.exists() and repo_root.is_dir() and not os.access(repo_root, os.R_OK):
        errors.append(f"Directory is not readable: {repo_root}")

    model_path = resolve_model_path(repo_root)
    config_path = repo_root / "modelops.config.yaml"

    if not model_path.exists() and not config_path.exists():
        errors.append("Directory does not contain a model/ folder or modelops.config.yaml file.")
    elif config_path.exists():
        from modelops_core.config import load_repo_config

        config = load_repo_config(repo_root)
        if config is None:
            errors.append("modelops.config.yaml exists but could not be parsed.")

    generated_root = resolve_generated_path(repo_root)
    if not (generated_root / "modelops.db").exists():
        warnings.append("Index is missing. Run build-index after opening.")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        **_workspace_summary(repo_root),
    }


_REPORT_EXTENSIONS = frozenset({".csv", ".json", ".md", ".pdf", ".xlsx"})


def _resolve_repo(repo: str | None) -> Path:
    return resolve_workspace(repo)


def _workspace_health(repo_root: Path) -> dict[str, Any]:
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)
    return {
        "indexed": db_path.exists(),
        "canonical_files": len(files),
        "repository": workspace_label() if workspace_is_bound() else str(repo_root),
    }


@router.get("/capabilities", response_model=ApiCapabilities)
def capabilities(
    repo: str | None = Query(None, description="Path to model repository"),
) -> ApiCapabilities:
    """Discover API version, workspace health, and supported operations."""
    repo_root = _resolve_repo(repo)
    health = _workspace_health(repo_root)
    recovery = []
    if not health["indexed"]:
        recovery.append(BUILD_INDEX)
    if not mutation_enabled():
        recovery.append(INSPECT_READ_ONLY)
    config = load_repo_config(repo_root)
    if config is None or config.ai is None:
        recovery.append(AI_UNAVAILABLE_ACTION)

    read = [
        CapabilityEntry(
            name="capabilities",
            method="GET",
            href="/api/v1/capabilities",
            description="Discover API version and supported operations.",
        ),
        CapabilityEntry(
            name="search",
            method="GET",
            href="/api/v1/search",
            description="Keyword search across indexed canonical objects.",
        ),
        CapabilityEntry(
            name="object_detail",
            method="GET",
            href="/api/v1/objects/{id}",
            description="Fetch a single canonical object and its relationships.",
        ),
        CapabilityEntry(
            name="health",
            method="GET",
            href="/health",
            description="Workspace health summary.",
        ),
        CapabilityEntry(
            name="activity",
            method="GET",
            href="/api/v1/activity",
            description=(
                "Read append-only local repository activity without treating generated events "
                "as canonical changes."
            ),
        ),
        CapabilityEntry(
            name="list_assessment_manifests",
            method="GET",
            href="/api/v1/assessment-manifests",
            description="List typed generated assessment packages for safe local comparison.",
        ),
        CapabilityEntry(
            name="assessment_comparison",
            method="GET",
            href="/api/v1/assessment-comparisons?base_manifest={path}&head_manifest={path}",
            description=(
                "Compare two typed assessment manifests inside the local workspace without "
                "inferring finding resolution."
            ),
        ),
        CapabilityEntry(
            name="list_reports",
            method="GET",
            href="/api/v1/reports",
            description="List disposable generated artifacts without exposing local paths.",
        ),
        CapabilityEntry(
            name="list_findings",
            method="GET",
            href="/api/v1/findings?assessment={generated-relative-path}",
            description="Read typed assessment findings and separate human review state.",
        ),
        CapabilityEntry(
            name="list_objects",
            method="GET",
            href="/objects",
            description="List canonical objects with optional type filter.",
        ),
        CapabilityEntry(
            name="list_change_requests",
            method="GET",
            href="/change-requests",
            description="List ChangeRequests in the repository.",
        ),
        CapabilityEntry(
            name="get_object",
            method="GET",
            href="/objects/{id}",
            description="Get a single canonical object by ID.",
        ),
        CapabilityEntry(
            name="validate",
            method="GET",
            href="/validate",
            description="Run deterministic validation on the repository.",
        ),
        CapabilityEntry(
            name="trace",
            method="GET",
            href="/trace/{id}",
            description="Trace upstream and downstream relationships.",
        ),
        CapabilityEntry(
            name="impact",
            method="GET",
            href="/impact/{id}",
            description="Generate an impact report for an object.",
        ),
        CapabilityEntry(
            name="list_proposals",
            method="GET",
            href="/proposals",
            description="List PatchProposals in the repository.",
        ),
        CapabilityEntry(
            name="get_proposal",
            method="GET",
            href="/proposals/{id}",
            description="Get a PatchProposal by ID.",
        ),
    ]

    mutations = [
        CapabilityEntry(
            name="export",
            method="POST",
            href="/export",
            description="Export the canonical model to CSV or XLSX.",
        ),
        CapabilityEntry(
            name="gaps",
            method="POST",
            href="/gaps",
            description="Detect dataset-to-model gaps for a local file.",
        ),
        CapabilityEntry(
            name="dataset_readiness",
            method="POST",
            href="/dataset-readiness",
            description="Run the full dataset-readiness workflow.",
        ),
        CapabilityEntry(
            name="validate_proposal",
            method="POST",
            href="/proposals/{id}/validate",
            description="Validate a PatchProposal without applying it.",
        ),
        CapabilityEntry(
            name="dry_run_proposal",
            method="POST",
            href="/proposals/{id}/dry-run",
            description="Preview the result of applying a PatchProposal.",
        ),
        CapabilityEntry(
            name="apply_proposal",
            method="POST",
            href="/proposals/{id}/apply",
            description="Apply an accepted PatchProposal.",
        ),
        CapabilityEntry(
            name="review_proposal",
            method="POST",
            href="/proposals/{id}/review",
            description="Review a PatchProposal and transition its status.",
        ),
        CapabilityEntry(
            name="create_change_request",
            method="POST",
            href="/change-requests",
            description="Create a new ChangeRequest.",
        ),
        CapabilityEntry(
            name="approve_change_request",
            method="POST",
            href="/change-requests/{id}/approve",
            description="Approve a ChangeRequest.",
        ),
        CapabilityEntry(
            name="reject_change_request",
            method="POST",
            href="/change-requests/{id}/reject",
            description="Reject a ChangeRequest.",
        ),
        CapabilityEntry(
            name="review_finding",
            method="POST",
            href="/api/v1/findings/review",
            description="Record a human disposition for an assessment finding.",
        ),
        CapabilityEntry(
            name="import_profile",
            method="POST",
            href="/api/v1/imports/profile",
            description="Profile an uploaded CSV or XLSX dataset.",
        ),
        CapabilityEntry(
            name="import_preview",
            method="POST",
            href="/api/v1/imports/preview",
            description="Preview an uploaded XLSX workbook as a PatchProposal.",
        ),
        CapabilityEntry(
            name="import_validate",
            method="POST",
            href="/api/v1/imports/validate",
            description="Validate a returned review workbook before it is turned into a proposal.",
        ),
        CapabilityEntry(
            name="import_propose",
            method="POST",
            href="/api/v1/imports/propose",
            description="Turn a validated review workbook into a reviewable PatchProposal.",
        ),
        CapabilityEntry(
            name="get_workspace",
            method="GET",
            href="/api/v1/workspace",
            description="Read the currently active local workspace summary.",
        ),
        CapabilityEntry(
            name="validate_workspace",
            method="POST",
            href="/api/v1/workspace/validate",
            description="Validate a candidate local repository path without switching.",
        ),
        CapabilityEntry(
            name="export_model",
            method="POST",
            href="/api/v1/exports",
            description="Export the canonical model to CSV or XLSX.",
        ),
        CapabilityEntry(
            name="open_workspace",
            method="POST",
            href="/api/v1/workspace/open",
            description="Switch the API process to a different local workspace.",
        ),
        CapabilityEntry(
            name="create_workspace",
            method="POST",
            href="/api/v1/workspace/create",
            description="Create a new repository from a template and open it.",
        ),
    ]

    return ApiCapabilities(
        version=__version__,
        api_version="v1",
        repository=health["repository"],
        indexed=health["indexed"],
        canonical_files=health["canonical_files"],
        read_only=not mutation_enabled(),
        read=read,
        mutations=mutations,
        recovery=[action.as_dict() for action in recovery],
    )


@router.get("/recovery", response_model=RecoveryResponse)
def recovery_states(
    repo: str | None = Query(None, description="Path to model repository"),
) -> RecoveryResponse:
    """Return all active degraded-mode states and safe recovery actions."""
    repo_root = _resolve_repo(repo)
    health = _workspace_health(repo_root)
    config = load_repo_config(repo_root)
    ai_configured = config is not None and config.ai is not None
    states = workspace_recovery_states(
        repo_root,
        indexed=health["indexed"],
        read_only=not mutation_enabled(),
        ai_configured=ai_configured,
    )
    return RecoveryResponse(
        states=[
            RecoveryStateEntry(
                code=state.code,
                severity=state.severity,
                label=state.label,
                message=state.message,
                actions=[RecoveryActionEntry(**action.as_dict()) for action in state.actions],
                more_info=state.more_info,
            )
            for state in states
        ]
    )


@router.get("/activity", response_model=ActivityResponse)
def activity(
    repo: str | None = Query(None, description="Path to model repository"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of recent audit events"),
) -> ActivityResponse:
    """Return recent audit history; generated operations remain explicitly non-canonical."""
    repo_root = _resolve_repo(repo)
    events = AuditEventService(repo_root).read_events()
    events.sort(key=lambda event: event.timestamp, reverse=True)
    items = [
        ActivityEventItem(
            event_id=event.event_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            actor=event.actor or None,
            status=event.status,
            proposal_id=event.proposal_id,
            changed_object_ids=event.changed_object_ids,
            validation_status=event.validation_status,
            source_state="canonical" if event.changed_object_ids else "generated",
            canonical_change=bool(event.changed_object_ids),
        )
        for event in events[:limit]
    ]
    return ActivityResponse(total_count=len(events), events=items)


def _report_safety_classification(path: Path) -> str:
    """Classify artifacts conservatively; generation alone does not make content shareable."""
    if path.name == "sanitization-manifest.json":
        return "sanitization_metadata"
    if (path.parent / "sanitization-manifest.json").is_file():
        return "sanitized_bundle"
    return "local_only"


@router.get("/reports", response_model=ReportArtifactResponse)
def reports(
    repo: str | None = Query(None, description="Path to model repository"),
    limit: int = Query(100, ge=1, le=500, description="Maximum artifacts to return"),
) -> ReportArtifactResponse:
    """List safe metadata for generated reports; canonical source files are never listed."""
    repo_root = _resolve_repo(repo)
    generated_root = resolve_generated_path(repo_root)
    if not generated_root.exists():
        return ReportArtifactResponse(total_count=0, artifacts=[])

    paths = sorted(
        (
            path
            for path in generated_root.rglob("*")
            if path.is_file() and path.suffix.lower() in _REPORT_EXTENSIONS
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    artifacts = [
        ReportArtifactItem(
            artifact_id=path.relative_to(generated_root).as_posix(),
            name=path.name,
            format=path.suffix.removeprefix(".").upper(),
            created_at=datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            size_bytes=path.stat().st_size,
            safety_classification=_report_safety_classification(path),
            source_repository=workspace_label(),
            tool_version=__version__,
        )
        for path in paths[:limit]
    ]
    return ReportArtifactResponse(total_count=len(paths), artifacts=artifacts)


@router.get("/reports/{artifact_id:path}")
def download_report(
    artifact_id: str,
    repo: str | None = Query(None, description="Path to model repository"),
) -> FileResponse:
    """Download one generated artifact after containment and format checks."""
    generated_root = resolve_generated_path(_resolve_repo(repo)).resolve()
    candidate = (generated_root / artifact_id).resolve()
    try:
        candidate.relative_to(generated_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Artifact must remain inside generated/."
        ) from exc
    if candidate.suffix.lower() not in _REPORT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Artifact format is not downloadable through the local API.",
        )
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Generated artifact not found.")
    return FileResponse(candidate, filename=candidate.name)


def _ensure_index(repo_root: Path) -> Path:
    """Build the disposable index if missing; return the SQLite path."""
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not db_path.exists():
        build_index(repo_root)
    return db_path


@router.post(
    "/reports/generate",
    dependencies=[Depends(require_mutation_token)],
    response_model=ReportGenerateResponse,
)
def generate_report(
    request: ReportGenerateRequest,
    repo: str | None = Query(None, description="Path to model repository"),
) -> ReportGenerateResponse:
    """Generate a disposable report using existing Martenweave report services."""
    repo_root = _resolve_repo(repo)
    generated_root = resolve_generated_path(repo_root)
    reports_dir = generated_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    created_at = datetime.now(UTC).isoformat()

    artifact_path: Path
    artifact_format: str

    if request.report_type == "gap_report":
        db_path = _ensure_index(repo_root)
        report = generate_gap_summary_report(db_path, repo_root)
        artifact_path = reports_dir / f"gap-report-{timestamp}.json"
        artifact_path.write_text(
            json.dumps(
                {
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
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        artifact_format = "json"

    elif request.report_type == "risk_report":
        content = generate_risk_report(repo_root)
        artifact_path = reports_dir / f"risk-report-{timestamp}.md"
        artifact_path.write_text(content, encoding="utf-8")
        artifact_format = "md"

    elif request.report_type == "readiness":
        db_path = _ensure_index(repo_root)
        scorecard = generate_scorecard(db_path, repo_root)
        artifact_path = reports_dir / f"readiness-report-{timestamp}.json"
        artifact_path.write_text(
            json.dumps(
                {
                    "repo_name": scorecard.repo_name,
                    "generated_at": scorecard.generated_at,
                    "readiness_level": scorecard.readiness_level,
                    "object_count": scorecard.object_count,
                    "metrics": [m.__dict__ for m in scorecard.metrics],
                    "gaps": [g.__dict__ for g in scorecard.gaps],
                    "summary": scorecard.summary,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        artifact_format = "json"

    elif request.report_type == "model_summary":
        db_path = _ensure_index(repo_root)
        report = generate_model_summary(repo_root, db_path=db_path)
        artifact_path = reports_dir / f"model-summary-{timestamp}.md"
        artifact_path.write_text(model_summary_to_markdown(report), encoding="utf-8")
        artifact_format = "md"

    elif request.report_type == "pilot_outcome":
        manifests = list(generated_root.rglob("manifest.json"))
        if not manifests:
            raise HTTPException(
                status_code=400,
                detail="No assessment manifest found. Run an assessment first.",
            )
        manifest_path = max(manifests, key=lambda p: p.stat().st_mtime)
        outcome = generate_pilot_outcome(manifest_path)
        artifact_path = reports_dir / f"pilot-outcome-{timestamp}.md"
        write_pilot_outcome(outcome, artifact_path)
        artifact_format = "md"

    elif request.report_type == "business_review_pack":
        artifact_path = reports_dir / f"business-review-pack-{timestamp}"
        generate_review_pack(repo_root, artifact_path)
        # The summary.md acts as the pack manifest for download.
        artifact_path = artifact_path / "summary.md"
        artifact_format = "md"

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported report_type: {request.report_type}",
        )

    return ReportGenerateResponse(
        artifact_id=artifact_path.relative_to(generated_root).as_posix(),
        name=artifact_path.name,
        format=artifact_format,
        created_at=created_at,
    )


def _finding_package(generated_root: Path, assessment: str | None) -> Path | None:
    """Choose a contained assessment package without exposing arbitrary local files."""
    if assessment:
        candidate = (generated_root / assessment).resolve()
        try:
            candidate.relative_to(generated_root.resolve())
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Assessment must remain inside generated/."
            ) from exc
        if not (candidate / "findings.json").is_file():
            raise HTTPException(status_code=404, detail="Assessment findings were not found.")
        return candidate
    candidates = list(generated_root.rglob("findings.json"))
    return max(candidates, key=lambda path: path.stat().st_mtime).parent if candidates else None


@router.get("/assessment-manifests", response_model=AssessmentManifestResponse)
def assessment_manifests(
    repo: str | None = Query(None, description="Path to model repository"),
) -> AssessmentManifestResponse:
    """List valid typed assessment packages without exposing absolute workspace paths."""
    generated_root = resolve_generated_path(_resolve_repo(repo)).resolve()
    items = []
    for manifest_path in generated_root.rglob("manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            findings = json.loads(
                (manifest_path.parent / "findings.json").read_text(encoding="utf-8")
            )
            if not manifest.get("run_id") or not isinstance(findings.get("findings"), list):
                continue
        except (OSError, json.JSONDecodeError):
            continue
        items.append(
            AssessmentManifestItem(
                manifest_id=str(manifest_path.relative_to(generated_root)),
                run_id=str(manifest["run_id"]),
                created_at=manifest.get("created_at"),
                finding_count=len(findings["findings"]),
            )
        )
    items.sort(key=lambda item: item.manifest_id, reverse=True)
    return AssessmentManifestResponse(total_count=len(items), manifests=items)


@router.get("/findings", response_model=FindingResponse)
def findings(
    repo: str | None = Query(None, description="Path to model repository"),
    assessment: str | None = Query(None, description="Generated-relative assessment directory"),
) -> FindingResponse:
    """Return latest typed findings with review state, never merging reviews into provenance."""
    generated_root = resolve_generated_path(_resolve_repo(repo)).resolve()
    package = _finding_package(generated_root, assessment)
    if package is None:
        return FindingResponse(total_count=0, findings=[])
    try:
        payload = json.loads((package / "findings.json").read_text(encoding="utf-8"))
        reviews_path = package / "finding-reviews.json"
        reviews = (
            json.loads(reviews_path.read_text(encoding="utf-8")) if reviews_path.is_file() else {}
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=400, detail="Assessment finding artifacts are unreadable."
        ) from exc
    assessment_id = package.relative_to(generated_root).as_posix()
    items: list[FindingItem] = []
    for raw in payload.get("findings", []):
        try:
            finding = AssessmentFinding.model_validate(raw)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Assessment findings violate the typed contract."
            ) from exc
        items.append(
            FindingItem(
                finding=finding.model_dump(mode="json"),
                review=(reviews.get("reviews", {}) or {}).get(finding.id),
                assessment_id=assessment_id,
            )
        )
    return FindingResponse(assessment_id=assessment_id, total_count=len(items), findings=items)


@router.get("/assessment-comparisons")
def assessment_comparison(
    base_manifest: str = Query(..., description="Path to the earlier assessment manifest"),
    head_manifest: str = Query(..., description="Path to the later assessment manifest"),
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Compare local typed assessment packages while preserving stable finding provenance."""
    repo_root = _resolve_repo(repo)
    base_path = resolve_workspace_input(base_manifest, repo_root)
    head_path = resolve_workspace_input(head_manifest, repo_root)
    if base_path.suffix.lower() != ".json" or head_path.suffix.lower() != ".json":
        raise HTTPException(status_code=400, detail="Assessment manifests must be JSON files.")
    try:
        return compare_assessments(base_path, head_path).to_dict()
    except AssessmentComparisonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/diff", response_model=DiffResultResponse)
def diff_repositories_endpoint(
    base_path: str = Query(..., description="Path to the base repository model directory"),
    head_path: str | None = Query(
        None, description="Head repository model directory; defaults to current workspace model/."
    ),
    repo: str | None = Query(None, description="Path to model repository"),
) -> DiffResultResponse:
    """Compare two repository model directories and return added, removed, and changed objects."""
    repo_root = _resolve_repo(repo)
    base = resolve_workspace_input(base_path, repo_root)
    head = (
        resolve_workspace_input(head_path, repo_root)
        if head_path
        else resolve_model_path(repo_root)
    )

    if not base.is_dir():
        raise HTTPException(status_code=400, detail=f"Base model directory not found: {base}")
    if not head.is_dir():
        raise HTTPException(status_code=400, detail=f"Head model directory not found: {head}")

    try:
        result = diff_repositories(base, head)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Diff failed: {exc}") from exc

    return DiffResultResponse(
        base_count=result.base_count,
        head_count=result.head_count,
        added=result.added,
        removed=result.removed,
        changed=[
            ChangedObjectItem(
                object_id=obj.object_id,
                object_type=obj.object_type,
                object_name=obj.object_name,
                field_changes=[
                    FieldChangeItem(
                        field=change.field,
                        old_value=change.old_value,
                        new_value=change.new_value,
                    )
                    for change in obj.field_changes
                ],
            )
            for obj in result.changed
        ],
        has_changes=result.has_changes,
    )


@router.get("/search", response_model=PaginatedSearchResponse)
def search(
    repo: str | None = Query(None, description="Path to model repository"),
    q: str | None = Query(None, description="Search query"),
    type: str | None = Query(None, description="Filter by object type"),
    status: str | None = Query(None, description="Filter by object status"),
    domain: str | None = Query(None, description="Filter by domain"),
    tags: list[str] | None = None,
    limit: int = Query(50, ge=1, le=200, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Result offset for pagination"),
) -> PaginatedSearchResponse:
    """Search indexed canonical objects by keyword."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not db_path.exists():
        raise HTTPException(status_code=400, detail="Index not found. Run build-index first.")

    result = search_objects(
        db_path,
        query=q or "",
        object_type=type,
        status=status,
        domain=domain,
        tags=tags,
        limit=limit,
        offset=offset,
    )

    items = [
        SearchResultItem(
            object_id=r.object_id,
            object_type=r.object_type,
            status=r.status,
            name=r.name,
            title=r.title,
            domain=r.domain,
            description=r.description,
            source_file=r.source_file,
            score=r.score,
            matched_fields=r.matched_fields,
        )
        for r in result.results
    ]
    return PaginatedSearchResponse(total_count=result.total_count, results=items)


@router.get("/objects/{obj_id}", response_model=ObjectDetailResponse)
def object_detail(
    obj_id: str,
    repo: str | None = Query(None, description="Path to model repository"),
) -> ObjectDetailResponse:
    """Fetch a canonical object by ID, including its relationships."""
    repo_root = _resolve_repo(repo)
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not db_path.exists():
        raise HTTPException(status_code=400, detail="Index not found. Run build-index first.")

    obj = get_object_by_id(db_path, obj_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"Object {obj_id} not found")

    related = list_related_objects(db_path, obj_id)
    related_items = [
        RelatedObjectItem(
            to_object_id=r["to_object_id"],
            relationship_type=r["relationship_type"],
            relationship_class=r["relationship_class"],
        )
        for r in related
    ]
    return ObjectDetailResponse(object=obj, relationships=related_items)


# ---------------------------------------------------------------------------
# Finding review
# ---------------------------------------------------------------------------


@router.post(
    "/findings/review",
    dependencies=[Depends(require_mutation_token)],
    response_model=FindingReviewResponse,
)
def review_finding(
    request: FindingReviewRequest,
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Record a human disposition for an assessment finding."""
    repo_root = _resolve_repo(repo)
    generated_root = resolve_generated_path(repo_root).resolve()
    assessment_dir = (generated_root / request.assessment).resolve()
    try:
        assessment_dir.relative_to(generated_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Assessment must remain inside generated/."
        ) from exc

    if not (assessment_dir / "findings.json").is_file():
        raise HTTPException(status_code=404, detail="Assessment findings were not found.")

    try:
        record = set_review(
            assessment_dir,
            request.finding_id,
            request.disposition,
            request.reviewer,
            request.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return record


@router.post(
    "/findings/promote",
    dependencies=[Depends(require_mutation_token)],
    response_model=FindingPromoteResponse,
)
def promote_finding_endpoint(
    request: FindingPromoteRequest,
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Promote a confirmed assessment finding to a reviewable PatchProposal."""
    repo_root = _resolve_repo(repo)
    generated_root = resolve_generated_path(repo_root).resolve()
    assessment_dir = (generated_root / request.assessment).resolve()
    try:
        assessment_dir.relative_to(generated_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Assessment must remain inside generated/."
        ) from exc

    if not (assessment_dir / "findings.json").is_file():
        raise HTTPException(status_code=404, detail="Assessment findings were not found.")

    try:
        proposal_path = promote_finding(
            assessment_dir,
            repo_root,
            request.finding_id,
            created_by=request.created_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    proposal_id = proposal_path.stem
    return {
        "finding_id": request.finding_id,
        "proposal_id": proposal_id,
        "proposal_path": proposal_path.relative_to(repo_root).as_posix(),
    }


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


def _safe_upload_filename(filename: str | None) -> str:
    """Return a safe basename with no path traversal and no dangerous characters."""
    if not filename:
        return "upload"
    from pathlib import Path as _Path

    name = _Path(filename).name
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    if not safe or safe.startswith("."):
        safe = "upload" + safe
    return safe


@router.post(
    "/imports/profile",
    dependencies=[Depends(require_mutation_token)],
    response_model=ImportProfileResponse,
)
def import_profile(
    file: Annotated[UploadFile, File(..., description="CSV or XLSX dataset file")],
    dataset_id: str | None = Query(None, description="Optional stable dataset identifier"),
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Profile an uploaded CSV or XLSX dataset."""
    repo_root = _resolve_repo(repo)
    generated_root = resolve_generated_path(repo_root)
    uploads_dir = generated_root / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_upload_filename(file.filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix}'. Expected .csv, .xlsx, or .xls.",
        )

    if dataset_id is None:
        dataset_id = Path(safe_name).stem
    dataset_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in dataset_id)

    upload_path = uploads_dir / safe_name
    upload_path.write_bytes(file.file.read())

    if suffix == ".csv":
        profile = profile_csv(upload_path, dataset_id)
        format_name = "csv"
    else:
        profile = profile_xlsx(upload_path, dataset_id)
        format_name = "xlsx"

    return {
        "dataset_id": dataset_id,
        "format": format_name,
        "profile": dataset_profile_to_dict(profile),
    }


@router.post(
    "/imports/preview",
    dependencies=[Depends(require_mutation_token)],
    response_model=ImportPreviewResponse,
)
def import_preview(
    file: Annotated[
        UploadFile, File(..., description="XLSX workbook to preview as a PatchProposal")
    ],
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Preview an uploaded XLSX workbook as a PatchProposal without applying it."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    generated_root = resolve_generated_path(repo_root)
    uploads_dir = generated_root / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_upload_filename(file.filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix != ".xlsx":
        raise HTTPException(
            status_code=400,
            detail=f"Import preview requires an XLSX workbook, got '{suffix}'.",
        )

    upload_path = uploads_dir / safe_name
    upload_path.write_bytes(file.file.read())

    try:
        proposal = import_model_sheet_xlsx(upload_path, model_path, require_stable_ids=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"proposal": proposal}


def _validate_review_workbook(upload_path: Path, model_path: Path) -> dict[str, Any]:
    """Validate a returned XLSX workbook for identity, stable IDs, and references."""
    errors: list[str] = []
    warnings: list[str] = []

    suffix = upload_path.suffix.lower()
    if suffix != ".xlsx":
        errors.append(f"Review workbook must be an XLSX file, got '{suffix}'.")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "workbook_object_count": 0,
            "existing_object_count": 0,
            "overlap_count": 0,
        }

    try:
        rows_by_type = _read_xlsx(upload_path)
    except Exception as exc:
        errors.append(f"Could not read workbook: {exc}")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "workbook_object_count": 0,
            "existing_object_count": 0,
            "overlap_count": 0,
        }

    existing = _load_existing_objects(model_path)
    workbook_ids = {
        row_id
        for rows in rows_by_type.values()
        for row in rows
        if (row_id := row.get("id", "").strip())
    }
    if not workbook_ids and not any(rows_by_type.values()):
        errors.append("Workbook contains no sheets with model rows.")
    elif not workbook_ids:
        errors.append("Workbook rows are missing stable 'id' values.")

    overlap = workbook_ids & set(existing.keys())
    if workbook_ids and not overlap:
        errors.append(
            "Workbook does not match this repository. No object IDs overlap with the current model."
        )

    warnings.extend(_validate_import(rows_by_type, existing))
    warnings.extend(_detect_formulas(upload_path))

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "workbook_object_count": len(workbook_ids),
        "existing_object_count": len(existing),
        "overlap_count": len(overlap),
    }


@router.post(
    "/imports/validate",
    dependencies=[Depends(require_mutation_token)],
    response_model=ImportValidateResponse,
)
def import_validate(
    file: Annotated[
        UploadFile, File(..., description="XLSX workbook to validate as a returned review artifact")
    ],
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Validate a returned review workbook without creating a PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    generated_root = resolve_generated_path(repo_root)
    uploads_dir = generated_root / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_upload_filename(file.filename)
    upload_path = uploads_dir / safe_name
    upload_path.write_bytes(file.file.read())

    return _validate_review_workbook(upload_path, model_path)


@router.post(
    "/imports/propose",
    dependencies=[Depends(require_mutation_token)],
    response_model=ImportProposeResponse,
)
def import_propose(
    file: Annotated[
        UploadFile, File(..., description="XLSX workbook to turn into a PatchProposal")
    ],
    repo: str | None = Query(None, description="Path to model repository"),
) -> dict[str, Any]:
    """Turn a validated review workbook into a reviewable PatchProposal."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    generated_root = resolve_generated_path(repo_root)
    uploads_dir = generated_root / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_upload_filename(file.filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix != ".xlsx":
        raise HTTPException(
            status_code=400,
            detail=f"Review workbook proposal requires an XLSX workbook, got '{suffix}'.",
        )

    upload_path = uploads_dir / safe_name
    upload_path.write_bytes(file.file.read())

    validation = _validate_review_workbook(upload_path, model_path)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail="; ".join(validation["errors"]))

    try:
        proposal = import_model_sheet_xlsx(upload_path, model_path, require_stable_ids=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    proposal_id = f"PP-IMPORT-{timestamp}"
    proposal["id"] = proposal_id
    proposal["name"] = proposal_id
    proposal["title"] = f"Spreadsheet review: {safe_name}"

    proposal_path = write_patch_proposal(proposal, model_path)

    return {
        "proposal_id": proposal_id,
        "proposal_path": str(proposal_path),
        "operations_count": len(proposal.get("operations", [])),
        "warnings": proposal.get("warnings", []),
    }


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


@router.post(
    "/exports",
    dependencies=[Depends(require_mutation_token)],
    response_model=ExportResponse,
)
def export_model(
    repo: str | None = Query(None, description="Path to model repository"),
    format: str = Query("xlsx", description="Export format: csv or xlsx"),
    business_review: bool = Query(False, description="Produce a styled business-review workbook"),
) -> dict[str, Any]:
    """Export the canonical model to CSV or XLSX."""
    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    generated_root = resolve_generated_path(repo_root)

    if format.lower() == "csv":
        output_dir = generated_root / "exports" / "csv"
        export_model_csv(model_path, output_dir=output_dir)
        return {"format": "csv", "artifact_id": "exports/csv"}
    elif format.lower() == "xlsx":
        output_path = generated_root / "exports" / "model.xlsx"
        export_model_xlsx(model_path, output_path=output_path, business_review=business_review)
        return {"format": "xlsx", "artifact_id": "exports/model.xlsx"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {format}")


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------


@router.get("/workspace", response_model=WorkspaceSummary)
def get_workspace() -> dict[str, Any]:
    """Return a safe summary of the currently active workspace."""
    repo_root = _resolve_repo(None)
    return _workspace_summary(repo_root)


@router.post("/workspace/validate", response_model=WorkspaceValidateResponse)
def validate_workspace(
    request: WorkspaceValidateRequest,
) -> dict[str, Any]:
    """Validate a candidate repository path without switching workspaces."""
    repo_root = Path(request.path)
    return _validate_repository_path(repo_root)


@router.post(
    "/workspace/open",
    dependencies=[Depends(require_mutation_token)],
    response_model=WorkspaceValidateResponse,
)
def open_workspace(
    request: WorkspaceValidateRequest,
) -> dict[str, Any]:
    """Validate and switch the API process to a different local workspace."""
    repo_root = Path(request.path)
    validation = _validate_repository_path(repo_root)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail="; ".join(validation["errors"]))

    configure_workspace(repo_root, mutation_token=current_mutation_token())
    return {**_validate_repository_path(repo_root), "valid": True, "errors": []}


@router.post(
    "/workspace/create",
    dependencies=[Depends(require_mutation_token)],
    response_model=WorkspaceValidateResponse,
)
def create_workspace(
    request: WorkspaceCreateRequest,
) -> dict[str, Any]:
    """Create a new repository from a template and open it."""
    repo_root = Path(request.path)
    if repo_root.exists() and any(repo_root.iterdir()):
        raise HTTPException(
            status_code=400,
            detail=f"Target directory is not empty: {repo_root}",
        )

    if request.template and request.template not in available_templates():
        raise HTTPException(
            status_code=400,
            detail=f"Template '{request.template}' not found.",
        )

    try:
        init_repository(repo_root, name=request.name, template=request.template)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    configure_workspace(repo_root, mutation_token=current_mutation_token())
    return {**_validate_repository_path(repo_root), "valid": True, "errors": []}

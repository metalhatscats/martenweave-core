"""Versioned v1 API router for the Martenweave local API."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from modelops_core import __version__
from modelops_core.api.models import (
    ActivityEventItem,
    ActivityResponse,
    ApiCapabilities,
    AssessmentManifestItem,
    AssessmentManifestResponse,
    CapabilityEntry,
    FindingItem,
    FindingResponse,
    ObjectDetailResponse,
    PaginatedSearchResponse,
    RelatedObjectItem,
    ReportArtifactItem,
    ReportArtifactResponse,
    SearchResultItem,
)
from modelops_core.api.recovery import BUILD_INDEX, INSPECT_READ_ONLY
from modelops_core.api.workspace import (
    mutation_enabled,
    resolve_workspace,
    resolve_workspace_input,
    workspace_is_bound,
    workspace_label,
)
from modelops_core.assessment.comparison import AssessmentComparisonError, compare_assessments
from modelops_core.assessment.finding_contract import AssessmentFinding
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.index.query_service import (
    get_object_by_id,
    list_related_objects,
    search_objects,
)
from modelops_core.reports.audit_service import AuditEventService
from modelops_core.repository import scan_repository

router = APIRouter(prefix="/api/v1")

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
    generated_root = resolve_generated_path(_resolve_repo(repo))
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

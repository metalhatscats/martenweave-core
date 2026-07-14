"""Versioned v1 API router for the Martenweave local API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from modelops_core import __version__
from modelops_core.api.models import (
    ApiCapabilities,
    CapabilityEntry,
    ObjectDetailResponse,
    PaginatedSearchResponse,
    RelatedObjectItem,
    SearchResultItem,
)
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.index.query_service import (
    get_object_by_id,
    list_related_objects,
    search_objects,
)
from modelops_core.repository import scan_repository

router = APIRouter(prefix="/api/v1")


def _resolve_repo(repo: str | None) -> Path:
    return Path(repo).resolve() if repo else Path.cwd().resolve()


def _workspace_health(repo_root: Path) -> dict[str, Any]:
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)
    return {
        "indexed": db_path.exists(),
        "canonical_files": len(files),
        "repository": str(repo_root),
    }


@router.get("/capabilities", response_model=ApiCapabilities)
def capabilities(
    repo: str | None = Query(None, description="Path to model repository"),
) -> ApiCapabilities:
    """Discover API version, workspace health, and supported operations."""
    repo_root = _resolve_repo(repo)
    health = _workspace_health(repo_root)

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
        read_only=False,
        read=read,
        mutations=mutations,
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

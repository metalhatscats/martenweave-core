"""Pydantic response models for the versioned Martenweave API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CapabilityEntry(BaseModel):
    """A single supported operation exposed by the API."""

    name: str
    method: str
    href: str
    description: str


class RecoveryActionEntry(BaseModel):
    """A deterministic, non-mutating recovery action advertised by the API."""

    code: str
    label: str
    command: str | None = None
    requires_confirmation: bool = False


class ApiCapabilities(BaseModel):
    """Capability discovery response for the versioned API."""

    version: str = Field(..., description="Martenweave package version.")
    api_version: str = Field(..., description="API contract version.")
    repository: str = Field(..., description="Absolute path to the resolved repository.")
    indexed: bool = Field(..., description="Whether a generated SQLite index is present.")
    canonical_files: int = Field(..., description="Number of canonical files found in model/.")
    read_only: bool = Field(..., description="Whether mutation endpoints are disabled.")
    read: list[CapabilityEntry] = Field(..., description="Available read operations.")
    mutations: list[CapabilityEntry] = Field(..., description="Available mutation operations.")
    recovery: list[RecoveryActionEntry] = Field(
        default_factory=list,
        description="Safe recovery actions for the current workspace state.",
    )


class SearchResultItem(BaseModel):
    """A single search result returned by /api/v1/search."""

    object_id: str
    object_type: str
    status: str
    name: str | None
    title: str | None
    domain: str | None
    description: str | None
    source_file: str
    score: float
    matched_fields: list[str]


class PaginatedSearchResponse(BaseModel):
    """Paginated response wrapper for search results."""

    total_count: int
    results: list[SearchResultItem]


class RelatedObjectItem(BaseModel):
    """A relationship edge from the requested object to another object."""

    object_id: str = Field(..., alias="to_object_id")
    relationship_type: str
    relationship_class: str

    model_config = {"populate_by_name": True}


class ObjectDetailResponse(BaseModel):
    """Detailed object response for /api/v1/objects/{id}."""

    object: dict[str, Any]
    relationships: list[RelatedObjectItem]

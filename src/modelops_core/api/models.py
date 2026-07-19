"""Pydantic response models for the versioned Martenweave API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProposalReviewRequest(BaseModel):
    """Request body for reviewing a PatchProposal."""

    status: str = Field(..., description="Target review status.")
    reviewer: str = Field(default="workbench", description="Identity of the reviewer.")
    reviewer_notes: str | None = Field(default=None, description="Free-form reviewer notes.")
    rejection_reason: str | None = Field(
        default=None, description="Reason for rejection when status is rejected."
    )


class ProposalReviewResponse(BaseModel):
    """Response body after transitioning a PatchProposal's review status."""

    proposal_id: str
    status: str
    reviewer: str
    reviewed_at: str
    warning: str | None = None


class ChangeRequestCreateRequest(BaseModel):
    """Request body for creating a ChangeRequest."""

    id: str
    title: str
    status: str = Field(default="pending")
    requester: str | None = None
    reason: str | None = None
    requested_change: str | None = None
    expected_impact: str | None = None
    affected_objects: list[str] | None = None
    linked_proposals: list[str] | None = None
    related_issues: list[str] | None = None
    related_decisions: list[str] | None = None
    approvers: list[str] | None = None
    priority: str | None = None
    source_evidence: str | None = None


class ChangeRequestResponse(BaseModel):
    """Summary response for a ChangeRequest."""

    id: str
    status: str
    title: str
    requester: str | None = None
    affected_objects: list[str] = Field(default_factory=list)
    source_path: str | None = None


class FindingReviewRequest(BaseModel):
    """Request body for reviewing an assessment finding."""

    assessment: str = Field(..., description="Generated-relative assessment directory.")
    finding_id: str = Field(..., description="Stable finding ID from findings.json.")
    disposition: str = Field(..., description="Human disposition for the finding.")
    reviewer: str = Field(default="workbench", description="Identity of the reviewer.")
    note: str | None = Field(default=None, description="Optional free-form note.")


class FindingReviewResponse(BaseModel):
    """Response body after recording a finding review."""

    finding_id: str
    disposition: str
    reviewer: str
    reviewed_at: str
    note: str


class FindingPromoteRequest(BaseModel):
    """Request body for promoting a confirmed assessment finding."""

    assessment: str = Field(..., description="Generated-relative assessment directory.")
    finding_id: str = Field(..., description="Stable finding ID from findings.json.")
    created_by: str = Field(default="workbench", description="Actor recorded on the proposal.")


class FindingPromoteResponse(BaseModel):
    """Response body after promoting a confirmed finding to a PatchProposal."""

    finding_id: str
    proposal_id: str
    proposal_path: str


class ImportProfileResponse(BaseModel):
    """Response body for a profiled dataset upload."""

    dataset_id: str
    format: str
    profile: dict[str, Any]


class ImportPreviewResponse(BaseModel):
    """Response body for an XLSX import preview."""

    proposal: dict[str, Any]


class ImportValidateResponse(BaseModel):
    """Response body for validating a returned review workbook."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    workbook_object_count: int = 0
    existing_object_count: int = 0
    overlap_count: int = 0


class WorkspaceSummary(BaseModel):
    """Summary of the currently active or candidate workspace."""

    repository_label: str
    version: str
    api_version: str = "v1"
    indexed: bool
    canonical_files: int
    read_only: bool


class WorkspaceValidateResponse(WorkspaceSummary):
    """Validation result for a candidate workspace."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class WorkspaceValidateRequest(BaseModel):
    """Request body for validating a repository path."""

    path: str = Field(..., description="Absolute local repository path.")


class WorkspaceCreateRequest(BaseModel):
    """Request body for creating a new repository."""

    path: str = Field(..., description="Absolute directory path for the new repository.")
    name: str = Field(default="My Model Repository", description="Repository display name.")
    template: str | None = Field(default=None, description="Optional model-spine template name.")


class ImportProposeResponse(BaseModel):
    """Response body after turning a reviewed workbook into a PatchProposal."""

    proposal_id: str
    proposal_path: str
    operations_count: int
    warnings: list[str] = Field(default_factory=list)


class ExportResponse(BaseModel):
    """Response body for a model export request."""

    format: str
    artifact_id: str


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


class RecoveryStateEntry(BaseModel):
    """A degraded workspace state with safe recovery actions."""

    code: str
    severity: str
    label: str
    message: str
    actions: list[RecoveryActionEntry]
    more_info: str | None = None


class RecoveryResponse(BaseModel):
    """All active recovery states for the current workspace."""

    states: list[RecoveryStateEntry]


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


class ActivityEventItem(BaseModel):
    """An append-only local audit event suitable for a Workbench history view."""

    event_id: str
    event_type: str
    timestamp: str
    actor: str | None = None
    status: str
    proposal_id: str | None = None
    changed_object_ids: list[str] = Field(default_factory=list)
    validation_status: str | None = None
    source_state: str
    canonical_change: bool


class ActivityResponse(BaseModel):
    """Recent repository activity sourced exclusively from the local audit log."""

    total_count: int
    events: list[ActivityEventItem]


class ReportArtifactItem(BaseModel):
    """A generated local artifact that is available for inspection or download."""

    artifact_id: str
    name: str
    format: str
    created_at: str
    size_bytes: int
    source_state: str = "generated"
    safety_classification: str
    source_repository: str | None = None
    tool_version: str | None = None


class ReportArtifactResponse(BaseModel):
    """Generated artifact inventory; canonical files are intentionally excluded."""

    total_count: int
    artifacts: list[ReportArtifactItem]


class ReportGenerateRequest(BaseModel):
    """Request body for generating a disposable report."""

    report_type: str = Field(..., description="Type of report to generate.")
    format: str | None = Field(default=None, description="Optional output format hint.")


class ReportGenerateResponse(BaseModel):
    """Response body after generating a report."""

    artifact_id: str
    name: str
    format: str
    created_at: str


class ProposalDiffItem(BaseModel):
    """A single before/after diff entry for a PatchProposal operation."""

    op: str
    object_id: str
    target_path: str | None = None
    before: Any | None = None
    after: Any | None = None
    status: str | None = None
    reason: str | None = None


class ProposalDiffResponse(BaseModel):
    """Before/after diff preview for a PatchProposal."""

    proposal_id: str
    diffs: list[ProposalDiffItem]


class FieldChangeItem(BaseModel):
    """A single field-level change between two object versions."""

    field: str
    old_value: Any | None = None
    new_value: Any | None = None


class ChangedObjectItem(BaseModel):
    """An object that exists in both base and head but has differences."""

    object_id: str
    object_type: str
    object_name: str | None = None
    field_changes: list[FieldChangeItem] = Field(default_factory=list)


class DiffResultResponse(BaseModel):
    """Added, removed, and changed canonical objects between two repository states."""

    base_count: int
    head_count: int
    added: list[dict[str, Any]] = Field(default_factory=list)
    removed: list[dict[str, Any]] = Field(default_factory=list)
    changed: list[ChangedObjectItem] = Field(default_factory=list)
    has_changes: bool


class FindingItem(BaseModel):
    """Typed assessment finding plus separate human review state."""

    finding: dict[str, Any]
    review: dict[str, Any] | None = None
    assessment_id: str


class FindingResponse(BaseModel):
    """Findings from one local assessment package, never canonical model truth."""

    assessment_id: str | None = None
    total_count: int
    findings: list[FindingItem]


class AssessmentManifestItem(BaseModel):
    """A safe generated-relative typed assessment package reference."""

    manifest_id: str
    run_id: str
    created_at: str | None = None
    finding_count: int = 0


class AssessmentManifestResponse(BaseModel):
    total_count: int
    manifests: list[AssessmentManifestItem]


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
    business_owner: str | None = None
    technical_owner: str | None = None
    data_steward: str | None = None
    business_owner_name: str | None = None
    technical_owner_name: str | None = None
    data_steward_name: str | None = None


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

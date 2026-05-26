"""Base schemas and enums shared across all canonical object types."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ObjectType(StrEnum):
    """Canonical object types in the model registry."""

    MASTER_DATA_DOMAIN = "MasterDataDomain"
    MIGRATION_OBJECT = "MigrationObject"
    BUSINESS_ENTITY = "BusinessEntity"
    ENTITY_CONTEXT = "EntityContext"
    ATTRIBUTE = "Attribute"
    ATTRIBUTE_USAGE = "AttributeUsage"
    SYSTEM = "System"
    SYSTEM_ENVIRONMENT = "SystemEnvironment"
    SAP_OBJECT = "SAPObject"
    FIELD_ENDPOINT = "FieldEndpoint"
    INTERFACE = "Interface"
    INTERFACE_ENDPOINT = "InterfaceEndpoint"
    DATASET = "Dataset"
    APPLICATION = "Application"
    INTEGRATION_FLOW = "IntegrationFlow"
    DATA_FLOW_STEP = "DataFlowStep"
    TRANSFORMATION_RULE = "TransformationRule"
    MAPPING_SET = "MappingSet"
    MAPPING = "Mapping"
    VALUE_LIST = "ValueList"
    VALUE_MAPPING = "ValueMapping"
    BUSINESS_RULE = "BusinessRule"
    TRANSFORMATION_LOGIC = "TransformationLogic"
    VALIDATION_RULE = "ValidationRule"
    DATA_QUALITY_CHECK = "DataQualityCheck"
    OWNERSHIP_ROLE = "OwnershipRole"
    PERSON = "Person"
    TEAM = "Team"
    ISSUE = "Issue"
    RISK = "Risk"
    DECISION = "Decision"
    CHANGE_REQUEST = "ChangeRequest"
    PATCH_PROPOSAL = "PatchProposal"
    EVIDENCE = "Evidence"


class GeneralStatus(StrEnum):
    """Generic lifecycle statuses."""

    PROPOSED = "proposed"
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
    BLOCKED = "blocked"
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    ARCHIVED = "archived"


class IssueStatus(StrEnum):
    """Issue-specific statuses."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class PatchProposalStatus(StrEnum):
    """Patch proposal lifecycle."""

    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ChangeRequestStatus(StrEnum):
    """Change request lifecycle."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class BaseObject(BaseModel):
    """Minimal shared fields for all canonical objects."""

    id: str = Field(..., description="Canonical object ID.")
    type: ObjectType = Field(..., description="Canonical object type.")
    status: str = Field(..., description="Lifecycle status.")
    schema_version: str | None = Field(
        default=None, description="Schema version of this object."
    )
    name: str | None = Field(default=None, description="Short name.")
    title: str | None = Field(default=None, description="Human-readable title.")
    domain: str | None = Field(default=None, description="Owning domain ID.")
    description: str | None = Field(default=None, description="Long-form description.")
    target_release: str | None = Field(
        default=None, description="Target release version or milestone."
    )
    roadmap_priority: str | None = Field(
        default=None, description="Roadmap priority (e.g. low, medium, high, critical)."
    )
    created_at: str | None = Field(
        default=None, description="ISO 8601 timestamp when the object was created."
    )
    updated_at: str | None = Field(
        default=None, description="ISO 8601 timestamp when the object was last updated."
    )
    tags: list[str] | None = Field(
        default=None, description="Categorical labels for filtering and search."
    )

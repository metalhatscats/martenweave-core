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
    DATASET = "Dataset"
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

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
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
    name: str | None = Field(default=None, description="Short name.")
    title: str | None = Field(default=None, description="Human-readable title.")
    domain: str | None = Field(default=None, description="Owning domain ID.")
    description: str | None = Field(default=None, description="Long-form description.")

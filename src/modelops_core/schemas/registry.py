"""Canonical object type registry.

Single source of truth for object type metadata:
- type ID and display labels
- reference fields (with expected target types and relationship types)
- search-relevant frontmatter fields
- SAP context rules (for FieldEndpoint validation)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReferenceField:
    """Metadata for a frontmatter field that references another object."""

    name: str
    relationship_type: str
    expected_target_type: str | None = None
    """Expected target object type. None means 'any type'."""
    relationship_class: str = "reference"
    """Traversal class: core_dependency, context, mapping, validation,
    governance, evidence, or reference."""


@dataclass(frozen=True)
class ObjectTypeEntry:
    """Metadata for a single canonical object type."""

    type_id: str
    ui_label_singular: str
    ui_label_plural: str
    reference_fields: tuple[ReferenceField, ...] = field(default_factory=tuple)
    search_fields: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Shared reference field definitions.
# ---------------------------------------------------------------------------
_DOMAIN_REF = ReferenceField("domain", "belongs_to_domain", "MasterDataDomain", "core_dependency")
_MIGRATION_OBJECT_REF = ReferenceField(
    "migration_object", "part_of_migration", "MigrationObject", "core_dependency"
)
_ENTITY_REF = ReferenceField("entity", "belongs_to_entity", "BusinessEntity", "core_dependency")
_ENTITY_CONTEXT_REF = ReferenceField(
    "entity_context", "used_in_context", "EntityContext", "context"
)
_PARENT_ENTITY_REF = ReferenceField(
    "parent_entity", "part_of_entity", "BusinessEntity", "core_dependency"
)
_SYSTEM_REF = ReferenceField("system", "located_in_system", "System", "context")
_APPLICATION_REF = ReferenceField("application", "used_by_application", "Application", "context")
_SOURCE_SYSTEM_REF = ReferenceField("source_system", "flows_from", "System", "context")
_TARGET_SYSTEM_REF = ReferenceField("target_system", "flows_to", "System", "context")
_INTERFACE_REF = ReferenceField("interface", "part_of_interface", "Interface", "core_dependency")
_INTEGRATION_FLOW_REF = ReferenceField(
    "integration_flow", "part_of_flow", "IntegrationFlow", "core_dependency"
)
_SOURCE_STEP_REF = ReferenceField("source_step", "preceded_by", "DataFlowStep", "core_dependency")
_TARGET_STEP_REF = ReferenceField("target_step", "followed_by", "DataFlowStep", "core_dependency")
_TRANSFORMATION_RULE_REF = ReferenceField(
    "transformation_rule", "applies_transformation", "TransformationRule", "mapping"
)
_SOURCE_FIELD_ENDPOINT_REF = ReferenceField(
    "source_field_endpoint", "reads_from", "FieldEndpoint", "mapping"
)
_TARGET_FIELD_ENDPOINT_REF = ReferenceField(
    "target_field_endpoint", "writes_to", "FieldEndpoint", "mapping"
)
_BUSINESS_ATTRIBUTE_REF = ReferenceField(
    "business_attribute", "represents_attribute", "Attribute", "core_dependency"
)
_ATTRIBUTE_REF = ReferenceField("attribute", "has_attribute", "Attribute", "core_dependency")
_FIELD_ENDPOINT_REF = ReferenceField(
    "field_endpoint", "implemented_by_field", "FieldEndpoint", "core_dependency"
)
_SOURCE_ENDPOINT_REF = ReferenceField(
    "source_endpoint", "mapped_from", "FieldEndpoint", "mapping"
)
_TARGET_ENDPOINT_REF = ReferenceField(
    "target_endpoint", "mapped_to", "FieldEndpoint", "mapping"
)
_SOURCE_ENDPOINTS_REF = ReferenceField(
    "source_endpoints", "mapped_from", "FieldEndpoint", "mapping"
)
_TARGET_ENDPOINTS_REF = ReferenceField(
    "target_endpoints", "mapped_to", "FieldEndpoint", "mapping"
)
_RELATED_ISSUE_REF = ReferenceField("related_issue", "affected_by_issue", "Issue", "governance")
_RELATED_ISSUES_REF = ReferenceField(
    "related_issues", "affected_by_issue", "Issue", "governance"
)
_RELATED_DECISIONS_REF = ReferenceField(
    "related_decisions", "explained_by_decision", "Decision", "governance"
)
_VALUE_LIST_REF = ReferenceField(
    "value_list", "has_allowed_values", "ValueList", "validation"
)
_SOURCE_VALUE_LIST_REF = ReferenceField(
    "source_value_list", "maps_from_values", "ValueList", "mapping"
)
_TARGET_VALUE_LIST_REF = ReferenceField(
    "target_value_list", "maps_to_values", "ValueList", "mapping"
)
_VALUE_MAPPING_REF = ReferenceField(
    "value_mapping", "uses_value_mapping", "ValueMapping", "mapping"
)
_PARENT_VALUE_LIST_REF = ReferenceField(
    "parent_value_list", "part_of_value_list", "ValueList", "reference"
)
_MAPPING_REF = ReferenceField("mapping", "uses_mapping", "Mapping", "mapping")
_MAPPING_SET_REF = ReferenceField(
    "mapping_set", "part_of_mapping_set", "MappingSet", "mapping"
)
_VALIDATION_RULES_REF = ReferenceField(
    "validation_rules", "validated_by", "ValidationRule", "validation"
)
_EVIDENCE_REF = ReferenceField("evidence", "supported_by_evidence", "Evidence", "evidence")
_SOURCE_PATCH_PROPOSALS_REF = ReferenceField(
    "source_patch_proposals", "proposed_by", "PatchProposal", "governance"
)
_AFFECTED_OBJECTS_REF = ReferenceField("affected_objects", "affects", None, "governance")
_RELATED_OBJECTS_REF = ReferenceField("related_objects", "related_to", None, "reference")
_BUSINESS_OWNER_REF = ReferenceField("business_owner", "owned_by_business", "Person", "governance")
_TECHNICAL_OWNER_REF = ReferenceField(
    "technical_owner", "owned_by_technical", "Person", "governance"
)
_DATA_STEWARD_REF = ReferenceField("data_steward", "stewarded_by", "Person", "governance")
_APPROVER_REF = ReferenceField("approver", "approved_by", "Person", "governance")
_ACCOUNTABLE_TEAM_REF = ReferenceField(
    "accountable_team", "accountable_to", "Team", "governance"
)

# Common search-relevant frontmatter fields.
_COMMON_SEARCH_FIELDS: tuple[str, ...] = (
    "column_name",
    "field_name",
    "technical_name",
    "issue_type",
    "rule_type",
    "context_category",
    "grain",
)

# ---------------------------------------------------------------------------
# Registry entries for all canonical object types.
# ---------------------------------------------------------------------------
_REGISTRY: dict[str, ObjectTypeEntry] = {
    "MasterDataDomain": ObjectTypeEntry(
        type_id="MasterDataDomain",
        ui_label_singular="Master Data Domain",
        ui_label_plural="Master Data Domains",
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "MigrationObject": ObjectTypeEntry(
        type_id="MigrationObject",
        ui_label_singular="Migration Object",
        ui_label_plural="Migration Objects",
        reference_fields=(_DOMAIN_REF,),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "BusinessEntity": ObjectTypeEntry(
        type_id="BusinessEntity",
        ui_label_singular="Business Entity",
        ui_label_plural="Business Entities",
        reference_fields=(_DOMAIN_REF, _ENTITY_CONTEXT_REF, _PARENT_ENTITY_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "EntityContext": ObjectTypeEntry(
        type_id="EntityContext",
        ui_label_singular="Entity Context",
        ui_label_plural="Entity Contexts",
        reference_fields=(_DOMAIN_REF, _ENTITY_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Attribute": ObjectTypeEntry(
        type_id="Attribute",
        ui_label_singular="Business Attribute",
        ui_label_plural="Business Attributes",
        reference_fields=(
            _DOMAIN_REF,
            _ENTITY_REF,
            _BUSINESS_OWNER_REF,
            _TECHNICAL_OWNER_REF,
            _DATA_STEWARD_REF,
            _ACCOUNTABLE_TEAM_REF,
            _ENTITY_CONTEXT_REF,
            _VALIDATION_RULES_REF,
            _RELATED_ISSUES_REF,
            _RELATED_DECISIONS_REF,
            _MAPPING_REF,
            _VALUE_LIST_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "AttributeUsage": ObjectTypeEntry(
        type_id="AttributeUsage",
        ui_label_singular="Attribute Usage",
        ui_label_plural="Attribute Usages",
        reference_fields=(_ATTRIBUTE_REF, _ENTITY_CONTEXT_REF, _FIELD_ENDPOINT_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "System": ObjectTypeEntry(
        type_id="System",
        ui_label_singular="System",
        ui_label_plural="Systems",
        reference_fields=(_DOMAIN_REF,),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "SystemEnvironment": ObjectTypeEntry(
        type_id="SystemEnvironment",
        ui_label_singular="System Environment",
        ui_label_plural="System Environments",
        reference_fields=(_SYSTEM_REF,),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "SAPObject": ObjectTypeEntry(
        type_id="SAPObject",
        ui_label_singular="SAP Object",
        ui_label_plural="SAP Objects",
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "FieldEndpoint": ObjectTypeEntry(
        type_id="FieldEndpoint",
        ui_label_singular="Field Endpoint",
        ui_label_plural="Field Endpoints",
        reference_fields=(
            _DOMAIN_REF,
            _ENTITY_REF,
            _BUSINESS_OWNER_REF,
            _TECHNICAL_OWNER_REF,
            _DATA_STEWARD_REF,
            _ACCOUNTABLE_TEAM_REF,
            _ENTITY_CONTEXT_REF,
            _SYSTEM_REF,
            _ATTRIBUTE_REF,
            _BUSINESS_ATTRIBUTE_REF,
            _VALUE_LIST_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Interface": ObjectTypeEntry(
        type_id="Interface",
        ui_label_singular="Interface",
        ui_label_plural="Interfaces",
        reference_fields=(_DOMAIN_REF, _SYSTEM_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "InterfaceEndpoint": ObjectTypeEntry(
        type_id="InterfaceEndpoint",
        ui_label_singular="Interface Endpoint",
        ui_label_plural="Interface Endpoints",
        reference_fields=(_DOMAIN_REF, _INTERFACE_REF, _SYSTEM_REF, _APPLICATION_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Application": ObjectTypeEntry(
        type_id="Application",
        ui_label_singular="Application",
        ui_label_plural="Applications",
        reference_fields=(_DOMAIN_REF, _SYSTEM_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "IntegrationFlow": ObjectTypeEntry(
        type_id="IntegrationFlow",
        ui_label_singular="Integration Flow",
        ui_label_plural="Integration Flows",
        reference_fields=(_DOMAIN_REF, _SOURCE_SYSTEM_REF, _TARGET_SYSTEM_REF, _INTERFACE_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "DataFlowStep": ObjectTypeEntry(
        type_id="DataFlowStep",
        ui_label_singular="Data Flow Step",
        ui_label_plural="Data Flow Steps",
        reference_fields=(
            _DOMAIN_REF,
            _INTEGRATION_FLOW_REF,
            _SOURCE_STEP_REF,
            _TARGET_STEP_REF,
            _TRANSFORMATION_RULE_REF,
            _SOURCE_FIELD_ENDPOINT_REF,
            _TARGET_FIELD_ENDPOINT_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "TransformationRule": ObjectTypeEntry(
        type_id="TransformationRule",
        ui_label_singular="Transformation Rule",
        ui_label_plural="Transformation Rules",
        reference_fields=(
            _DOMAIN_REF,
            _SOURCE_FIELD_ENDPOINT_REF,
            _TARGET_FIELD_ENDPOINT_REF,
            _ATTRIBUTE_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Dataset": ObjectTypeEntry(
        type_id="Dataset",
        ui_label_singular="Dataset",
        ui_label_plural="Datasets",
        reference_fields=(
            _DOMAIN_REF,
            _SYSTEM_REF,
            _BUSINESS_OWNER_REF,
            _TECHNICAL_OWNER_REF,
            _DATA_STEWARD_REF,
            _ACCOUNTABLE_TEAM_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "MappingSet": ObjectTypeEntry(
        type_id="MappingSet",
        ui_label_singular="Mapping Set",
        ui_label_plural="Mapping Sets",
        reference_fields=(_DOMAIN_REF,),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Mapping": ObjectTypeEntry(
        type_id="Mapping",
        ui_label_singular="Mapping",
        ui_label_plural="Mappings",
        reference_fields=(
            _DOMAIN_REF,
            _SOURCE_ENDPOINT_REF,
            _TARGET_ENDPOINT_REF,
            _BUSINESS_OWNER_REF,
            _TECHNICAL_OWNER_REF,
            _SOURCE_VALUE_LIST_REF,
            _TARGET_VALUE_LIST_REF,
            _VALUE_MAPPING_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "ValueList": ObjectTypeEntry(
        type_id="ValueList",
        ui_label_singular="Value List",
        ui_label_plural="Value Lists",
        reference_fields=(
            _DOMAIN_REF,
            _PARENT_VALUE_LIST_REF,
            _BUSINESS_OWNER_REF,
            _TECHNICAL_OWNER_REF,
            _DATA_STEWARD_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "ValueMapping": ObjectTypeEntry(
        type_id="ValueMapping",
        ui_label_singular="Value Mapping",
        ui_label_plural="Value Mappings",
        reference_fields=(
            _DOMAIN_REF,
            _VALUE_LIST_REF,
            _SOURCE_VALUE_LIST_REF,
            _TARGET_VALUE_LIST_REF,
            _BUSINESS_OWNER_REF,
            _TECHNICAL_OWNER_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "BusinessRule": ObjectTypeEntry(
        type_id="BusinessRule",
        ui_label_singular="Business Rule",
        ui_label_plural="Business Rules",
        reference_fields=(_DOMAIN_REF, _ATTRIBUTE_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "TransformationLogic": ObjectTypeEntry(
        type_id="TransformationLogic",
        ui_label_singular="Transformation Logic",
        ui_label_plural="Transformation Logics",
        reference_fields=(_DOMAIN_REF, _MAPPING_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "ValidationRule": ObjectTypeEntry(
        type_id="ValidationRule",
        ui_label_singular="Validation Rule",
        ui_label_plural="Validation Rules",
        reference_fields=(
            _DOMAIN_REF,
            _ATTRIBUTE_REF,
            _VALUE_LIST_REF,
            _BUSINESS_OWNER_REF,
            _APPROVER_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "DataQualityCheck": ObjectTypeEntry(
        type_id="DataQualityCheck",
        ui_label_singular="Data Quality Check",
        ui_label_plural="Data Quality Checks",
        reference_fields=(_DOMAIN_REF, _ATTRIBUTE_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "OwnershipRole": ObjectTypeEntry(
        type_id="OwnershipRole",
        ui_label_singular="Ownership Role",
        ui_label_plural="Ownership Roles",
        reference_fields=(_DOMAIN_REF, _ATTRIBUTE_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Person": ObjectTypeEntry(
        type_id="Person",
        ui_label_singular="Person",
        ui_label_plural="People",
        reference_fields=(_DOMAIN_REF,),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Team": ObjectTypeEntry(
        type_id="Team",
        ui_label_singular="Team",
        ui_label_plural="Teams",
        reference_fields=(_DOMAIN_REF,),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Issue": ObjectTypeEntry(
        type_id="Issue",
        ui_label_singular="Issue",
        ui_label_plural="Issues",
        reference_fields=(
            _DOMAIN_REF,
            _ATTRIBUTE_REF,
            _RELATED_OBJECTS_REF,
            _BUSINESS_OWNER_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Risk": ObjectTypeEntry(
        type_id="Risk",
        ui_label_singular="Risk",
        ui_label_plural="Risks",
        reference_fields=(_DOMAIN_REF, _ATTRIBUTE_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Decision": ObjectTypeEntry(
        type_id="Decision",
        ui_label_singular="Decision",
        ui_label_plural="Decisions",
        reference_fields=(
            _DOMAIN_REF,
            _ATTRIBUTE_REF,
            _EVIDENCE_REF,
            _BUSINESS_OWNER_REF,
            _APPROVER_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "ChangeRequest": ObjectTypeEntry(
        type_id="ChangeRequest",
        ui_label_singular="Change Request",
        ui_label_plural="Change Requests",
        reference_fields=(_DOMAIN_REF, _AFFECTED_OBJECTS_REF, _EVIDENCE_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "PatchProposal": ObjectTypeEntry(
        type_id="PatchProposal",
        ui_label_singular="Patch Proposal",
        ui_label_plural="Patch Proposals",
        reference_fields=(_DOMAIN_REF, _AFFECTED_OBJECTS_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Evidence": ObjectTypeEntry(
        type_id="Evidence",
        ui_label_singular="Evidence",
        ui_label_plural="Evidence",
        reference_fields=(_DOMAIN_REF,),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
}

# Global reference field map (backward-compatible union of all per-type fields).
_GLOBAL_REFERENCE_FIELDS: dict[str, ReferenceField] = {}
for _entry in _REGISTRY.values():
    for _ref in _entry.reference_fields:
        _GLOBAL_REFERENCE_FIELDS.setdefault(_ref.name, _ref)
_GLOBAL_REFERENCE_FIELDS.setdefault("source_patch_proposals", _SOURCE_PATCH_PROPOSALS_REF)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_entry(type_id: str) -> ObjectTypeEntry | None:
    """Look up an object type by its canonical type ID."""
    return _REGISTRY.get(type_id)


def get_all_types() -> list[str]:
    """Return all registered canonical object type IDs."""
    return list(_REGISTRY.keys())


def get_ui_label(type_id: str, plural: bool = False) -> str:
    """Return the human-readable UI label for an object type."""
    entry = _REGISTRY.get(type_id)
    if entry is None:
        return type_id
    return entry.ui_label_plural if plural else entry.ui_label_singular


def get_reference_fields(type_id: str | None = None) -> dict[str, ReferenceField]:
    """Return reference fields for a given type, or the global union if no type is given."""
    if type_id is None:
        return dict(_GLOBAL_REFERENCE_FIELDS)
    entry = _REGISTRY.get(type_id)
    if entry is None:
        return {}
    return {ref.name: ref for ref in entry.reference_fields}


def get_relationship_fields(type_id: str | None = None) -> dict[str, str]:
    """Return a mapping from frontmatter field name to relationship type."""
    refs = get_reference_fields(type_id)
    return {name: ref.relationship_type for name, ref in refs.items()}


def get_relationship_classes(type_id: str | None = None) -> dict[str, str]:
    """Return a mapping from frontmatter field name to relationship class."""
    refs = get_reference_fields(type_id)
    return {name: ref.relationship_class for name, ref in refs.items()}


def get_expected_target_types(type_id: str | None = None) -> dict[str, str | None]:
    """Return a mapping from frontmatter field name to expected target object type."""
    refs = get_reference_fields(type_id)
    return {name: ref.expected_target_type for name, ref in refs.items()}


def get_search_fields(type_id: str | None = None) -> tuple[str, ...]:
    """Return search-relevant frontmatter fields for an object type."""
    if type_id is None:
        return _COMMON_SEARCH_FIELDS
    entry = _REGISTRY.get(type_id)
    if entry is None or not entry.search_fields:
        return _COMMON_SEARCH_FIELDS
    return entry.search_fields




def register_type(entry: ObjectTypeEntry) -> None:
    """Register a new object type (for tests or extensions)."""
    if entry.type_id in _REGISTRY:
        raise ValueError(f"Object type '{entry.type_id}' is already registered.")
    _REGISTRY[entry.type_id] = entry
    for ref in entry.reference_fields:
        _GLOBAL_REFERENCE_FIELDS.setdefault(ref.name, ref)

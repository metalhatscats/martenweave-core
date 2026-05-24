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


@dataclass(frozen=True)
class SAPContextRule:
    """SAP table → required EntityContext context_category."""

    sap_table: str
    required_context_category: str
    error_code: str


@dataclass(frozen=True)
class ObjectTypeEntry:
    """Metadata for a single canonical object type."""

    type_id: str
    ui_label_singular: str
    ui_label_plural: str
    reference_fields: tuple[ReferenceField, ...] = field(default_factory=tuple)
    search_fields: tuple[str, ...] = field(default_factory=tuple)
    sap_context_rules: tuple[SAPContextRule, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Shared reference field definitions.
# ---------------------------------------------------------------------------
_DOMAIN_REF = ReferenceField("domain", "domain", "MasterDataDomain")
_MIGRATION_OBJECT_REF = ReferenceField("migration_object", "migration_object", "MigrationObject")
_ENTITY_REF = ReferenceField("entity", "entity", "BusinessEntity")
_ENTITY_CONTEXT_REF = ReferenceField("entity_context", "entity_context", "EntityContext")
_SYSTEM_REF = ReferenceField("system", "system", "System")
_BUSINESS_ATTRIBUTE_REF = ReferenceField("business_attribute", "business_attribute", "Attribute")
_ATTRIBUTE_REF = ReferenceField("attribute", "attribute", "Attribute")
_FIELD_ENDPOINT_REF = ReferenceField("field_endpoint", "field_endpoint", "FieldEndpoint")
_SOURCE_ENDPOINT_REF = ReferenceField("source_endpoint", "source_endpoint", "FieldEndpoint")
_TARGET_ENDPOINT_REF = ReferenceField("target_endpoint", "target_endpoint", "FieldEndpoint")
_SOURCE_ENDPOINTS_REF = ReferenceField("source_endpoints", "source_endpoints", "FieldEndpoint")
_TARGET_ENDPOINTS_REF = ReferenceField("target_endpoints", "target_endpoints", "FieldEndpoint")
_RELATED_ISSUE_REF = ReferenceField("related_issue", "related_issue", "Issue")
_RELATED_ISSUES_REF = ReferenceField("related_issues", "related_issues", "Issue")
_RELATED_DECISIONS_REF = ReferenceField("related_decisions", "related_decisions", "Decision")
_VALUE_LIST_REF = ReferenceField("value_list", "value_list", "ValueList")
_SOURCE_VALUE_LIST_REF = ReferenceField("source_value_list", "source_value_list", "ValueList")
_TARGET_VALUE_LIST_REF = ReferenceField("target_value_list", "target_value_list", "ValueList")
_VALUE_MAPPING_REF = ReferenceField("value_mapping", "value_mapping", "ValueMapping")
_MAPPING_REF = ReferenceField("mapping", "mapping", "Mapping")
_MAPPING_SET_REF = ReferenceField("mapping_set", "mapping_set", "MappingSet")
_VALIDATION_RULES_REF = ReferenceField("validation_rules", "validation_rules", "ValidationRule")
_EVIDENCE_REF = ReferenceField("evidence", "evidence", "Evidence")
_SOURCE_PATCH_PROPOSALS_REF = ReferenceField(
    "source_patch_proposals", "source_patch_proposals", "PatchProposal"
)
_AFFECTED_OBJECTS_REF = ReferenceField("affected_objects", "affected_objects", None)
_RELATED_OBJECTS_REF = ReferenceField("related_objects", "related_objects", None)

# Common search-relevant frontmatter fields.
_COMMON_SEARCH_FIELDS: tuple[str, ...] = (
    "sap_table",
    "sap_field",
    "column_name",
    "field_name",
    "technical_name",
    "issue_type",
    "rule_type",
    "context_category",
    "grain",
)

# SAP table → required EntityContext context_category rules.
_SAP_CONTEXT_RULES: tuple[SAPContextRule, ...] = (
    SAPContextRule("KNVV", "customer_sales_area", "SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA"),
    SAPContextRule("KNB1", "customer_company_code", "SAP_CONTEXT_KNB1_REQUIRES_COMPANY_CODE"),
    SAPContextRule(
        "KNVP", "customer_partner_function", "SAP_CONTEXT_KNVP_REQUIRES_PARTNER_FUNCTION"
    ),
    SAPContextRule("BUT000", "bp_central", "SAP_CONTEXT_BUT000_REQUIRES_BP_CENTRAL"),
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
        reference_fields=(_DOMAIN_REF, _ENTITY_CONTEXT_REF),
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
            _ENTITY_CONTEXT_REF,
            _SYSTEM_REF,
            _ATTRIBUTE_REF,
            _BUSINESS_ATTRIBUTE_REF,
        ),
        search_fields=_COMMON_SEARCH_FIELDS,
        sap_context_rules=_SAP_CONTEXT_RULES,
    ),
    "Interface": ObjectTypeEntry(
        type_id="Interface",
        ui_label_singular="Interface",
        ui_label_plural="Interfaces",
        reference_fields=(_DOMAIN_REF, _SYSTEM_REF),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "Dataset": ObjectTypeEntry(
        type_id="Dataset",
        ui_label_singular="Dataset",
        ui_label_plural="Datasets",
        reference_fields=(_DOMAIN_REF, _SYSTEM_REF),
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
        reference_fields=(_DOMAIN_REF,),
        search_fields=_COMMON_SEARCH_FIELDS,
    ),
    "ValueMapping": ObjectTypeEntry(
        type_id="ValueMapping",
        ui_label_singular="Value Mapping",
        ui_label_plural="Value Mappings",
        reference_fields=(_DOMAIN_REF, _VALUE_LIST_REF),
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
        reference_fields=(_DOMAIN_REF, _ATTRIBUTE_REF),
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
        reference_fields=(_DOMAIN_REF, _ATTRIBUTE_REF, _RELATED_OBJECTS_REF),
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
        reference_fields=(_DOMAIN_REF, _ATTRIBUTE_REF, _EVIDENCE_REF),
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


def get_sap_context_rules(type_id: str) -> tuple[SAPContextRule, ...]:
    """Return SAP context rules for an object type (e.g. FieldEndpoint)."""
    entry = _REGISTRY.get(type_id)
    if entry is None:
        return ()
    return entry.sap_context_rules


def register_type(entry: ObjectTypeEntry) -> None:
    """Register a new object type (for tests or extensions)."""
    if entry.type_id in _REGISTRY:
        raise ValueError(f"Object type '{entry.type_id}' is already registered.")
    _REGISTRY[entry.type_id] = entry
    for ref in entry.reference_fields:
        _GLOBAL_REFERENCE_FIELDS.setdefault(ref.name, ref)

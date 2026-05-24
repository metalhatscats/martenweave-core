"""Canonical schemas for ModelOps MDM Core."""

from modelops_core.schemas.common import BaseObject, GeneralStatus, ObjectType
from modelops_core.schemas.registry import (
    ObjectTypeEntry,
    ReferenceField,
    SAPContextRule,
    get_entry,
    get_expected_target_types,
    get_reference_fields,
    get_relationship_fields,
    get_sap_context_rules,
    get_search_fields,
    get_ui_label,
    register_type,
)

__all__ = [
    "BaseObject",
    "GeneralStatus",
    "ObjectType",
    "ObjectTypeEntry",
    "ReferenceField",
    "SAPContextRule",
    "get_entry",
    "get_expected_target_types",
    "get_reference_fields",
    "get_relationship_fields",
    "get_sap_context_rules",
    "get_search_fields",
    "get_ui_label",
    "register_type",
]

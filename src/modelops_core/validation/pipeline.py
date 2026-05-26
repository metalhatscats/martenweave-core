"""Layer 1–3 deterministic validation pipeline for canonical objects."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from modelops_core.domain_packs import get_domain_packs
from modelops_core.repository import ParsedObject
from modelops_core.schemas import ObjectType, get_expected_target_types
from modelops_core.schemas.versioning import validate_object_schema_version
from modelops_core.validation.result import ValidationResult, ValidationSeverity, ValidationSummary

_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$")


def _fm_value(frontmatter: dict[str, Any] | None, key: str) -> Any:
    if frontmatter is None:
        return None
    return frontmatter.get(key)


def _check_id(frontmatter: dict[str, Any] | None, source_file: str) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    raw_id = _fm_value(frontmatter, "id")
    if raw_id is None:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="ID_MISSING",
                message="Object is missing required 'id' field.",
                source_file=source_file,
                field_path="id",
                suggested_fix="Add a unique stable ID (e.g., ATTR-NAME).",
            )
        )
    elif not isinstance(raw_id, str) or not _ID_PATTERN.match(raw_id):
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="ID_INVALID_FORMAT",
                message=f"Invalid ID format: '{raw_id}'. Must match {_ID_PATTERN.pattern}.",
                object_id=str(raw_id) if raw_id is not None else None,
                source_file=source_file,
                field_path="id",
                suggested_fix="Use uppercase A–Z / 0–9 with hyphens only (e.g., ATTR-NAME).",
            )
        )
    return results


def _check_type(frontmatter: dict[str, Any] | None, source_file: str) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    raw_type = _fm_value(frontmatter, "type")
    if raw_type is None:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="TYPE_MISSING",
                message="Object is missing required 'type' field.",
                source_file=source_file,
                field_path="type",
                suggested_fix="Add a canonical object type (e.g., Attribute).",
            )
        )
        return results
    try:
        ObjectType(raw_type)
    except ValueError:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="TYPE_UNKNOWN",
                message=f"Unknown object type: '{raw_type}'.",
                object_type=str(raw_type),
                source_file=source_file,
                field_path="type",
                suggested_fix="Use a registered canonical object type.",
            )
        )
    return results


def _check_status(frontmatter: dict[str, Any] | None, source_file: str) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    raw_status = _fm_value(frontmatter, "status")
    if raw_status is None or (isinstance(raw_status, str) and not raw_status.strip()):
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="STATUS_MISSING",
                message="Object is missing required 'status' field or it is empty.",
                source_file=source_file,
                field_path="status",
                suggested_fix="Add a non-empty lifecycle status (e.g., draft, active).",
            )
        )
    return results


def _check_display_name(
    frontmatter: dict[str, Any] | None, source_file: str
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    name = _fm_value(frontmatter, "name")
    title = _fm_value(frontmatter, "title")
    if not name and not title:
        obj_id = _fm_value(frontmatter, "id")
        results.append(
            ValidationResult(
                severity=ValidationSeverity.WARNING,
                code="DISPLAY_NAME_MISSING",
                message="Object has neither 'name' nor 'title'; display may be poor.",
                object_id=str(obj_id) if obj_id is not None else None,
                source_file=source_file,
                field_path="name",
                suggested_fix="Add a 'name' or 'title' field for better display.",
            )
        )
    return results


def _check_timestamps(
    frontmatter: dict[str, Any] | None, source_file: str
) -> list[ValidationResult]:
    """Warn if created_at or updated_at are missing."""
    results: list[ValidationResult] = []
    created_at = _fm_value(frontmatter, "created_at")
    if not created_at:
        obj_id = _fm_value(frontmatter, "id")
        results.append(
            ValidationResult(
                severity=ValidationSeverity.WARNING,
                code="TIMESTAMP_MISSING",
                message="Object is missing 'created_at' timestamp.",
                object_id=str(obj_id) if obj_id is not None else None,
                source_file=source_file,
                field_path="created_at",
                suggested_fix=(
                    "Add a 'created_at' ISO 8601 timestamp "
                    "(e.g. 2024-01-15T10:30:00+00:00)."
                ),
            )
        )
    return results


_MAX_TAG_LENGTH = 32
_MAX_TAGS = 10


def _check_tags(
    frontmatter: dict[str, Any] | None, source_file: str
) -> list[ValidationResult]:
    """Validate tag format: lowercase, no spaces, max length, max count."""
    results: list[ValidationResult] = []
    tags = _fm_value(frontmatter, "tags")
    if tags is None:
        return results
    if not isinstance(tags, list):
        obj_id = _fm_value(frontmatter, "id")
        results.append(
            ValidationResult(
                severity=ValidationSeverity.WARNING,
                code="TAGS_INVALID_TYPE",
                message="'tags' must be a list of strings.",
                object_id=str(obj_id) if obj_id is not None else None,
                source_file=source_file,
                field_path="tags",
                suggested_fix="Use a YAML list: tags: [customer, sales]",
            )
        )
        return results
    if len(tags) > _MAX_TAGS:
        obj_id = _fm_value(frontmatter, "id")
        results.append(
            ValidationResult(
                severity=ValidationSeverity.WARNING,
                code="TAGS_TOO_MANY",
                message=f"Object has {len(tags)} tags (max {_MAX_TAGS}).",
                object_id=str(obj_id) if obj_id is not None else None,
                source_file=source_file,
                field_path="tags",
                suggested_fix=f"Reduce to {_MAX_TAGS} or fewer tags.",
            )
        )
    for idx, tag in enumerate(tags):
        if not isinstance(tag, str):
            obj_id = _fm_value(frontmatter, "id")
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="TAG_INVALID_TYPE",
                    message=f"Tag at index {idx} is not a string.",
                    object_id=str(obj_id) if obj_id is not None else None,
                    source_file=source_file,
                    field_path=f"tags[{idx}]",
                    suggested_fix="All tags must be strings.",
                )
            )
            continue
        issues: list[str] = []
        if " " in tag:
            issues.append("contains spaces")
        if tag != tag.lower():
            issues.append("not lowercase")
        if len(tag) > _MAX_TAG_LENGTH:
            issues.append(f"exceeds {_MAX_TAG_LENGTH} chars")
        if issues:
            obj_id = _fm_value(frontmatter, "id")
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="TAG_INVALID_FORMAT",
                    message=f"Tag '{tag}' is invalid: {', '.join(issues)}.",
                    object_id=str(obj_id) if obj_id is not None else None,
                    source_file=source_file,
                    field_path=f"tags[{idx}]",
                    suggested_fix="Use lowercase, no spaces, max 32 chars.",
                )
            )
    return results


def _check_schema_version(
    frontmatter: dict[str, Any] | None, source_file: str
) -> list[ValidationResult]:
    """Check schema_version on a single canonical object."""
    results: list[ValidationResult] = []
    for issue in validate_object_schema_version(frontmatter, source_file):
        results.append(
            ValidationResult(
                severity=ValidationSeverity(issue.severity),
                code=issue.code,
                message=issue.message,
                object_id=issue.object_id,
                source_file=issue.source_file,
                suggested_fix=issue.suggested_fix,
            )
        )
    return results


def _validate_individual(obj: ParsedObject) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    if obj.parser_error is not None:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="PARSER_ERROR",
                message=obj.parser_error,
                source_file=obj.source_path,
                suggested_fix="Fix syntax errors in the source file.",
            )
        )
        return results

    if obj.frontmatter is None:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="FRONTMATTER_MISSING",
                message="File has no YAML frontmatter or YAML root mapping.",
                source_file=obj.source_path,
                suggested_fix=(
                    "Add YAML frontmatter (--- ... ---) for Markdown, "
                    "or ensure the YAML file starts with a mapping."
                ),
            )
        )
        return results

    results.extend(_check_id(obj.frontmatter, obj.source_path))
    results.extend(_check_type(obj.frontmatter, obj.source_path))
    results.extend(_check_status(obj.frontmatter, obj.source_path))
    results.extend(_check_display_name(obj.frontmatter, obj.source_path))
    results.extend(_check_timestamps(obj.frontmatter, obj.source_path))
    results.extend(_check_tags(obj.frontmatter, obj.source_path))
    results.extend(_check_schema_version(obj.frontmatter, obj.source_path))
    return results


def _detect_duplicate_ids(objects: list[ParsedObject]) -> list[ValidationResult]:
    id_to_sources: defaultdict[str, list[str]] = defaultdict(list)
    for obj in objects:
        if obj.parser_error is not None or obj.frontmatter is None:
            continue
        raw_id = obj.frontmatter.get("id")
        if isinstance(raw_id, str) and _ID_PATTERN.match(raw_id):
            id_to_sources[raw_id].append(obj.source_path)

    results: list[ValidationResult] = []
    for obj_id, sources in id_to_sources.items():
        if len(sources) <= 1:
            continue
        for source in sources:
            related = [s for s in sources if s != source]
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    code="ID_DUPLICATE",
                    message=f"Duplicate ID '{obj_id}' found in multiple files.",
                    object_id=obj_id,
                    source_file=source,
                    field_path="id",
                    related_objects=related,
                    suggested_fix="Ensure each object has a globally unique ID.",
                )
            )
    return results


def _build_registry(objects: list[ParsedObject]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for obj in objects:
        if obj.parser_error is not None or obj.frontmatter is None:
            continue
        obj_id = obj.frontmatter.get("id")
        obj_type = obj.frontmatter.get("type")
        if isinstance(obj_id, str) and _ID_PATTERN.match(obj_id):
            registry[obj_id] = {"type": obj_type, "source_path": obj.source_path}
    return registry


def _validate_references(
    objects: list[ParsedObject], registry: dict[str, dict[str, Any]]
) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    for obj in objects:
        if obj.parser_error is not None or obj.frontmatter is None:
            continue
        frontmatter = obj.frontmatter
        source_id = frontmatter.get("id")
        source_id_str = str(source_id) if isinstance(source_id, str) else None

        reference_fields = get_expected_target_types()
        for field, expected_type in reference_fields.items():
            value = frontmatter.get(field)
            if value is None:
                continue

            refs: list[str] = []
            if isinstance(value, str):
                refs = [value]
            elif isinstance(value, list):
                refs = [str(v) for v in value if isinstance(v, str)]
            else:
                continue

            for ref_id in refs:
                if ref_id not in registry:
                    results.append(
                        ValidationResult(
                            severity=ValidationSeverity.ERROR,
                            code="REFERENCE_BROKEN",
                            message=(
                                f"Broken reference: '{field}' points to "
                                f"'{ref_id}' which does not exist."
                            ),
                            object_id=source_id_str,
                            source_file=obj.source_path,
                            field_path=field,
                            suggested_fix=(
                                f"Create an object with id '{ref_id}' or "
                                f"correct the '{field}' value."
                            ),
                        )
                    )
                    continue

                if expected_type is not None:
                    actual_type = registry[ref_id].get("type")
                    if actual_type != expected_type:
                        results.append(
                            ValidationResult(
                                severity=ValidationSeverity.ERROR,
                                code="REFERENCE_TYPE_MISMATCH",
                                message=(
                                    f"Reference type mismatch: '{field}' "
                                    f"expects '{expected_type}' but "
                                    f"'{ref_id}' is '{actual_type}'."
                                ),
                                object_id=source_id_str,
                                source_file=obj.source_path,
                                field_path=field,
                                suggested_fix=(
                                    f"Point '{field}' to an object of type "
                                    f"'{expected_type}'."
                                ),
                            )
                        )

    return results


_OWNERSHIP_TYPES = frozenset(
    {
        "Attribute",
        "FieldEndpoint",
        "Dataset",
        "Mapping",
        "ValidationRule",
        "Issue",
        "Decision",
        "BusinessEntity",
        "ValueList",
        "ValueMapping",
    }
)
_OWNERSHIP_FIELDS = (
    "business_owner",
    "technical_owner",
    "data_steward",
    "accountable_team",
    "approver",
)


def _validate_lov_governance(
    objects: list[ParsedObject], registry: dict[str, dict[str, Any]]
) -> list[ValidationResult]:
    """Validate ValueList and ValueMapping governance rules."""
    results: list[ValidationResult] = []
    value_list_codes: dict[str, set[str]] = {}

    for obj in objects:
        fm = obj.frontmatter or {}
        if fm.get("type") != "ValueList":
            continue
        obj_id = fm.get("id")
        entries = fm.get("entries") or []
        codes = set()
        for entry in entries:
            if isinstance(entry, dict):
                code = entry.get("code")
                if code is not None:
                    codes.add(str(code))
        value_list_codes[obj_id] = codes
        status = str(fm.get("status", "")).lower()
        if status in ("active", "draft") and not codes:
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="LOV_EMPTY",
                    message=f"ValueList '{obj_id}' has no entries.",
                    object_id=obj_id,
                    source_file=obj.source_path,
                    field_path="entries",
                    suggested_fix="Add at least one entry to the value list.",
                )
            )

    for obj in objects:
        fm = obj.frontmatter or {}
        if fm.get("type") != "ValueMapping":
            continue
        obj_id = fm.get("id")
        status = str(fm.get("status", "")).lower()
        entries = fm.get("entries") or []
        if status in ("active", "draft") and not entries:
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="VALUE_MAPPING_EMPTY",
                    message=f"ValueMapping '{obj_id}' has no entries.",
                    object_id=obj_id,
                    source_file=obj.source_path,
                    field_path="entries",
                    suggested_fix="Add at least one mapping entry.",
                )
            )
        source_vl = fm.get("source_value_list")
        target_vl = fm.get("target_value_list")
        source_codes = value_list_codes.get(source_vl, set())
        target_codes = value_list_codes.get(target_vl, set())
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            src_code = entry.get("source_code")
            tgt_code = entry.get("target_code")
            if src_code is not None and source_vl and src_code not in source_codes:
                results.append(
                    ValidationResult(
                        severity=ValidationSeverity.ERROR,
                        code="VALUE_MAPPING_SOURCE_CODE_INVALID",
                        message=(
                            f"ValueMapping '{obj_id}' entry {idx} references "
                            f"source_code '{src_code}' not found in "
                            f"ValueList '{source_vl}'."
                        ),
                        object_id=obj_id,
                        source_file=obj.source_path,
                        field_path=f"entries[{idx}].source_code",
                        suggested_fix="Use a code that exists in the source ValueList.",
                    )
                )
            if tgt_code is not None and target_vl and tgt_code not in target_codes:
                results.append(
                    ValidationResult(
                        severity=ValidationSeverity.ERROR,
                        code="VALUE_MAPPING_TARGET_CODE_INVALID",
                        message=(
                            f"ValueMapping '{obj_id}' entry {idx} references "
                            f"target_code '{tgt_code}' not found in "
                            f"ValueList '{target_vl}'."
                        ),
                        object_id=obj_id,
                        source_file=obj.source_path,
                        field_path=f"entries[{idx}].target_code",
                        suggested_fix="Use a code that exists in the target ValueList.",
                    )
                )

    return results


def _validate_ownership(objects: list[ParsedObject]) -> list[ValidationResult]:
    """Warn when active important objects lack ownership."""
    results: list[ValidationResult] = []
    for obj in objects:
        if obj.parser_error is not None or obj.frontmatter is None:
            continue
        fm = obj.frontmatter
        obj_type = str(fm.get("type", ""))
        if obj_type not in _OWNERSHIP_TYPES:
            continue
        status = str(fm.get("status", "")).lower()
        if status not in ("active", "draft"):
            continue
        has_owner = any(fm.get(field) for field in _OWNERSHIP_FIELDS)
        if not has_owner:
            obj_id = fm.get("id")
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="OWNERSHIP_MISSING",
                    message=(
                        f"{obj_type} '{obj_id}' has no owner or steward. "
                        f"Consider adding business_owner, technical_owner, "
                        f"data_steward, accountable_team, or approver."
                    ),
                    object_id=obj_id,
                    source_file=obj.source_path,
                    field_path=None,
                    suggested_fix="Add an ownership field to this object.",
                )
            )
    return results


def _validate_methodology(
    objects: list[ParsedObject], registry: dict[str, dict[str, Any]]
) -> list[ValidationResult]:
    """Warn about weak model structure and missing enrichment.

    These are methodology-level quality checks, not hard errors.
    Simple table mode is intentionally not punished.
    """
    results: list[ValidationResult] = []

    # Categorise objects for quick lookups
    field_endpoints: list[ParsedObject] = []
    attributes: list[ParsedObject] = []
    entity_contexts: list[ParsedObject] = []
    value_lists: list[ParsedObject] = []
    mappings: list[ParsedObject] = []
    validation_rules: list[ParsedObject] = []
    business_entities: list[ParsedObject] = []
    attribute_usages: list[ParsedObject] = []

    for obj in objects:
        if obj.parser_error is not None or obj.frontmatter is None:
            continue
        ot = obj.frontmatter.get("type")
        if ot == "FieldEndpoint":
            field_endpoints.append(obj)
        elif ot == "Attribute":
            attributes.append(obj)
        elif ot == "EntityContext":
            entity_contexts.append(obj)
        elif ot == "ValueList":
            value_lists.append(obj)
        elif ot == "Mapping":
            mappings.append(obj)
        elif ot == "ValidationRule":
            validation_rules.append(obj)
        elif ot == "BusinessEntity":
            business_entities.append(obj)
        elif ot == "AttributeUsage":
            attribute_usages.append(obj)

    has_contexts = len(entity_contexts) > 0
    has_value_lists = len(value_lists) > 0
    has_mappings = len(mappings) > 0
    has_validation_rules = len(validation_rules) > 0

    # Which fields are referenced by mappings?
    mapped_fep_ids: set[str] = set()
    for m in mappings:
        fm = m.frontmatter or {}
        for key in ("source_endpoint", "target_endpoint"):
            val = fm.get(key)
            if isinstance(val, str):
                mapped_fep_ids.add(val)

    # Which attributes are referenced by validation rules?
    validated_attr_ids: set[str] = set()
    for vr in validation_rules:
        fm = vr.frontmatter or {}
        val = fm.get("attribute")
        if isinstance(val, str):
            validated_attr_ids.add(val)

    # Which field endpoints are referenced by attribute usages?
    fep_ids_with_usage: set[str] = set()
    for au in attribute_usages:
        fm = au.frontmatter or {}
        val = fm.get("field_endpoint")
        if isinstance(val, str):
            fep_ids_with_usage.add(val)

    # Rule 1: Active FieldEndpoints without Attribute or AttributeUsage
    for obj in field_endpoints:
        fm = obj.frontmatter
        status = str(fm.get("status", "")).lower()
        if status not in ("active", "draft"):
            continue
        obj_id = fm.get("id")
        has_attr = bool(fm.get("attribute") or fm.get("business_attribute"))
        has_usage = obj_id in fep_ids_with_usage
        if not has_attr and not has_usage:
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="FIELD_ENDPOINT_MISSING_ATTRIBUTE",
                    message=(
                        f"FieldEndpoint '{obj_id}' has no linked Attribute, "
                        f"business_attribute, or AttributeUsage."
                    ),
                    object_id=obj_id,
                    source_file=obj.source_path,
                    suggested_fix=(
                        "Add 'attribute' or 'business_attribute' to link this "
                        "field to business meaning, or create an AttributeUsage."
                    ),
                )
            )

    # Rule 2: Flat model structure (many fields, no contexts)
    active_feps = [
        obj
        for obj in field_endpoints
        if str(obj.frontmatter.get("status", "")).lower() in ("active", "draft")
    ]
    if len(active_feps) >= 10 and not has_contexts and business_entities:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.WARNING,
                code="FLAT_MODEL_STRUCTURE",
                message=(
                    f"Model has {len(active_feps)} FieldEndpoints but no "
                    f"EntityContext objects. Large objects may be flattened."
                ),
                object_id=None,
                source_file=None,
                suggested_fix=(
                    "Add EntityContext objects to group fields by system/"
                    "business grain. Use simple table mode intentionally for "
                    "small models."
                ),
            )
        )

    # Rule 3: Attributes without context in enterprise models
    if has_contexts:
        for obj in attributes:
            fm = obj.frontmatter
            status = str(fm.get("status", "")).lower()
            if status not in ("active", "draft"):
                continue
            if not fm.get("entity_context"):
                obj_id = fm.get("id")
                results.append(
                    ValidationResult(
                        severity=ValidationSeverity.WARNING,
                        code="ATTRIBUTE_MISSING_CONTEXT",
                        message=(
                            f"Attribute '{obj_id}' has no entity_context. "
                            f"In enterprise models, attributes should be "
                            f"contextualized."
                        ),
                        object_id=obj_id,
                        source_file=obj.source_path,
                        suggested_fix=(
                            "Add 'entity_context' to link this attribute to a "
                            "system/business grain."
                        ),
                    )
                )

    # Rule 4: FieldEndpoints lacking enrichment in mature models
    # Only when the model already has ValueLists, Mappings, or ValidationRules
    if has_value_lists or has_mappings or has_validation_rules:
        for obj in field_endpoints:
            fm = obj.frontmatter
            status = str(fm.get("status", "")).lower()
            if status not in ("active", "draft"):
                continue
            obj_id = fm.get("id")
            attr_id = fm.get("attribute") or fm.get("business_attribute")

            has_lov = bool(fm.get("value_list"))
            is_mapped = obj_id in mapped_fep_ids
            attr_has_rule = attr_id in validated_attr_ids

            missing: list[str] = []
            if has_value_lists and not has_lov:
                missing.append("value_list")
            if has_mappings and not is_mapped:
                missing.append("mapping")
            if has_validation_rules and not attr_has_rule:
                missing.append("validation_rule")

            if missing:
                results.append(
                    ValidationResult(
                        severity=ValidationSeverity.WARNING,
                        code="FIELD_ENDPOINT_MISSING_ENRICHMENT",
                        message=(
                            f"FieldEndpoint '{obj_id}' lacks enrichment: "
                            f"no {', '.join(missing)}."
                        ),
                        object_id=obj_id,
                        source_file=obj.source_path,
                        suggested_fix=(
                            "Add value_list, mapping, or validation rule "
                            "coverage where relevant."
                        ),
                    )
                )

    # Rule 5: Active AttributeUsage objects without usage_type
    for obj in attribute_usages:
        fm = obj.frontmatter
        status = str(fm.get("status", "")).lower()
        if status not in ("active", "draft"):
            continue
        obj_id = fm.get("id")
        if not fm.get("usage_type"):
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="ATTRIBUTE_USAGE_MISSING_TYPE",
                    message=(
                        f"AttributeUsage '{obj_id}' has no usage_type. "
                        f"Consider adding usage_type to clarify how the attribute is used."
                    ),
                    object_id=obj_id,
                    source_file=obj.source_path,
                    suggested_fix=(
                        "Add 'usage_type' (e.g. primary, secondary, derived, reference) "
                        "to this AttributeUsage."
                    ),
                )
            )

    return results


def _run_domain_pack_validation(
    objects: list[ParsedObject],
    registry: dict[str, dict[str, Any]],
    enabled_packs: list[str] | None,
) -> list[ValidationResult]:
    """Run domain-pack validators for enabled packs."""
    results: list[ValidationResult] = []
    packs = get_domain_packs(enabled_packs)
    for pack in packs:
        for r in pack.validate(objects, registry):
            results.append(
                ValidationResult(
                    severity=ValidationSeverity(r.get("severity", "ERROR")),
                    code=r["code"],
                    message=r["message"],
                    object_id=r.get("object_id"),
                    source_file=None,
                    field_path=None,
                    suggested_fix=r.get("suggested_fix"),
                )
            )
    return results


def validate_objects(
    objects: list[ParsedObject],
    enabled_domain_packs: list[str] | None = None,
) -> ValidationSummary:
    """Run Layer 1–3 deterministic validation on a batch of parsed objects.

    Args:
        objects: Parsed canonical objects to validate.
        enabled_domain_packs: List of domain pack identifiers to enable
            (e.g. ``["sap"]``). If None or empty, only generic validation runs.

    Returns:
        ValidationSummary with all results.
    """
    all_results: list[ValidationResult] = []

    for obj in objects:
        all_results.extend(_validate_individual(obj))

    all_results.extend(_detect_duplicate_ids(objects))

    registry = _build_registry(objects)
    all_results.extend(_validate_references(objects, registry))
    all_results.extend(_validate_lov_governance(objects, registry))
    all_results.extend(_validate_ownership(objects))
    all_results.extend(_validate_methodology(objects, registry))
    all_results.extend(_run_domain_pack_validation(objects, registry, enabled_domain_packs))

    return ValidationSummary(results=all_results)

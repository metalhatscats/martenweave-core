"""Layer 1–3 deterministic validation pipeline for canonical objects."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from modelops_core.repository import ParsedObject
from modelops_core.schemas import ObjectType, get_expected_target_types, get_sap_context_rules
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


def _validate_sap_context(
    objects: list[ParsedObject], registry: dict[str, dict[str, Any]]
) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    for obj in objects:
        if obj.parser_error is not None or obj.frontmatter is None:
            continue

        frontmatter = obj.frontmatter
        if frontmatter.get("type") != "FieldEndpoint":
            continue

        endpoint_type = frontmatter.get("endpoint_type")
        sap_table = frontmatter.get("sap_table")
        if endpoint_type != "sap_table_field" or not sap_table:
            continue

        obj_id = frontmatter.get("id")
        obj_id_str = str(obj_id) if isinstance(obj_id, str) else None

        entity_context_id = frontmatter.get("entity_context")
        if not entity_context_id:
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    code="SAP_CONTEXT_MISSING",
                    message=(
                        f"SAP FieldEndpoint '{obj_id_str}' missing "
                        f"required 'entity_context'."
                    ),
                    object_id=obj_id_str,
                    source_file=obj.source_path,
                    field_path="entity_context",
                    suggested_fix="Add the correct EntityContext ID for this SAP table.",
                )
            )
            continue

        if entity_context_id not in registry:
            continue

        context_fm = None
        for candidate in objects:
            if candidate.frontmatter and candidate.frontmatter.get("id") == entity_context_id:
                context_fm = candidate.frontmatter
                break

        if context_fm is None:
            continue

        context_category = context_fm.get("context_category")
        if not context_category:
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    code="SAP_CONTEXT_CATEGORY_MISSING",
                    message=(
                        f"EntityContext '{entity_context_id}' has no "
                        f"'context_category'."
                    ),
                    object_id=obj_id_str,
                    source_file=obj.source_path,
                    field_path="entity_context.context_category",
                    suggested_fix="Add a context_category to the EntityContext.",
                )
            )
            continue

        rules = {r.sap_table: r for r in get_sap_context_rules("FieldEndpoint")}
        rule = rules.get(sap_table)
        if rule is not None:
            required_category = rule.required_context_category
            error_code = rule.error_code
        else:
            required_category = None
            error_code = None

        if required_category is not None and context_category != required_category:
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    code=error_code,
                    message=(
                        f"SAP table '{sap_table}' requires EntityContext "
                        f"with context_category '{required_category}', "
                        f"but '{entity_context_id}' has "
                        f"'{context_category}'."
                    ),
                    object_id=obj_id_str,
                    source_file=obj.source_path,
                    field_path="entity_context.context_category",
                    suggested_fix=(
                        f"Link this FieldEndpoint to an EntityContext with "
                        f"context_category '{required_category}'."
                    ),
                )
            )

    return results


def validate_objects(objects: list[ParsedObject]) -> ValidationSummary:
    """Run Layer 1–3 deterministic validation on a batch of parsed objects."""
    all_results: list[ValidationResult] = []

    for obj in objects:
        all_results.extend(_validate_individual(obj))

    all_results.extend(_detect_duplicate_ids(objects))

    registry = _build_registry(objects)
    all_results.extend(_validate_references(objects, registry))
    all_results.extend(_validate_sap_context(objects, registry))

    return ValidationSummary(results=all_results)

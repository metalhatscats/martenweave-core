"""Layer 1–3 deterministic validation pipeline for canonical objects."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from modelops_core.domain_packs import get_domain_packs
from modelops_core.repository import ParsedObject
from modelops_core.schemas import ObjectType, get_expected_target_types
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
    }
)
_OWNERSHIP_FIELDS = (
    "business_owner",
    "technical_owner",
    "data_steward",
    "accountable_team",
    "approver",
)


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
    all_results.extend(_validate_ownership(objects))
    all_results.extend(_run_domain_pack_validation(objects, registry, enabled_domain_packs))

    return ValidationSummary(results=all_results)

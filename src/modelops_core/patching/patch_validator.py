"""PatchProposal deterministic validation."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.patching.patch_model import _ALLOWED_OPERATIONS
from modelops_core.schemas.registry import get_all_types, get_entry
from modelops_core.validation.result import ValidationResult, ValidationSeverity

_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$")


def _normalize_operation_name(op: str) -> str:
    """Map legacy/alias operation names to their canonical implementation."""
    if op in {"add_object", "create_issue"}:
        return "create_object"
    return op


def _load_existing_objects(repo_model_path: Path | None) -> dict[str, str | None]:
    """Return canonical object IDs mapped to their object type."""
    if repo_model_path is None or not repo_model_path.exists():
        return {}
    from modelops_core.repository import parse_file, scan_repository

    objects: dict[str, str | None] = {}
    for file_path in scan_repository(repo_model_path):
        try:
            parsed = parse_file(file_path)
            if parsed.frontmatter and parsed.frontmatter.get("id"):
                objects[str(parsed.frontmatter["id"])] = (
                    str(parsed.frontmatter["type"])
                    if parsed.frontmatter.get("type") is not None
                    else None
                )
        except Exception:
            continue
    return objects


def _is_path_traversal(value: str | None) -> bool:
    """Detect path traversal in a target_path value."""
    if not isinstance(value, str):
        return False
    if ".." in value:
        return True
    if value.startswith("/") or value.startswith("\\"):
        return True
    return False


def _iter_reference_values(value: Any, *, is_list: bool) -> list[tuple[str, Any]]:
    """Yield normalized reference values for a reference field."""
    if value in (None, ""):
        return []
    if is_list and isinstance(value, list):
        return [(f"[{idx}]", item) for idx, item in enumerate(value)]
    return [("", value)]


def validate_patch_proposal(
    proposal: dict[str, Any],
    repo_model_path: Path | None = None,
) -> list[ValidationResult]:
    """Validate a PatchProposal dict.

    Args:
        proposal: PatchProposal frontmatter dict.
        repo_model_path: Optional repository ``model/`` path. When provided,
            semantic checks (object existence, registered types) are performed.

    Returns:
        A list of ValidationResult findings.
    """
    results: list[ValidationResult] = []
    proposal_id = proposal.get("id")

    if not isinstance(proposal_id, str) or not _ID_PATTERN.match(proposal_id):
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="PATCH_ID_INVALID",
                message=f"Invalid patch proposal ID: '{proposal_id}'.",
                object_id=str(proposal_id) if proposal_id else None,
                suggested_fix="Use uppercase A–Z / 0–9 with hyphens only.",
            )
        )

    obj_type = proposal.get("type")
    if obj_type != "PatchProposal":
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="PATCH_TYPE_MISMATCH",
                message=f"Expected type 'PatchProposal', got '{obj_type}'.",
                object_id=str(proposal_id) if proposal_id else None,
                suggested_fix="Set type to 'PatchProposal'.",
            )
        )

    status = proposal.get("status")
    if status not in {"pending_review", "accepted", "rejected"}:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="PATCH_STATUS_INVALID",
                message=f"Invalid patch status: '{status}'.",
                object_id=str(proposal_id) if proposal_id else None,
                suggested_fix="Use 'pending_review', 'accepted', or 'rejected'.",
            )
        )

    existing_objects = _load_existing_objects(repo_model_path)
    existing_ids = set(existing_objects)
    registered_types = set(get_all_types())
    created_object_types: dict[str, str | None] = {}

    operations = proposal.get("operations", [])
    if isinstance(operations, list):
        for op in operations:
            if not isinstance(op, dict):
                continue
            op_type = op.get("op")
            if _normalize_operation_name(op_type) != "create_object":
                continue
            object_id = op.get("object_id")
            object_type = op.get("object_type")
            if (
                isinstance(object_id, str)
                and _ID_PATTERN.match(object_id)
                and isinstance(object_type, str)
                and object_type
            ):
                created_object_types[object_id] = object_type

    if not operations:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="PATCH_OPERATIONS_EMPTY",
                message="PatchProposal has no operations.",
                object_id=str(proposal_id) if proposal_id else None,
                suggested_fix="Add at least one operation.",
            )
        )
    elif isinstance(operations, list):
        for idx, op in enumerate(operations):
            if not isinstance(op, dict):
                continue
            op_type = op.get("op")
            if op_type not in _ALLOWED_OPERATIONS:
                results.append(
                    ValidationResult(
                        severity=ValidationSeverity.ERROR,
                        code="PATCH_OPERATION_DISALLOWED",
                        message=f"Operation '{op_type}' is not allowed.",
                        object_id=str(proposal_id) if proposal_id else None,
                        field_path=f"operations[{idx}].op",
                        suggested_fix=(
                            f"Allowed operations: {', '.join(sorted(_ALLOWED_OPERATIONS))}."
                        ),
                    )
                )
                continue

            canonical_op = _normalize_operation_name(op_type)
            object_id = op.get("object_id")
            target_path = op.get("target_path")
            object_type = op.get("object_type")
            if canonical_op == "create_object" and op_type == "create_issue" and not object_type:
                object_type = "Issue"
            after = op.get("after")

            if not isinstance(object_id, str) or not _ID_PATTERN.match(object_id):
                results.append(
                    ValidationResult(
                        severity=ValidationSeverity.ERROR,
                        code="PATCH_OPERATION_OBJECT_ID_INVALID",
                        message=f"Invalid object_id '{object_id}' in operation {idx}.",
                        object_id=str(proposal_id) if proposal_id else None,
                        field_path=f"operations[{idx}].object_id",
                        suggested_fix="Use uppercase A–Z / 0–9 with hyphens only.",
                    )
                )

            if _is_path_traversal(target_path):
                results.append(
                    ValidationResult(
                        severity=ValidationSeverity.ERROR,
                        code="PATCH_TARGET_PATH_TRAVERSAL",
                        message=(
                            f"target_path '{target_path}' in operation {idx} "
                            "contains path traversal."
                        ),
                        object_id=str(proposal_id) if proposal_id else None,
                        field_path=f"operations[{idx}].target_path",
                        suggested_fix="Use a plain frontmatter field name.",
                    )
                )

            if canonical_op == "update_object":
                if repo_model_path and existing_ids and object_id not in existing_ids:
                    results.append(
                        ValidationResult(
                            severity=ValidationSeverity.ERROR,
                            code="PATCH_UPDATE_OBJECT_NOT_FOUND",
                            message=(f"update_object targets non-existent object '{object_id}'."),
                            object_id=str(proposal_id) if proposal_id else None,
                            field_path=f"operations[{idx}].object_id",
                            suggested_fix="Target an existing canonical object ID.",
                        )
                    )
                if after in (None, ""):
                    results.append(
                        ValidationResult(
                            severity=ValidationSeverity.WARNING,
                            code="PATCH_AFTER_VALUE_EMPTY",
                            message=(f"update_object for '{object_id}' has an empty after value."),
                            object_id=str(proposal_id) if proposal_id else None,
                            field_path=f"operations[{idx}].after",
                            suggested_fix="Confirm the empty value is intentional.",
                        )
                    )

            elif canonical_op == "create_object":
                if repo_model_path and registered_types and object_type not in registered_types:
                    results.append(
                        ValidationResult(
                            severity=ValidationSeverity.ERROR,
                            code="PATCH_OBJECT_TYPE_UNREGISTERED",
                            message=(
                                f"create_object uses unregistered object_type '{object_type}'."
                            ),
                            object_id=str(proposal_id) if proposal_id else None,
                            field_path=f"operations[{idx}].object_type",
                            suggested_fix=(
                                f"Registered types: {', '.join(sorted(registered_types))}."
                            ),
                        )
                    )
                if isinstance(after, dict) and isinstance(object_type, str):
                    entry = get_entry(object_type)
                    if entry is not None:
                        for ref_field in entry.reference_fields:
                            for suffix, ref in _iter_reference_values(
                                after.get(ref_field.name),
                                is_list=ref_field.is_list,
                            ):
                                field_path = f"operations[{idx}].after.{ref_field.name}{suffix}"
                                if not isinstance(ref, str) or not _ID_PATTERN.match(ref):
                                    results.append(
                                        ValidationResult(
                                            severity=ValidationSeverity.ERROR,
                                            code="PATCH_REFERENCE_ID_INVALID",
                                            message=(
                                                f"{object_type}.{ref_field.name} references "
                                                f"invalid object ID '{ref}'."
                                            ),
                                            object_id=str(proposal_id) if proposal_id else None,
                                            field_path=field_path,
                                            suggested_fix="Use a valid canonical object ID.",
                                        )
                                    )
                                    continue

                                target_type = created_object_types.get(ref) or existing_objects.get(
                                    ref
                                )
                                if target_type is None:
                                    results.append(
                                        ValidationResult(
                                            severity=ValidationSeverity.ERROR,
                                            code="PATCH_REFERENCE_OBJECT_NOT_FOUND",
                                            message=(
                                                f"{object_type}.{ref_field.name} references "
                                                f"non-existent object '{ref}'."
                                            ),
                                            object_id=str(proposal_id) if proposal_id else None,
                                            field_path=field_path,
                                            suggested_fix=(
                                                "Reference an existing canonical object ID or "
                                                "create the target object in the same proposal."
                                            ),
                                        )
                                    )
                                    continue

                                if (
                                    ref_field.expected_target_type
                                    and target_type != ref_field.expected_target_type
                                ):
                                    results.append(
                                        ValidationResult(
                                            severity=ValidationSeverity.ERROR,
                                            code="PATCH_REFERENCE_TARGET_TYPE_MISMATCH",
                                            message=(
                                                f"{object_type}.{ref_field.name} references "
                                                f"'{ref}' of type '{target_type}', expected "
                                                f"'{ref_field.expected_target_type}'."
                                            ),
                                            object_id=str(proposal_id) if proposal_id else None,
                                            field_path=field_path,
                                            suggested_fix=(
                                                f"Reference a "
                                                f"{ref_field.expected_target_type} object."
                                            ),
                                        )
                                    )

    affected_objects = proposal.get("affected_objects")
    if affected_objects is not None:
        if not isinstance(affected_objects, list):
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="PATCH_AFFECTED_OBJECT_FORMAT",
                    message="affected_objects should be a list.",
                    object_id=str(proposal_id) if proposal_id else None,
                    suggested_fix="Change affected_objects to a list of object IDs.",
                )
            )
        else:
            for idx, ref in enumerate(affected_objects):
                if not isinstance(ref, str) or not _ID_PATTERN.match(ref):
                    results.append(
                        ValidationResult(
                            severity=ValidationSeverity.ERROR,
                            code="PATCH_AFFECTED_OBJECT_ID_INVALID",
                            message=(f"affected_objects[{idx}] has invalid object ID '{ref}'."),
                            object_id=str(proposal_id) if proposal_id else None,
                            field_path=f"affected_objects[{idx}]",
                            suggested_fix="Use a valid canonical object ID.",
                        )
                    )
                elif existing_ids and ref not in existing_ids:
                    if ref not in created_object_types:
                        results.append(
                            ValidationResult(
                                severity=ValidationSeverity.ERROR,
                                code="PATCH_AFFECTED_OBJECT_NOT_FOUND",
                                message=(
                                    f"affected_objects[{idx}] references non-existent object "
                                    f"'{ref}'."
                                ),
                                object_id=str(proposal_id) if proposal_id else None,
                                field_path=f"affected_objects[{idx}]",
                                suggested_fix=(
                                    "Reference an existing canonical object ID or create the "
                                    "target object in the same proposal."
                                ),
                            )
                        )

    expires_at = proposal.get("expires_at")
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(str(expires_at))
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=UTC)
            if exp_dt < datetime.now(UTC):
                results.append(
                    ValidationResult(
                        severity=ValidationSeverity.WARNING,
                        code="PATCH_PROPOSAL_EXPIRED",
                        message=f"PatchProposal expired on {expires_at}.",
                        object_id=str(proposal_id) if proposal_id else None,
                        suggested_fix="Renew expires_at or close the proposal.",
                    )
                )
        except ValueError:
            results.append(
                ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    code="PATCH_EXPIRES_AT_INVALID",
                    message=f"Invalid expires_at format: '{expires_at}'.",
                    object_id=str(proposal_id) if proposal_id else None,
                    suggested_fix="Use ISO 8601 format (e.g. 2024-12-31T23:59:59+00:00).",
                )
            )

    return results

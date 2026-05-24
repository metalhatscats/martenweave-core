"""PatchProposal deterministic validation."""

from __future__ import annotations

import re
from typing import Any

from modelops_core.patching.patch_model import _ALLOWED_OPERATIONS
from modelops_core.validation.result import ValidationResult, ValidationSeverity

_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$")


def validate_patch_proposal(proposal: dict[str, Any]) -> list[ValidationResult]:
    """Validate a PatchProposal dict.

    Returns a list of ValidationResult findings.
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

    operations = proposal.get("operations", [])
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
                            f"Allowed operations:"
                            f" {', '.join(sorted(_ALLOWED_OPERATIONS))}."
                        ),
                    )
                )

    affected_objects = proposal.get("affected_objects")
    if affected_objects is not None and not isinstance(affected_objects, list):
        results.append(
            ValidationResult(
                severity=ValidationSeverity.WARNING,
                code="PATCH_AFFECTED_OBJECT_FORMAT",
                message="affected_objects should be a list.",
                object_id=str(proposal_id) if proposal_id else None,
                suggested_fix="Change affected_objects to a list of object IDs.",
            )
        )

    return results

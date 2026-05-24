"""ChangeRequest deterministic validation."""

from __future__ import annotations

import re
from typing import Any

from modelops_core.validation.result import ValidationResult, ValidationSeverity

_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$")


def validate_change_request(change_request: dict[str, Any]) -> list[ValidationResult]:
    """Validate a ChangeRequest dict."""
    results: list[ValidationResult] = []
    cr_id = change_request.get("id")

    if not isinstance(cr_id, str) or not _ID_PATTERN.match(cr_id):
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="CHANGE_REQUEST_ID_INVALID",
                message=f"Invalid change request ID: '{cr_id}'.",
                object_id=str(cr_id) if cr_id else None,
                suggested_fix="Use uppercase A–Z / 0–9 with hyphens only.",
            )
        )

    obj_type = change_request.get("type")
    if obj_type != "ChangeRequest":
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="CHANGE_REQUEST_TYPE_MISMATCH",
                message=f"Expected type 'ChangeRequest', got '{obj_type}'.",
                object_id=str(cr_id) if cr_id else None,
                suggested_fix="Set type to 'ChangeRequest'.",
            )
        )

    status = change_request.get("status")
    if status not in {"pending", "approved", "rejected", "implemented"}:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="CHANGE_REQUEST_STATUS_INVALID",
                message=f"Invalid change request status: '{status}'.",
                object_id=str(cr_id) if cr_id else None,
                suggested_fix="Use 'pending', 'approved', 'rejected', or 'implemented'.",
            )
        )

    proposals = change_request.get("source_patch_proposals", [])
    if not proposals:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.WARNING,
                code="CHANGE_REQUEST_NO_PATCH_PROPOSALS",
                message="ChangeRequest has no source patch proposals.",
                object_id=str(cr_id) if cr_id else None,
                suggested_fix="Link at least one accepted PatchProposal.",
            )
        )

    approval_status = change_request.get("approval_status")
    if approval_status and approval_status not in {"pending", "approved", "rejected"}:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="CHANGE_REQUEST_APPROVAL_STATUS_INVALID",
                message=f"Invalid approval_status: '{approval_status}'.",
                object_id=str(cr_id) if cr_id else None,
                suggested_fix="Use 'pending', 'approved', or 'rejected'.",
            )
        )

    implementation_status = change_request.get("implementation_status")
    if implementation_status and implementation_status not in {
        "pending",
        "in_progress",
        "completed",
        "failed",
    }:
        results.append(
            ValidationResult(
                severity=ValidationSeverity.ERROR,
                code="CHANGE_REQUEST_IMPLEMENTATION_STATUS_INVALID",
                message=f"Invalid implementation_status: '{implementation_status}'.",
                object_id=str(cr_id) if cr_id else None,
                suggested_fix="Use 'pending', 'in_progress', 'completed', or 'failed'.",
            )
        )

    return results

"""Tests for patch proposal and change request validation."""

from __future__ import annotations

from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import build_patch_proposal
from modelops_core.patching.patch_validator import validate_patch_proposal


def test_valid_patch_proposal() -> None:
    op = PatchOperation(
        op="update_object", object_id="ATTR-TEST", target_path="name", after="New Name"
    )
    proposal = build_patch_proposal("PP-001", [op])
    results = validate_patch_proposal(proposal)
    assert not any(r.severity == "ERROR" for r in results)


def test_invalid_patch_id() -> None:
    op = PatchOperation(
        op="update_object", object_id="ATTR-TEST", target_path="name", after="New Name"
    )
    proposal = build_patch_proposal("pp-invalid", [op])
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_ID_INVALID" for r in results)


def test_empty_operations() -> None:
    proposal = build_patch_proposal("PP-001", [])
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_OPERATIONS_EMPTY" for r in results)


def test_disallowed_operation() -> None:
    op = PatchOperation(op="delete_object", object_id="ATTR-TEST")
    proposal = build_patch_proposal("PP-001", [op])
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_OPERATION_DISALLOWED" for r in results)

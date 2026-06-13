"""Tests for patch proposal and change request validation."""

from __future__ import annotations

from pathlib import Path

from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import build_patch_proposal
from modelops_core.patching.patch_validator import validate_patch_proposal


def _proposal_with_ops(*ops: PatchOperation, proposal_id: str = "PP-001") -> dict:
    return build_patch_proposal(proposal_id, list(ops))


def test_valid_patch_proposal() -> None:
    op = PatchOperation(
        op="update_object", object_id="ATTR-TEST", target_path="name", after="New Name"
    )
    proposal = build_patch_proposal("PP-001", [op])
    results = validate_patch_proposal(proposal)
    assert not any(r.severity == "ERROR" for r in results)


def test_valid_patch_proposal_with_repo_path(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="New Name"
    )
    proposal = build_patch_proposal("PP-VALID-REPO", [op])
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
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


def test_update_object_not_found(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="MISSING-OBJECT",
        target_path="name",
        after="New Name",
    )
    proposal = build_patch_proposal("PP-MISSING", [op])
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert any(r.code == "PATCH_UPDATE_OBJECT_NOT_FOUND" for r in results)


def test_create_object_unregistered_type(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_object",
        object_id="NEW-001",
        object_type="UnknownType",
        after={"id": "NEW-001", "type": "UnknownType", "status": "draft"},
    )
    proposal = build_patch_proposal("PP-BAD-TYPE", [op])
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert any(r.code == "PATCH_OBJECT_TYPE_UNREGISTERED" for r in results)


def test_create_object_registered_type_passes(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_object",
        object_id="SYS-001",
        object_type="System",
        after={"id": "SYS-001", "type": "System", "status": "draft"},
    )
    proposal = build_patch_proposal("PP-GOOD-TYPE", [op])
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert not any(r.severity == "ERROR" for r in results)


def test_target_path_traversal_dotdot() -> None:
    op = PatchOperation(
        op="update_object",
        object_id="ATTR-TEST",
        target_path="../name",
        after="X",
    )
    proposal = build_patch_proposal("PP-TRAV", [op])
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_TARGET_PATH_TRAVERSAL" for r in results)


def test_target_path_traversal_absolute() -> None:
    op = PatchOperation(
        op="update_object",
        object_id="ATTR-TEST",
        target_path="/etc/passwd",
        after="X",
    )
    proposal = build_patch_proposal("PP-ABS", [op])
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_TARGET_PATH_TRAVERSAL" for r in results)


def test_operation_object_id_invalid() -> None:
    op = PatchOperation(
        op="update_object",
        object_id="lowercase-id",
        target_path="name",
        after="X",
    )
    proposal = build_patch_proposal("PP-BAD-OBJ-ID", [op])
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_OPERATION_OBJECT_ID_INVALID" for r in results)


def test_empty_after_value_warning(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="",
    )
    proposal = build_patch_proposal("PP-EMPTY-AFTER", [op])
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert any(r.code == "PATCH_AFTER_VALUE_EMPTY" for r in results)
    assert all(r.severity != "ERROR" for r in results if r.code == "PATCH_AFTER_VALUE_EMPTY")


def test_multi_operation_proposal_all_valid(temp_model_dir: Path) -> None:
    ops = [
        PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"),
        PatchOperation(
            op="create_object",
            object_id="SYS-NEW",
            object_type="System",
            after={"id": "SYS-NEW", "type": "System", "status": "draft"},
        ),
    ]
    proposal = build_patch_proposal("PP-MULTI", ops)
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert not any(r.severity == "ERROR" for r in results)


def test_multi_operation_proposal_mixed_errors(temp_model_dir: Path) -> None:
    ops = [
        PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"),
        PatchOperation(
            op="update_object",
            object_id="MISSING",
            target_path="name",
            after="Y",
        ),
        PatchOperation(
            op="create_object",
            object_id="NEW-001",
            object_type="BadType",
            after={},
        ),
    ]
    proposal = build_patch_proposal("PP-MIXED", ops)
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert any(r.code == "PATCH_UPDATE_OBJECT_NOT_FOUND" for r in results)
    assert any(r.code == "PATCH_OBJECT_TYPE_UNREGISTERED" for r in results)


def test_unicode_in_operation_object_id_invalid() -> None:
    op = PatchOperation(
        op="update_object",
        object_id="ATTR-ÜNICODE",
        target_path="name",
        after="X",
    )
    proposal = build_patch_proposal("PP-UNICODE", [op])
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_OPERATION_OBJECT_ID_INVALID" for r in results)


def test_create_object_missing_type_is_unregistered(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_object",
        object_id="NEW-001",
        after={"id": "NEW-001"},
    )
    proposal = build_patch_proposal("PP-NO-TYPE", [op])
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert any(r.code == "PATCH_OBJECT_TYPE_UNREGISTERED" for r in results)


def test_proposal_status_invalid() -> None:
    proposal = build_patch_proposal("PP-001", [])
    proposal["status"] = "unknown"
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_STATUS_INVALID" for r in results)


def test_affected_objects_format_warning() -> None:
    proposal = build_patch_proposal("PP-001", [])
    proposal["affected_objects"] = "not-a-list"
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_AFFECTED_OBJECT_FORMAT" for r in results)


def test_affected_objects_valid_list_passes(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="New Name"
    )
    proposal = build_patch_proposal("PP-AFFECTED-OK", [op])
    proposal["affected_objects"] = ["DOMAIN-TEST"]
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert not any(r.severity == "ERROR" for r in results)


def test_affected_objects_invalid_id() -> None:
    op = PatchOperation(
        op="update_object", object_id="ATTR-TEST", target_path="name", after="New Name"
    )
    proposal = build_patch_proposal("PP-AFFECTED-BAD-ID", [op])
    proposal["affected_objects"] = ["lowercase-id"]
    results = validate_patch_proposal(proposal)
    assert any(r.code == "PATCH_AFFECTED_OBJECT_ID_INVALID" for r in results)


def test_affected_objects_not_found(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="New Name"
    )
    proposal = build_patch_proposal("PP-AFFECTED-MISSING", [op])
    proposal["affected_objects"] = ["MISSING-OBJECT"]
    results = validate_patch_proposal(proposal, repo_model_path=temp_model_dir)
    assert any(r.code == "PATCH_AFFECTED_OBJECT_NOT_FOUND" for r in results)

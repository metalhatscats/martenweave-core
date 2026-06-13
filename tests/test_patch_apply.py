"""Tests for patch apply service."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.patching.apply_service import apply_patch_proposal
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    write_patch_proposal,
)


def test_apply_update_object(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="Updated Domain Name",
    )
    proposal = build_patch_proposal("PP-APPLY-001", [op])
    write_patch_proposal(proposal, temp_model_dir)

    # Transition to accepted
    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-APPLY-001.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    result = apply_patch_proposal(temp_model_dir, "PP-APPLY-001")
    assert result.application_status == "applied"
    assert str(temp_model_dir / "DOMAIN-TEST.md") in result.changed_files

    # Verify file was updated
    from modelops_core.repository import parse_file

    updated = parse_file(temp_model_dir / "DOMAIN-TEST.md")
    assert updated.frontmatter is not None
    assert updated.frontmatter["name"] == "Updated Domain Name"


def test_apply_creates_object(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_object",
        object_id="SYS-NEW",
        object_type="System",
        after={"id": "SYS-NEW", "type": "System", "status": "draft", "name": "New System"},
    )
    proposal = build_patch_proposal("PP-APPLY-002", [op])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-APPLY-002.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    result = apply_patch_proposal(temp_model_dir, "PP-APPLY-002")
    assert result.application_status == "applied"

    from modelops_core.repository import parse_file

    created = parse_file(temp_model_dir / "systems" / "SYS-NEW.md")
    assert created.frontmatter is not None
    assert created.frontmatter["id"] == "SYS-NEW"


def test_apply_rejects_unaccepted_proposal(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    proposal = build_patch_proposal("PP-APPLY-003", [op])
    write_patch_proposal(proposal, temp_model_dir)

    with pytest.raises(ValueError, match="Only 'accepted' proposals can be applied"):
        apply_patch_proposal(temp_model_dir, "PP-APPLY-003")


def test_apply_rejects_invalid_proposal_empty_operations(temp_model_dir: Path) -> None:
    """Accepted proposals with empty operations cannot apply."""
    proposal = build_patch_proposal("PP-APPLY-EMPTY", [])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-APPLY-EMPTY.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    with pytest.raises(ValueError, match="PATCH_OPERATIONS_EMPTY"):
        apply_patch_proposal(temp_model_dir, "PP-APPLY-EMPTY")

    # No files should have been mutated
    assert not (temp_model_dir / "systems" / "SYS-NEW.md").exists()


def test_apply_rejects_invalid_proposal_disallowed_operation(temp_model_dir: Path) -> None:
    """Accepted proposals with disallowed operations cannot apply."""
    op = PatchOperation(op="delete_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    proposal = build_patch_proposal("PP-APPLY-BAD-OP", [op])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-APPLY-BAD-OP.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    with pytest.raises(ValueError, match="PATCH_OPERATION_DISALLOWED"):
        apply_patch_proposal(temp_model_dir, "PP-APPLY-BAD-OP")

    # No files should have been mutated
    from modelops_core.repository import parse_file

    updated = parse_file(temp_model_dir / "DOMAIN-TEST.md")
    assert updated.frontmatter is not None
    assert updated.frontmatter["name"] != "X"


def test_apply_update_invalid_status_blocked(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="status",
        after="bogus_status",
    )
    proposal = build_patch_proposal("PP-APPLY-BAD-STATUS", [op])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-APPLY-BAD-STATUS.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    with pytest.raises(ValueError, match="Pre-write validation failed"):
        apply_patch_proposal(temp_model_dir, "PP-APPLY-BAD-STATUS")

    from modelops_core.repository import parse_file

    updated = parse_file(temp_model_dir / "DOMAIN-TEST.md")
    assert updated.frontmatter is not None
    assert updated.frontmatter["status"] == "draft"


def test_apply_update_broken_reference_blocked(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="ATTR-TEST",
        target_path="domain",
        after="NONEXISTENT-DOMAIN",
    )
    proposal = build_patch_proposal("PP-APPLY-BAD-REF", [op])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-APPLY-BAD-REF.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    with pytest.raises(ValueError, match="Pre-write validation failed"):
        apply_patch_proposal(temp_model_dir, "PP-APPLY-BAD-REF")

    from modelops_core.repository import parse_file

    updated = parse_file(temp_model_dir / "ATTR-TEST.md")
    assert updated.frontmatter is not None
    assert updated.frontmatter["domain"] == "DOMAIN-TEST"


def test_apply_create_sap_context_violation_blocked(sample_repo: Path) -> None:
    model_dir = sample_repo / "model"
    op = PatchOperation(
        op="create_object",
        object_id="FEP-BAD-SAP",
        object_type="FieldEndpoint",
        after={
            "id": "FEP-BAD-SAP",
            "type": "FieldEndpoint",
            "status": "draft",
            "name": "Bad SAP Field",
            "endpoint_type": "sap_table_field",
            "sap_table": "KNVV",
        },
    )
    proposal = build_patch_proposal("PP-APPLY-BAD-SAP", [op])
    write_patch_proposal(proposal, model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = model_dir / "patch-proposals" / "PP-APPLY-BAD-SAP.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    with pytest.raises(ValueError, match="Pre-write validation failed"):
        apply_patch_proposal(model_dir, "PP-APPLY-BAD-SAP")

    assert not (model_dir / "field-endpoints" / "FEP-BAD-SAP.md").exists()


def test_apply_update_warning_allowed(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="",
    )
    proposal = build_patch_proposal("PP-APPLY-WARN", [op])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-APPLY-WARN.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    result = apply_patch_proposal(temp_model_dir, "PP-APPLY-WARN")
    assert result.application_status == "applied"
    assert any("DISPLAY_NAME_MISSING" in w for w in result.pre_write_warnings)

    from modelops_core.repository import parse_file

    updated = parse_file(temp_model_dir / "DOMAIN-TEST.md")
    assert updated.frontmatter is not None
    assert updated.frontmatter["name"] == ""



def test_apply_add_object_alias(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="add_object",
        object_id="SYS-ALIAS",
        object_type="System",
        after={"id": "SYS-ALIAS", "type": "System", "status": "draft", "name": "Alias System"},
    )
    proposal = build_patch_proposal("PP-ALIAS-001", [op])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-ALIAS-001.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    result = apply_patch_proposal(temp_model_dir, "PP-ALIAS-001")
    assert result.application_status == "applied"

    from modelops_core.repository import parse_file

    created = parse_file(temp_model_dir / "systems" / "SYS-ALIAS.md")
    assert created.frontmatter is not None
    assert created.frontmatter["id"] == "SYS-ALIAS"


def test_apply_create_issue_alias(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_issue",
        object_id="ISS-001",
        after={"id": "ISS-001", "name": "Missing owner", "status": "open"},
    )
    proposal = build_patch_proposal("PP-ISSUE-001", [op])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-ISSUE-001.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    result = apply_patch_proposal(temp_model_dir, "PP-ISSUE-001")
    assert result.application_status == "applied"

    from modelops_core.repository import parse_file

    created = parse_file(temp_model_dir / "issues" / "ISS-001.md")
    assert created.frontmatter is not None
    assert created.frontmatter["type"] == "Issue"


def test_apply_rejects_add_relationship(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="add_relationship",
        object_id="DOMAIN-TEST",
        target_path="related_to",
        after="OTHER",
    )
    proposal = build_patch_proposal("PP-BAD-REL", [op])
    write_patch_proposal(proposal, temp_model_dir)

    from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

    proposal_path = temp_model_dir / "patch-proposals" / "PP-BAD-REL.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

    with pytest.raises(ValueError, match="PATCH_OPERATION_DISALLOWED"):
        apply_patch_proposal(temp_model_dir, "PP-BAD-REL")



def test_allowed_operations_are_supported_by_apply_service() -> None:
    """Patch validator and apply service must agree on the operation set."""
    from modelops_core.patching.apply_service import (
        _SUPPORTED_OPERATIONS,
        _normalize_operation_name,
    )
    from modelops_core.patching.patch_model import _ALLOWED_OPERATIONS

    for op in _ALLOWED_OPERATIONS:
        assert op in _SUPPORTED_OPERATIONS, f"Allowed operation {op!r} not supported by apply"
        canonical = _normalize_operation_name(op)
        assert canonical in {"update_object", "create_object"}, (
            f"Operation {op!r} normalizes to unhandled {canonical!r}"
        )

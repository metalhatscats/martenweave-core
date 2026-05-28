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
    op = PatchOperation(
        op="delete_object", object_id="DOMAIN-TEST", target_path="name", after="X"
    )
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

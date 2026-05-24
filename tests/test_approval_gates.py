"""Tests for approval gates and risk assessment (issue #32)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.approval.risk_service import (
    RiskAssessment,
    assess_change_request,
    compute_proposal_risk,
)
from modelops_core.change_request.service import (
    approve_change_request,
    create_change_request,
    find_approved_cr_for_proposal,
    reject_change_request,
)
from modelops_core.cli import app
from modelops_core.index import build_index
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    transition_patch_proposal_status,
    write_patch_proposal,
)

runner = CliRunner()


def _repo_from_model(model_dir: Path) -> str:
    return str(model_dir.parent)


def test_low_risk_for_draft_attribute_update(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )

    operations = [
        {"op": "update_object", "object_id": "DOMAIN-TEST", "target_path": "name", "after": "X"}
    ]
    risk = compute_proposal_risk(operations, model_dir)

    assert isinstance(risk, RiskAssessment)
    assert risk.requires_approval is False
    assert risk.risk_level == "low"
    assert risk.risk_reasons == []


def test_high_risk_for_active_mapping_update(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "MAP-001.md").write_text(
        "---\n"
        "id: MAP-001\n"
        "type: Mapping\n"
        "status: active\n"
        "name: Test Mapping\n"
        "---\n",
        encoding="utf-8",
    )

    operations = [
        {"op": "update_object", "object_id": "MAP-001", "target_path": "name", "after": "X"}
    ]
    risk = compute_proposal_risk(operations, model_dir)

    assert risk.requires_approval is True
    assert risk.risk_level == "high"
    assert any("high-risk object type" in r for r in risk.risk_reasons)
    assert any("active object" in r for r in risk.risk_reasons)


def test_risk_for_ownership_field_change(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "ATTR-001.md").write_text(
        "---\n"
        "id: ATTR-001\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test\n"
        "---\n",
        encoding="utf-8",
    )

    operations = [
        {
            "op": "update_object",
            "object_id": "ATTR-001",
            "target_path": "business_owner",
            "after": "alice",
        }
    ]
    risk = compute_proposal_risk(operations, model_dir)

    assert risk.requires_approval is True
    assert risk.risk_level == "medium"
    assert any("governance field" in r for r in risk.risk_reasons)


def test_risk_for_many_affected_objects(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    operations = [
        {"op": "update_object", "object_id": f"OBJ-{i:03d}", "target_path": "name", "after": "X"}
        for i in range(6)
    ]
    risk = compute_proposal_risk(operations, model_dir)

    assert risk.requires_approval is True
    assert any("affects 6 objects" in r for r in risk.risk_reasons)


def test_assess_change_request(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "MAP-001.md").write_text(
        "---\n"
        "id: MAP-001\n"
        "type: Mapping\n"
        "status: active\n"
        "name: Test\n"
        "---\n",
        encoding="utf-8",
    )

    cr_fm = {
        "id": "CR-001",
        "type": "ChangeRequest",
        "status": "pending",
        "affected_objects": ["MAP-001"],
    }
    risk = assess_change_request(cr_fm, model_dir)

    assert risk.requires_approval is True
    assert risk.risk_level == "high"


def test_cr_approve_and_reject(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    create_change_request(
        model_path=model_dir,
        cr_id="CR-APPROVE-001",
        title="Test",
        status="pending",
    )

    cr = approve_change_request(model_dir, "CR-APPROVE-001", "alice")
    assert cr["status"] == "approved"
    assert len(cr["approvals"]) == 1
    assert cr["approvals"][0]["approver"] == "alice"
    assert cr["approvals"][0]["decision"] == "approved"

    cr2 = reject_change_request(model_dir, "CR-APPROVE-001", "bob")
    assert cr2["status"] == "rejected"
    assert len(cr2["approvals"]) == 2
    assert cr2["approvals"][1]["approver"] == "bob"
    assert cr2["approvals"][1]["decision"] == "rejected"


def test_find_approved_cr_for_proposal(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    create_change_request(
        model_path=model_dir,
        cr_id="CR-LINK-001",
        title="Linked",
        status="pending",
        linked_proposals=["PP-LINKED"],
    )
    approve_change_request(model_dir, "CR-LINK-001", "alice")

    found = find_approved_cr_for_proposal(model_dir, "PP-LINKED")
    assert found is not None
    assert found["id"] == "CR-LINK-001"

    missing = find_approved_cr_for_proposal(model_dir, "PP-OTHER")
    assert missing is None


def test_cli_cr_approve(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-CLI-001",
            "--title",
            "CLI Test",
            "--repo",
            str(repo_root),
        ],
    )

    result = runner.invoke(
        app,
        [
            "change-request",
            "approve",
            "CR-CLI-001",
            "--repo",
            str(repo_root),
            "--approver",
            "alice",
        ],
    )
    assert result.exit_code == 0
    assert "approved by alice" in result.output


def test_cli_cr_reject(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-CLI-002",
            "--title",
            "CLI Reject",
            "--repo",
            str(repo_root),
        ],
    )

    result = runner.invoke(
        app,
        [
            "change-request",
            "reject",
            "CR-CLI-002",
            "--repo",
            str(repo_root),
            "--approver",
            "bob",
        ],
    )
    assert result.exit_code == 0
    assert "rejected by bob" in result.output


def test_cli_proposal_apply_blocks_high_risk_without_cr(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "MAP-001.md").write_text(
        "---\n"
        "id: MAP-001\n"
        "type: Mapping\n"
        "status: active\n"
        "name: Test Mapping\n"
        "---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    op = PatchOperation(
        op="update_object", object_id="MAP-001", target_path="name", after="New"
    )
    proposal = build_patch_proposal("PP-HIGH-001", [op])
    write_patch_proposal(proposal, model_dir)
    proposal_path = model_dir / "patch-proposals" / "PP-HIGH-001.md"
    transition_patch_proposal_status(proposal_path, "accepted")

    result = runner.invoke(
        app,
        ["proposal", "apply", "PP-HIGH-001", "--repo", str(repo_root)],
    )
    assert result.exit_code == 1
    assert "Approval required" in result.output


def test_cli_proposal_apply_allows_with_approved_cr(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "MAP-001.md").write_text(
        "---\n"
        "id: MAP-001\n"
        "type: Mapping\n"
        "status: active\n"
        "name: Test Mapping\n"
        "---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    op = PatchOperation(
        op="update_object", object_id="MAP-001", target_path="name", after="New"
    )
    proposal = build_patch_proposal("PP-HIGH-002", [op])
    write_patch_proposal(proposal, model_dir)
    proposal_path = model_dir / "patch-proposals" / "PP-HIGH-002.md"
    transition_patch_proposal_status(proposal_path, "accepted")

    # Create and approve CR linking to proposal
    create_change_request(
        model_path=model_dir,
        cr_id="CR-PP-002",
        title="Approve PP",
        status="pending",
        linked_proposals=["PP-HIGH-002"],
    )
    approve_change_request(model_dir, "CR-PP-002", "alice")

    result = runner.invoke(
        app,
        ["proposal", "apply", "PP-HIGH-002", "--repo", str(repo_root)],
    )
    assert result.exit_code == 0
    assert "Applied PP-HIGH-002" in result.output


def test_cli_proposal_apply_force_bypasses_gate(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "MAP-001.md").write_text(
        "---\n"
        "id: MAP-001\n"
        "type: Mapping\n"
        "status: active\n"
        "name: Test Mapping\n"
        "---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    op = PatchOperation(
        op="update_object", object_id="MAP-001", target_path="name", after="New"
    )
    proposal = build_patch_proposal("PP-HIGH-003", [op])
    write_patch_proposal(proposal, model_dir)
    proposal_path = model_dir / "patch-proposals" / "PP-HIGH-003.md"
    transition_patch_proposal_status(proposal_path, "accepted")

    result = runner.invoke(
        app,
        ["proposal", "apply", "PP-HIGH-003", "--repo", str(repo_root), "--force"],
    )
    assert result.exit_code == 0
    assert "Applied PP-HIGH-003" in result.output


def test_cli_proposal_impact_shows_risk(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "MAP-001.md").write_text(
        "---\n"
        "id: MAP-001\n"
        "type: Mapping\n"
        "status: active\n"
        "name: Test Mapping\n"
        "---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-RISK-001.md").write_text(
        "---\n"
        "id: PP-RISK-001\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: MAP-001\n"
        "    target_path: name\n"
        "    after: New\n"
        "---\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["proposal", "impact", "PP-RISK-001", "--repo", str(repo_root)],
    )
    assert result.exit_code == 0
    assert "Risk level" in result.output


def test_cli_proposal_impact_json_includes_risk(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    repo_root = tmp_path

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-RISK-002.md").write_text(
        "---\n"
        "id: PP-RISK-002\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: DOMAIN-TEST\n"
        "    target_path: name\n"
        "    after: New\n"
        "---\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["proposal", "impact", "PP-RISK-002", "--repo", str(repo_root), "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "risk_assessment" in data
    assert data["risk_assessment"]["risk_level"] == "low"

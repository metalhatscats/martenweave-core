"""End-to-end tests for the full proposal lifecycle including rejection path."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.index.sqlite_builder import build_index
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    transition_patch_proposal_status,
    write_patch_proposal,
)
from modelops_core.reports.audit_service import AuditEventService
from modelops_core.repository import parse_file

runner = CliRunner()


def _init_repo(tmp_path: Path) -> Path:
    """Create a minimal temp repo with config, model, generated dirs."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "PERSON-OWNER.md").write_text(
        "---\nid: TEST-OWNER\ntype: Person\nstatus: active\nname: Test Owner\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\nid: ATTR-TEST\ntype: Attribute\nstatus: draft\n"
        "name: Test Attribute\ndomain: DOMAIN-TEST\n"
        "business_owner: TEST-OWNER\n---\n",
        encoding="utf-8",
    )

    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )

    build_index(repo_root=tmp_path, db_path=generated_dir / "modelops.db")
    return tmp_path


def _create_proposal(
    repo_root: Path, proposal_id: str = "PP-001", ops: list[PatchOperation] | None = None
) -> Path:
    """Create and write a PatchProposal to the repo."""
    if ops is None:
        ops = [
            PatchOperation(
                op="update_object",
                object_id="ATTR-TEST",
                object_type="Attribute",
                target_path="name",
                after="Updated Attribute Name",
                reason="E2E test update",
            )
        ]
    proposal = build_patch_proposal(
        proposal_id=proposal_id,
        operations=ops,
        affected_objects=["ATTR-TEST"],
        source_evidence="E2E lifecycle test",
        created_by="system",
    )
    model_path = repo_root / "model"
    return write_patch_proposal(proposal, model_path)


class TestHappyPathLifecycle:
    """Full lifecycle: create → validate → impact → diff → accept → dry-run → apply → audit."""

    def test_proposal_validate(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)
        result = runner.invoke(
            app, ["proposal", "validate", "PP-001", "--repo", str(repo), "--json"]
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-001"
        assert data["error_count"] == 0

    def test_proposal_impact(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)
        result = runner.invoke(app, ["proposal", "impact", "PP-001", "--repo", str(repo), "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-001"
        assert "high_risk" in data

    def test_proposal_diff(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)
        result = runner.invoke(app, ["proposal", "diff", "PP-001", "--repo", str(repo), "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-001"
        diffs = data.get("diffs", [])
        assert any(d.get("target_path") == "name" for d in diffs)

    def test_dry_run_does_not_mutate(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)
        proposal_path = repo / "model" / "patch-proposals" / "PP-001.md"
        transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

        attr_path = repo / "model" / "ATTR-TEST.md"
        content_before = attr_path.read_text(encoding="utf-8")
        mtime_before = attr_path.stat().st_mtime

        result = runner.invoke(
            app, ["proposal", "apply", "PP-001", "--repo", str(repo), "--dry-run", "--json"]
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["would_change"] is True

        content_after = attr_path.read_text(encoding="utf-8")
        mtime_after = attr_path.stat().st_mtime
        assert content_before == content_after
        assert mtime_before == mtime_after

    def test_apply_mutates_and_audit(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)
        proposal_path = repo / "model" / "patch-proposals" / "PP-001.md"
        transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

        attr_path = repo / "model" / "ATTR-TEST.md"
        content_before = attr_path.read_text(encoding="utf-8")
        assert "Test Attribute" in content_before

        result = runner.invoke(
            app, ["proposal", "apply", "PP-001", "--repo", str(repo), "--apply", "--json"]
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["applied"] is True

        content_after = attr_path.read_text(encoding="utf-8")
        assert "Updated Attribute Name" in content_after

        # Audit verification
        service = AuditEventService(repo)
        events = service.read_events()
        event_types = [e.event_type for e in events]
        assert "patch_apply" in event_types

    def test_full_lifecycle_audit_events(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)

        # validate
        runner.invoke(app, ["proposal", "validate", "PP-001", "--repo", str(repo)])

        # accept
        proposal_path = repo / "model" / "patch-proposals" / "PP-001.md"
        transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

        # dry-run
        runner.invoke(app, ["proposal", "apply", "PP-001", "--repo", str(repo), "--dry-run"])

        # apply
        runner.invoke(app, ["proposal", "apply", "PP-001", "--repo", str(repo), "--apply"])

        service = AuditEventService(repo)
        events = service.read_events()
        event_types = [e.event_type for e in events]

        assert "proposal_validated" in event_types
        assert "patch_dry_run" in event_types
        assert "patch_apply" in event_types
        assert "proposal_status_changed" in event_types

        status_event = next(e for e in events if e.event_type == "proposal_status_changed")
        assert status_event.metadata.get("old_status") == "pending_review"
        assert status_event.metadata.get("new_status") == "accepted"
        assert status_event.actor == "alice"


class TestRejectionPath:
    """Rejection lifecycle: create → reject → verify display → audit."""

    def test_reject_proposal_and_verify_show(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)

        proposal_path = repo / "model" / "patch-proposals" / "PP-001.md"
        transition_patch_proposal_status(
            proposal_path,
            "rejected",
            reviewer="bob",
            reviewer_notes="Needs more evidence",
            rejection_reason="insufficient_evidence",
        )

        result = runner.invoke(app, ["proposal", "show", "PP-001", "--repo", str(repo), "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["status"] == "rejected"
        assert data["reviewer"] == "bob"
        assert data["rejection_reason"] == "insufficient_evidence"
        assert data["reviewer_notes"] == "Needs more evidence"

    def test_reject_proposal_and_verify_report(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)

        proposal_path = repo / "model" / "patch-proposals" / "PP-001.md"
        transition_patch_proposal_status(
            proposal_path,
            "rejected",
            reviewer="bob",
            rejection_reason="insufficient_evidence",
        )

        result = runner.invoke(app, ["proposal", "report", "--repo", str(repo), "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["by_status"]["rejected"] == 1
        assert data["rejected_analysis"]["total_rejected"] == 1
        assert data["rejected_analysis"]["rejection_reason_frequencies"] == {
            "insufficient_evidence": 1
        }
        assert data["rejected_analysis"]["rejected_by_reviewer"] == {"bob": 1}

    def test_reject_proposal_audit_event(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)

        proposal_path = repo / "model" / "patch-proposals" / "PP-001.md"
        transition_patch_proposal_status(
            proposal_path,
            "rejected",
            reviewer="bob",
            rejection_reason="insufficient_evidence",
        )

        service = AuditEventService(repo)
        events = service.read_events()
        reject_event = next((e for e in events if e.event_type == "proposal_status_changed"), None)
        assert reject_event is not None
        assert reject_event.metadata.get("old_status") == "pending_review"
        assert reject_event.metadata.get("new_status") == "rejected"
        assert reject_event.metadata.get("reason") == "insufficient_evidence"
        assert reject_event.actor == "bob"


class TestChangeRequestApproval:
    """Verify ChangeRequest creation and approval emit expected events."""

    def test_cr_create_and_approve_audit(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)

        result = runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-001",
                "--title",
                "Test CR",
                "--repo",
                str(repo),
            ],
        )
        assert result.exit_code == 0, result.output

        result = runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-001",
                "--approver",
                "alice",
                "--repo",
                str(repo),
            ],
        )
        assert result.exit_code == 0, result.output

        service = AuditEventService(repo)
        events = service.read_events()
        event_types = [e.event_type for e in events]
        assert "change_request_approved" in event_types

        approve_event = next(e for e in events if e.event_type == "change_request_approved")
        assert approve_event.actor == "alice"
        assert approve_event.status == "success"

    def test_accept_auto_creates_and_approves_cr(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)

        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-001",
                "--repo",
                str(repo),
                "--reviewer",
                "alice",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["status"] == "accepted"
        assert data["change_request_id"] == "CR-PP-001"
        assert data["change_request_status"] == "approved"

        # Verify CR file exists and is approved
        cr_path = repo / "model" / "change-requests" / "CR-PP-001.md"
        assert cr_path.exists()
        parsed = parse_file(cr_path)
        assert parsed.frontmatter is not None
        assert parsed.frontmatter["status"] == "approved"
        assert parsed.frontmatter["linked_proposals"] == ["PP-001"]

        # Verify audit events
        service = AuditEventService(repo)
        events = service.read_events()
        event_types = [e.event_type for e in events]
        assert "proposal_status_changed" in event_types
        assert "change_request_approved" in event_types

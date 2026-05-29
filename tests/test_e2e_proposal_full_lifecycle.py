"""End-to-end test for the complete proposal lifecycle in a single flow."""

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


def _create_proposal(repo_root: Path) -> Path:
    """Create and write a PatchProposal to the repo."""
    ops = [
        PatchOperation(
            op="update_object",
            object_id="ATTR-TEST",
            object_type="Attribute",
            target_path="name",
            after="Updated Attribute Name",
            reason="E2E lifecycle test",
        )
    ]
    proposal = build_patch_proposal(
        proposal_id="PP-E2E-001",
        operations=ops,
        affected_objects=["ATTR-TEST"],
        source_evidence="E2E lifecycle test",
        created_by="system",
    )
    model_path = repo_root / "model"
    return write_patch_proposal(proposal, model_path)


class TestFullProposalLifecycle:
    """Exercise the full propose → review-bundle → accept → dry-run → apply → audit flow."""

    def test_full_lifecycle(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _create_proposal(repo)

        # 1. review-bundle
        result = runner.invoke(
            app,
            [
                "proposal",
                "review-bundle",
                "PP-E2E-001",
                "--repo",
                str(repo),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        bundle = json.loads(result.output)
        assert bundle["proposal_id"] == "PP-E2E-001"
        assert bundle["report"]["status"] == "pending_review"
        assert bundle["report"]["operations_count"] == 1
        assert bundle["validation"]["is_safe"] is True
        assert bundle["validation"]["error_count"] == 0

        # 2. accept
        proposal_path = repo / "model" / "patch-proposals" / "PP-E2E-001.md"
        transition_patch_proposal_status(
            proposal_path, "accepted", reviewer="alice", reviewer_notes="LGTM"
        )

        result = runner.invoke(
            app, ["proposal", "show", "PP-E2E-001", "--repo", str(repo), "--json"]
        )
        assert result.exit_code == 0, result.output
        show_data = json.loads(result.output)
        assert show_data["status"] == "accepted"
        assert show_data["reviewer"] == "alice"

        # 3. dry-run apply
        attr_path = repo / "model" / "ATTR-TEST.md"
        content_before = attr_path.read_text(encoding="utf-8")
        mtime_before = attr_path.stat().st_mtime

        result = runner.invoke(
            app,
            [
                "proposal",
                "apply",
                "PP-E2E-001",
                "--repo",
                str(repo),
                "--dry-run",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        dry_run_data = json.loads(result.output)
        assert dry_run_data["dry_run"] is True
        assert dry_run_data["would_change"] is True

        content_after_dry = attr_path.read_text(encoding="utf-8")
        mtime_after_dry = attr_path.stat().st_mtime
        assert content_before == content_after_dry
        assert mtime_before == mtime_after_dry

        # 4. apply
        result = runner.invoke(
            app,
            [
                "proposal",
                "apply",
                "PP-E2E-001",
                "--repo",
                str(repo),
                "--apply",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        apply_data = json.loads(result.output)
        assert apply_data["applied"] is True
        assert apply_data["proposal_id"] == "PP-E2E-001"
        assert apply_data["changed_files"] != []

        content_after_apply = attr_path.read_text(encoding="utf-8")
        assert "Updated Attribute Name" in content_after_apply

        # 5. audit log verification
        service = AuditEventService(repo)
        events = service.read_events()
        event_types = [e.event_type for e in events]

        assert "patch_dry_run" in event_types
        assert "patch_apply" in event_types
        assert "proposal_status_changed" in event_types

        status_event = next(e for e in events if e.event_type == "proposal_status_changed")
        assert status_event.metadata.get("old_status") == "pending_review"
        assert status_event.metadata.get("new_status") == "accepted"
        assert status_event.actor == "alice"

        apply_event = next(e for e in events if e.event_type == "patch_apply")
        assert apply_event.status == "success"
        assert apply_event.proposal_id == "PP-E2E-001"

        # 6. index rebuilt verification
        db_path = repo / "generated" / "modelops.db"
        assert db_path.exists()
        # Verify the DB was modified after apply by checking mtime
        db_mtime = db_path.stat().st_mtime
        assert db_mtime > mtime_before

"""Tests for change request service."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.patching.change_request_service import (
    approve_change_request,
    build_change_request_from_patch_proposal,
    reject_change_request,
    render_change_request_markdown,
    write_change_request,
)


class TestBuildChangeRequestFromPatchProposal:
    def test_raises_when_not_accepted(self) -> None:
        proposal = {"status": "pending", "id": "PP-001"}
        with pytest.raises(ValueError, match="accepted"):
            build_change_request_from_patch_proposal(proposal)

    def test_builds_cr_with_correct_fields(self) -> None:
        proposal = {"status": "accepted", "id": "PP-001"}
        cr = build_change_request_from_patch_proposal(proposal)
        assert cr["type"] == "ChangeRequest"
        assert cr["status"] == "pending"
        assert cr["approval_status"] == "pending"
        assert cr["implementation_status"] == "pending"
        assert cr["source_patch_proposals"] == ["PP-001"]

    def test_handles_missing_id(self) -> None:
        proposal = {"status": "accepted"}
        cr = build_change_request_from_patch_proposal(proposal)
        assert cr["id"] == "CR-None"


class TestRenderChangeRequestMarkdown:
    def test_includes_frontmatter_and_title(self) -> None:
        cr = {"id": "CR-001", "type": "ChangeRequest", "status": "pending"}
        md = render_change_request_markdown(cr)
        assert "---" in md
        assert "# Change Request: CR-001" in md

    def test_includes_summary_when_present(self) -> None:
        cr = {"id": "CR-001", "type": "ChangeRequest", "summary": "Update groups"}
        md = render_change_request_markdown(cr)
        assert "Update groups" in md

    def test_omits_summary_when_missing(self) -> None:
        cr = {"id": "CR-001", "type": "ChangeRequest"}
        md = render_change_request_markdown(cr)
        # summary is not in the markdown when missing
        lines = md.splitlines()
        assert not any("summary" in line.lower() for line in lines)


class TestWriteChangeRequest:
    def test_creates_subdirectory(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        cr = {"id": "CR-001", "type": "ChangeRequest", "status": "pending"}
        path = write_change_request(cr, model_dir)
        assert path.exists()
        assert path.name == "CR-001.md"
        assert path.parent.name == "change-requests"


class TestApproveChangeRequest:
    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            approve_change_request(tmp_path, "CR-001")


class TestRejectChangeRequest:
    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            reject_change_request(tmp_path, "CR-001")

    def test_writes_rejection_without_reason(self, tmp_path: Path) -> None:
        cr_dir = tmp_path / "change-requests"
        cr_dir.mkdir()
        cr_path = cr_dir / "CR-001.md"
        cr_path.write_text(
            "---\nid: CR-001\ntype: ChangeRequest\nstatus: pending\n---\n# CR-001\n",
            encoding="utf-8",
        )
        reject_change_request(tmp_path, "CR-001")
        text = cr_path.read_text(encoding="utf-8")
        assert "rejected" in text.lower()
        assert "rejection_reason" not in text

    def test_writes_rejection_with_reason(self, tmp_path: Path) -> None:
        cr_dir = tmp_path / "change-requests"
        cr_dir.mkdir()
        cr_path = cr_dir / "CR-001.md"
        cr_path.write_text(
            "---\nid: CR-001\ntype: ChangeRequest\nstatus: pending\n---\n# CR-001\n",
            encoding="utf-8",
        )
        reject_change_request(tmp_path, "CR-001", reason="Needs more detail")
        text = cr_path.read_text(encoding="utf-8")
        assert "Needs more detail" in text

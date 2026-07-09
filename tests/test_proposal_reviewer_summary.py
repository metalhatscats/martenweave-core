"""Tests for the PatchProposal reviewer summary."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    write_patch_proposal,
)
from modelops_core.patching.proposal_reviewer_summary import (
    generate_reviewer_summary,
    reviewer_summary_to_dict,
)


def _build_minimal_repo(tmp_path: Path) -> Path:
    """Create a minimal repository with one active attribute."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "modelops.config.yaml").write_text(
        'schema_version: "1.0"\nname: Test Repository\n', encoding="utf-8"
    )

    model_dir = repo_root / "model"
    model_dir.mkdir()
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: active\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-DRAFT.md").write_text(
        "---\n"
        "id: ATTR-DRAFT\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Draft Attribute\n"
        "domain: DOMAIN-TEST\n"
        "description: Original draft description.\n"
        "---\n",
        encoding="utf-8",
    )

    return repo_root


def _build_valid_proposal() -> dict[str, object]:
    return build_patch_proposal(
        proposal_id="PP-TEST-001",
        operations=[
            PatchOperation(
                op="update_object",
                object_id="ATTR-DRAFT",
                object_type="Attribute",
                target_path="description",
                value="Updated draft description.",
            )
        ],
        affected_objects=["ATTR-DRAFT"],
        source_evidence="Test proposal",
        created_by="test",
    )


def _build_high_risk_proposal() -> dict[str, object]:
    return build_patch_proposal(
        proposal_id="PP-TEST-002",
        operations=[
            PatchOperation(
                op="update_object",
                object_id="ATTR-TEST",
                object_type="Attribute",
                target_path="business_owner",
                value="PERSON-NEW",
            )
        ],
        affected_objects=["ATTR-TEST"],
        source_evidence="Test proposal",
        created_by="test",
    )


def _build_invalid_proposal() -> dict[str, object]:
    return {
        "id": "pp-lowercase",
        "type": "PatchProposal",
        "status": "pending_review",
        "operations": [],
    }


class TestReviewerSummaryService:
    def test_valid_proposal_summary(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        proposal = _build_valid_proposal()

        summary = generate_reviewer_summary(proposal, repo_model_path=repo_root / "model")

        assert summary.proposal_id == "PP-TEST-001"
        assert summary.operations_count == 1
        assert summary.operations_by_type == {"update_object": 1}
        assert "ATTR-DRAFT" in summary.affected_object_ids
        assert summary.recommended_action in {"approve", "approve_with_review"}
        assert summary.validation_errors == []

    def test_high_risk_governance_change(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        proposal = _build_high_risk_proposal()

        summary = generate_reviewer_summary(proposal, repo_model_path=repo_root / "model")

        assert summary.risk_level == "high"
        assert summary.recommended_action == "inspect"
        assert any("governance" in reason.lower() for reason in summary.risk_reasons)
        assert any("active object" in note.lower() for note in summary.review_notes)

    def test_invalid_proposal_rejects(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        proposal = _build_invalid_proposal()

        summary = generate_reviewer_summary(proposal, repo_model_path=repo_root / "model")

        assert summary.recommended_action == "reject"
        assert any("PATCH_ID_INVALID" in error for error in summary.validation_errors)

    def test_files_touched_includes_existing_object(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        proposal = _build_valid_proposal()

        summary = generate_reviewer_summary(proposal, repo_model_path=repo_root / "model")

        assert any("ATTR-DRAFT.md" in path for path in summary.files_touched)

    def test_dict_contract(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        proposal = _build_valid_proposal()

        summary = generate_reviewer_summary(proposal, repo_model_path=repo_root / "model")
        data = reviewer_summary_to_dict(summary)

        expected_keys = {
            "proposal_id",
            "status",
            "validation_status",
            "operations_count",
            "operations_by_type",
            "affected_object_ids",
            "files_touched",
            "risk_level",
            "requires_approval",
            "risk_reasons",
            "validation_errors",
            "validation_warnings",
            "recommended_action",
            "review_notes",
        }
        assert set(data.keys()) == expected_keys


class TestReviewerSummaryCli:
    def test_proposal_show_renders_summary(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        proposal = _build_high_risk_proposal()
        write_patch_proposal(proposal, repo_root / "model")

        runner = CliRunner()
        result = runner.invoke(
            app, ["proposal", "show", "PP-TEST-002", "--repo", str(repo_root)]
        )
        assert result.exit_code == 0
        assert "Reviewer summary" in result.output
        assert "Recommended action" in result.output
        assert "inspect" in result.output
        assert "Risk reasons" in result.output

    def test_proposal_show_json_includes_summary(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        proposal = _build_valid_proposal()
        write_patch_proposal(proposal, repo_root / "model")

        runner = CliRunner()
        result = runner.invoke(
            app, ["proposal", "show", "PP-TEST-001", "--repo", str(repo_root), "--json"]
        )
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert data["id"] == "PP-TEST-001"
        assert "reviewer_summary" in data
        assert data["reviewer_summary"]["proposal_id"] == "PP-TEST-001"
        assert "recommended_action" in data["reviewer_summary"]

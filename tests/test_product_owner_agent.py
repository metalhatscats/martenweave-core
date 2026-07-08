"""Tests for the ProductOwner agentic loop."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.agents import ProductOwnerAgent, ProductOwnerInput
from modelops_core.ai.provider_adapter import AICandidateOutput, AIContextBundle
from modelops_core.cli import app
from modelops_core.index.sqlite_builder import build_index


def _build_minimal_repo(tmp_path: Path) -> Path:
    """Create a minimal model repository with one domain object."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    config_path = repo_root / "modelops.config.yaml"
    config_path.write_text("schema_version: \"1.0\"\nworkspace_name: Test\n", encoding="utf-8")

    model_dir = repo_root / "model"
    model_dir.mkdir()
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    build_index(repo_root, allow_invalid=True)
    return repo_root


class _ValidAdapter:
    """Test adapter that returns a valid update_object proposal."""

    def __init__(self, proposal_id: str = "PP-TEST-001") -> None:
        self.proposal_id = proposal_id
        self.calls: list[AIContextBundle] = []

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        self.calls.append(context)
        return [
            AICandidateOutput(
                proposal_id=self.proposal_id,
                title="Update test domain",
                operations=[
                    {
                        "op": "update_object",
                        "object_id": "DOMAIN-TEST",
                        "object_type": "MasterDataDomain",
                        "target_path": "name",
                        "after": "Updated Test Domain",
                        "reason": "Test proposal",
                    }
                ],
                affected_objects=["DOMAIN-TEST"],
                assumptions=["Test assumption"],
                human_checks=["Test check"],
                source_evidence="test note",
            )
        ]


class _InvalidAdapter:
    """Test adapter that always returns a structurally invalid proposal."""

    def __init__(self) -> None:
        self.calls: list[AIContextBundle] = []

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        self.calls.append(context)
        return [
            AICandidateOutput(
                proposal_id="pp-invalid-lowercase",
                title="Invalid proposal",
                operations=[
                    {
                        "op": "update_object",
                        "object_id": "DOMAIN-TEST",
                        "object_type": "MasterDataDomain",
                        "target_path": "name",
                        "after": "X",
                        "reason": "Invalid ID casing",
                    }
                ],
                affected_objects=["DOMAIN-TEST"],
                assumptions=["Invalid assumption"],
                human_checks=["Invalid check"],
            )
        ]


class TestProductOwnerAgent:
    def test_empty_input_returns_error(self) -> None:
        agent = ProductOwnerAgent(dry_run=True)
        result = agent.run(
            ProductOwnerInput(source_type="note", raw_text="   ", repo_root=None)
        )
        assert result.success is False
        assert result.iterations == 0
        assert result.error_message is not None

    def test_dry_run_does_not_write_files(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        adapter = _ValidAdapter()
        agent = ProductOwnerAgent(adapter=adapter, dry_run=True)

        before = list((repo_root / "model").rglob("*"))
        result = agent.run(
            ProductOwnerInput(
                source_type="note",
                raw_text="Update the test domain name",
                repo_root=repo_root,
            )
        )
        after = list((repo_root / "model").rglob("*"))

        assert result.success is True
        assert result.proposal_id == "PP-TEST-001"
        assert result.proposal_path is None
        assert result.change_request_id is None
        assert result.notification_event_ids == []
        assert before == after

    def test_successful_loop_writes_proposal(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        adapter = _ValidAdapter()
        agent = ProductOwnerAgent(adapter=adapter, dry_run=False)

        result = agent.run(
            ProductOwnerInput(
                source_type="note",
                raw_text="Update the test domain name",
                repo_root=repo_root,
            )
        )

        assert result.success is True
        assert result.iterations == 1
        assert result.proposal_id == "PP-TEST-001"
        assert result.proposal_path is not None
        assert result.proposal_path.exists()
        assert result.validation_status == "valid"
        assert result.impact_summary.get("affected_object_count") == 0

    def test_max_iterations_stops_gracefully(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        adapter = _InvalidAdapter()
        agent = ProductOwnerAgent(adapter=adapter, dry_run=True, max_iterations=2)

        result = agent.run(
            ProductOwnerInput(
                source_type="note",
                raw_text="Update missing object",
                repo_root=repo_root,
            )
        )

        assert result.success is False
        assert result.iterations == 2
        assert adapter.calls
        assert result.validation_status == "invalid"

    def test_refinement_note_includes_validation_errors(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        adapter = _InvalidAdapter()
        agent = ProductOwnerAgent(adapter=adapter, dry_run=True, max_iterations=2)

        agent.run(
            ProductOwnerInput(
                source_type="note",
                raw_text="Update missing object",
                repo_root=repo_root,
            )
        )

        assert len(adapter.calls) == 2
        second_note = adapter.calls[1].note
        assert "Refinement attempt 1" in second_note
        assert "pp-invalid-lowercase" in second_note or "PATCH_ID_INVALID" in second_note

    def test_change_request_source_creates_cr(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        adapter = _ValidAdapter()
        agent = ProductOwnerAgent(adapter=adapter, dry_run=False)

        cr_text = (
            "---\n"
            "id: CR-TEST\n"
            "type: ChangeRequest\n"
            "status: pending\n"
            "name: Test CR\n"
            "reason: Update domain\n"
            "requested_change: Change the name\n"
            "---\n"
        )
        result = agent.run(
            ProductOwnerInput(
                source_type="change_request",
                raw_text=cr_text,
                source_id="CR-TEST",
                repo_root=repo_root,
            )
        )

        assert result.success is True
        assert result.change_request_id is not None
        assert result.change_request_path is not None
        assert result.change_request_path.exists()
        assert result.proposal_id in result.change_request_path.read_text(encoding="utf-8")

    def test_issue_source_strips_frontmatter(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        adapter = _ValidAdapter()
        agent = ProductOwnerAgent(adapter=adapter, dry_run=True)

        issue_text = (
            "---\n"
            "title: Product request\n"
            "labels: [enhancement]\n"
            "---\n\n"
            "Please update the test domain name."
        )
        result = agent.run(
            ProductOwnerInput(
                source_type="issue",
                raw_text=issue_text,
                source_id="ISSUE-1",
                repo_root=repo_root,
            )
        )

        assert result.success is True
        assert adapter.calls
        assert "Please update the test domain name" in adapter.calls[0].note
        assert "title: Product request" not in adapter.calls[0].note


class TestProductOwnerCli:
    def test_cli_dry_run(self, sample_repo: Path) -> None:
        runner = CliRunner()
        note_file = sample_repo / "note.md"
        note_file.write_text("Update CUSTOMER GROUP", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "agent",
                "product-owner",
                str(note_file),
                "--repo",
                str(sample_repo),
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "ProductOwner loop completed" in result.output
        assert "PP-SCAFFOLD-001" in result.output

    def test_cli_missing_repo(self, tmp_path: Path) -> None:
        runner = CliRunner()
        note_file = tmp_path / "note.md"
        note_file.write_text("Update something", encoding="utf-8")

        result = runner.invoke(
            app,
            ["agent", "product-owner", str(note_file), "--repo", str(tmp_path)],
        )

        assert result.exit_code == 1
        assert "No modelops.config.yaml" in result.output

    def test_cli_json_output(self, sample_repo: Path) -> None:
        runner = CliRunner()
        note_file = sample_repo / "note.md"
        note_file.write_text("Update CUSTOMER GROUP", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "agent",
                "product-owner",
                str(note_file),
                "--repo",
                str(sample_repo),
                "--dry-run",
                "--json",
            ],
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"proposal_id"' in result.output

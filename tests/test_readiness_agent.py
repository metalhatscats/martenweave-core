"""Tests for the Readiness agentic loop."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.agents import ReadinessAgent, ReadinessInput
from modelops_core.cli import app
from modelops_core.index.sqlite_builder import build_index


def _build_minimal_repo(tmp_path: Path, with_decision: bool = False) -> Path:
    """Create a minimal model repository with one domain object."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    config_path = repo_root / "modelops.config.yaml"
    config_path.write_text(
        'schema_version: "1.0"\nname: Test Repository\n', encoding="utf-8"
    )

    model_dir = repo_root / "model"
    model_dir.mkdir()
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    if with_decision:
        (model_dir / "DEC-TEST.md").write_text(
            "---\n"
            "id: DEC-TEST\n"
            "type: Decision\n"
            "status: active\n"
            "name: Test Decision\n"
            "evidence: Workshop notes\n"
            "---\n",
            encoding="utf-8",
        )

    build_index(repo_root, allow_invalid=True)
    return repo_root


class TestReadinessAgent:
    def test_clean_repo_has_no_validation_or_ownership_blockers(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        agent = ReadinessAgent(dry_run=True)
        result = agent.run(ReadinessInput(repo_root=repo_root, profile="pilot"))

        # A clean minimal repo should not have validation errors or ownership gaps.
        assert "validation_errors" not in result.failed_gates
        assert "active_object_missing_owner" not in result.failed_gates
        # Scorecard may still report zero-coverage-pass because there are no SAP endpoints.
        assert result.gate_count == 7

    def test_dry_run_does_not_write_files(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)

        # Add an active object without owner to create a blocker
        model_dir = repo_root / "model"
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
        build_index(repo_root, allow_invalid=True)

        before = list(model_dir.rglob("*"))
        agent = ReadinessAgent(dry_run=True)
        result = agent.run(ReadinessInput(repo_root=repo_root, profile="pilot"))
        after = list(model_dir.rglob("*"))

        assert result.ready is False
        assert "active_object_missing_owner" in result.failed_gates
        assert before == after

    def test_writes_issues_when_blockers_exist(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)

        model_dir = repo_root / "model"
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
        build_index(repo_root, allow_invalid=True)

        agent = ReadinessAgent(dry_run=False)
        result = agent.run(ReadinessInput(repo_root=repo_root, profile="pilot"))

        assert result.ready is False
        assert len(result.issues_created) == 1
        assert all(i.startswith("ISS-READINESS-") for i in result.issues_created)
        issue_paths = [model_dir / "issues" / f"{i}.md" for i in result.issues_created]
        assert all(p.exists() for p in issue_paths)
        assert any("ATTR-TEST" in p.read_text(encoding="utf-8") for p in issue_paths)
        assert result.draft_issue_path is not None
        assert result.draft_issue_path.exists()

    def test_detects_invalid_open_proposal(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        model_dir = repo_root / "model"
        proposals_dir = model_dir / "patch-proposals"
        proposals_dir.mkdir(parents=True, exist_ok=True)
        (proposals_dir / "PP-BAD.md").write_text(
            "---\n"
            "id: pp-lowercase\n"
            "type: PatchProposal\n"
            "status: pending_review\n"
            "validation_status: invalid\n"
            "operations: []\n"
            "---\n",
            encoding="utf-8",
        )
        build_index(repo_root, allow_invalid=True)

        agent = ReadinessAgent(dry_run=True)
        result = agent.run(ReadinessInput(repo_root=repo_root, profile="pilot"))

        assert result.ready is False
        assert "invalid_open_proposal" in result.failed_gates

    def test_scorecard_zero_coverage_no_longer_reports_pass(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        build_index(repo_root, allow_invalid=True)

        agent = ReadinessAgent(dry_run=True)
        result = agent.run(ReadinessInput(repo_root=repo_root, profile="pilot"))

        # The minimal repo has no Decision objects; evidence_coverage is 0.0 and
        # should be reported as fail, so the readiness safety gate must not trigger.
        assert not any(
            b.gate == "scorecard_zero_coverage_pass" and "evidence_coverage" in b.message
            for b in result.blockers
        )


class TestReadinessCli:
    def test_cli_dry_run_ready_repo(self, sample_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["agent", "readiness", "--repo", str(sample_repo), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Gates checked:" in result.output
        assert "ready" in result.output.lower()

    def test_cli_dry_run_not_ready(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        model_dir = repo_root / "model"
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
        build_index(repo_root, allow_invalid=True)

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["agent", "readiness", "--repo", str(repo_root), "--dry-run"],
        )
        assert result.exit_code == 1  # not ready
        assert "Gates checked:" in result.output
        assert "active_object_missing_owner" in result.output

    def test_cli_json_output(self, sample_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["agent", "readiness", "--repo", str(sample_repo), "--dry-run", "--json"],
        )
        assert '"ready"' in result.output
        assert '"gate_count"' in result.output
        assert '"failed_gates"' in result.output

"""Tests for the top-level `readiness` CLI command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.index.sqlite_builder import build_index


def _build_minimal_repo(
    tmp_path: Path,
    *,
    with_field_endpoint: bool = False,
    with_validation_rule: bool = False,
) -> Path:
    """Create a minimal model repository.

    The active attribute always has an owner so that ownership gates do not
    interfere with coverage-focused assertions. All governance references point
    to real Person/EntityContext objects to avoid validation errors.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    config_path = repo_root / "modelops.config.yaml"
    config_path.write_text(
        'schema_version: "1.0"\nname: Test Repository\n', encoding="utf-8"
    )

    model_dir = repo_root / "model"
    model_dir.mkdir()
    (model_dir / "PERSON-OWNER.md").write_text(
        "---\n"
        "id: PERSON-OWNER\n"
        "type: Person\n"
        "status: active\n"
        "name: Test Owner\n"
        "---\n",
        encoding="utf-8",
    )
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
        "business_owner: PERSON-OWNER\n"
        "---\n",
        encoding="utf-8",
    )

    if with_field_endpoint:
        (model_dir / "ENTITY-CTX.md").write_text(
            "---\n"
            "id: ENTITY-CTX\n"
            "type: EntityContext\n"
            "status: active\n"
            "name: Test Context\n"
            "domain: DOMAIN-TEST\n"
            "business_owner: PERSON-OWNER\n"
            "---\n",
            encoding="utf-8",
        )
        (model_dir / "FEP-TEST.md").write_text(
            "---\n"
            "id: FEP-TEST\n"
            "type: FieldEndpoint\n"
            "status: active\n"
            "name: Test Field\n"
            "attribute: ATTR-TEST\n"
            "endpoint_type: sap_table_field\n"
            "sap_table: TEST\n"
            "sap_field: FIELD\n"
            "entity_context: ENTITY-CTX\n"
            "business_owner: PERSON-OWNER\n"
            "---\n",
            encoding="utf-8",
        )

    if with_validation_rule:
        (model_dir / "VR-TEST.md").write_text(
            "---\n"
            "id: VR-TEST\n"
            "type: ValidationRule\n"
            "status: active\n"
            "name: Test Rule\n"
            "attribute: ATTR-TEST\n"
            "business_owner: PERSON-OWNER\n"
            "---\n",
            encoding="utf-8",
        )

    build_index(repo_root, allow_invalid=True)
    return repo_root


class TestReadinessCommand:
    def test_top_level_command_ready_repo(self, sample_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["readiness", "--repo", str(sample_repo), "--profile", "demo", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Gates checked:" in result.output
        assert "ready" in result.output.lower()

    def test_top_level_command_json_output(self, sample_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "readiness",
                "--repo",
                str(sample_repo),
                "--profile",
                "demo",
                "--dry-run",
                "--json",
            ],
        )
        assert result.exit_code == 0
        assert '"ready"' in result.output
        assert '"gate_count"' in result.output
        assert '"failed_gates"' in result.output
        assert '"profile"' in result.output

    def test_profile_demo_allows_low_validation_coverage(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["readiness", "--repo", str(repo_root), "--profile", "demo", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "missing_validation_coverage" not in result.output

    def test_profile_pilot_blocks_missing_validation_coverage(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path, with_field_endpoint=True)

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["readiness", "--repo", str(repo_root), "--profile", "pilot", "--dry-run"],
        )
        assert result.exit_code == 1
        assert "missing_validation_coverage" in result.output

    def test_profile_pilot_passes_with_validation_rule(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(
            tmp_path, with_field_endpoint=True, with_validation_rule=True
        )

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "readiness",
                "--repo",
                str(repo_root),
                "--profile",
                "pilot",
                "--dry-run",
                "--json",
            ],
        )
        assert result.exit_code == 0
        assert '"ready": true' in result.output

    def test_profile_release_is_strict(self, tmp_path: Path) -> None:
        # No validation rules in a repo with an active attribute -> 0% coverage,
        # which satisfies demo/pilot thresholds but fails the release threshold.
        repo_root = _build_minimal_repo(tmp_path, with_field_endpoint=True)

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["readiness", "--repo", str(repo_root), "--profile", "release", "--dry-run"],
        )
        assert result.exit_code == 1
        assert "missing_validation_coverage" in result.output

    def test_missing_config_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["readiness", "--repo", str(tmp_path), "--dry-run"],
        )
        assert result.exit_code == 1
        assert "No modelops.config.yaml found" in result.output

    def test_agent_subcommand_still_works(self, sample_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "agent",
                "readiness",
                "--repo",
                str(sample_repo),
                "--profile",
                "demo",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Gates checked:" in result.output

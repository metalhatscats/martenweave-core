"""Tests for schema versioning and migration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.repository.parser import rewrite_frontmatter
from modelops_core.schemas.migration import (
    MIGRATIONS,
    Migration,
    migrate_object,
    needs_migration,
    preview_migration,
    register_migration,
)
from modelops_core.schemas.versioning import (
    CURRENT_SCHEMA_VERSION,
    DEPRECATED_SCHEMA_VERSIONS,
    UNSUPPORTED_SCHEMA_VERSIONS,
    validate_object_schema_version,
    validate_repo_schema_version,
)
from modelops_core.validation.pipeline import _check_schema_version
from modelops_core.validation.result import ValidationSeverity

# ---------------------------------------------------------------------------
# validate_object_schema_version
# ---------------------------------------------------------------------------


class TestValidateObjectSchemaVersion:
    def test_missing_schema_version_info(self) -> None:
        fm = {"id": "TEST-001", "type": "Attribute"}
        issues = validate_object_schema_version(fm, "test.md")
        assert len(issues) == 1
        assert issues[0].code == "SCHEMA_VERSION_MISSING"
        assert issues[0].severity == "INFO"

    def test_supported_schema_version_no_issue(self) -> None:
        fm = {"id": "TEST-001", "schema_version": CURRENT_SCHEMA_VERSION}
        issues = validate_object_schema_version(fm, "test.md")
        assert not issues

    def test_unsupported_schema_version_error(self) -> None:
        UNSUPPORTED_SCHEMA_VERSIONS.add("0.0")
        fm = {"id": "TEST-001", "schema_version": "0.0"}
        issues = validate_object_schema_version(fm, "test.md")
        UNSUPPORTED_SCHEMA_VERSIONS.discard("0.0")
        assert len(issues) == 1
        assert issues[0].code == "SCHEMA_VERSION_UNSUPPORTED"
        assert issues[0].severity == "ERROR"

    def test_deprecated_schema_version_warning(self) -> None:
        DEPRECATED_SCHEMA_VERSIONS.add("0.9")
        fm = {"id": "TEST-001", "schema_version": "0.9"}
        issues = validate_object_schema_version(fm, "test.md")
        DEPRECATED_SCHEMA_VERSIONS.discard("0.9")
        assert len(issues) == 1
        assert issues[0].code == "SCHEMA_VERSION_DEPRECATED"
        assert issues[0].severity == "WARNING"

    def test_unknown_schema_version_warning(self) -> None:
        fm = {"id": "TEST-001", "schema_version": "99.9"}
        issues = validate_object_schema_version(fm, "test.md")
        assert len(issues) == 1
        assert issues[0].code == "SCHEMA_VERSION_UNKNOWN"
        assert issues[0].severity == "WARNING"

    def test_none_frontmatter(self) -> None:
        assert validate_object_schema_version(None, "test.md") == []


# ---------------------------------------------------------------------------
# validate_repo_schema_version
# ---------------------------------------------------------------------------


class TestValidateRepoSchemaVersion:
    def test_missing_repo_schema_version_info(self) -> None:
        issues = validate_repo_schema_version({"name": "Test"})
        assert len(issues) == 1
        assert issues[0].code == "REPO_SCHEMA_VERSION_MISSING"
        assert issues[0].severity == "INFO"

    def test_supported_repo_schema_version(self) -> None:
        issues = validate_repo_schema_version(
            {"name": "Test", "schema_version": CURRENT_SCHEMA_VERSION}
        )
        assert not issues

    def test_none_config(self) -> None:
        assert validate_repo_schema_version(None) == []


# ---------------------------------------------------------------------------
# _check_schema_version (pipeline integration)
# ---------------------------------------------------------------------------


class TestCheckSchemaVersionPipeline:
    def test_pipeline_missing_schema_version(self) -> None:
        fm = {"id": "TEST-001", "type": "Attribute"}
        results = _check_schema_version(fm, "test.md")
        assert any(r.code == "SCHEMA_VERSION_MISSING" for r in results)
        assert all(r.severity == ValidationSeverity.INFO for r in results)

    def test_pipeline_current_version_no_issue(self) -> None:
        fm = {"id": "TEST-001", "schema_version": CURRENT_SCHEMA_VERSION}
        results = _check_schema_version(fm, "test.md")
        assert not results


# ---------------------------------------------------------------------------
# needs_migration
# ---------------------------------------------------------------------------


class TestNeedsMigration:
    def test_true_when_none(self) -> None:
        assert needs_migration(None) is False

    def test_true_when_missing(self) -> None:
        assert needs_migration({"id": "TEST"}) is True

    def test_true_when_old(self) -> None:
        assert needs_migration({"id": "TEST", "schema_version": "0.9"}) is True

    def test_false_when_current(self) -> None:
        assert needs_migration({"id": "TEST", "schema_version": CURRENT_SCHEMA_VERSION}) is False


# ---------------------------------------------------------------------------
# migrate_object
# ---------------------------------------------------------------------------


class TestMigrateObject:
    def test_returns_none_for_none(self) -> None:
        assert migrate_object(None) is None

    def test_sets_current_when_no_version(self) -> None:
        fm = {"id": "TEST"}
        result = migrate_object(fm)
        assert result is not None
        assert result["schema_version"] == CURRENT_SCHEMA_VERSION

    def test_sets_current_when_already_current(self) -> None:
        fm = {"id": "TEST", "schema_version": CURRENT_SCHEMA_VERSION}
        result = migrate_object(fm)
        assert result is not None
        assert result["schema_version"] == CURRENT_SCHEMA_VERSION

    def test_applies_registered_migration(self) -> None:
        register_migration(
            Migration(
                from_version="0.9",
                to_version=CURRENT_SCHEMA_VERSION,
                description="test migration",
                transform=lambda d: d.update({"migrated": True}),
            )
        )
        fm = {"id": "TEST", "schema_version": "0.9"}
        result = migrate_object(fm)
        # Clean up
        MIGRATIONS.pop()
        assert result is not None
        assert result["schema_version"] == CURRENT_SCHEMA_VERSION
        assert result["migrated"] is True

    def test_does_not_mutate_original(self) -> None:
        fm = {"id": "TEST", "schema_version": "0.9"}
        original = dict(fm)
        migrate_object(fm)
        assert fm == original


# ---------------------------------------------------------------------------
# preview_migration
# ---------------------------------------------------------------------------


class TestPreviewMigration:
    def test_preview_no_mutation(self) -> None:
        fm = {"id": "TEST", "schema_version": "0.9"}
        preview = preview_migration(fm)
        assert preview.get("schema_version") == CURRENT_SCHEMA_VERSION
        assert fm["schema_version"] == "0.9"


# ---------------------------------------------------------------------------
# rewrite_frontmatter
# ---------------------------------------------------------------------------


class TestRewriteFrontmatter:
    def test_rewrites_md_file(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        path.write_text(
            "---\nid: TEST\nstatus: draft\n---\n\n# Test\n",
            encoding="utf-8",
        )
        rewrite_frontmatter(path, {"id": "TEST", "status": "active", "schema_version": "1.0"})
        text = path.read_text(encoding="utf-8")
        assert "schema_version:" in text
        assert "# Test" in text

    def test_rewrites_yaml_file(self, tmp_path: Path) -> None:
        path = tmp_path / "test.yaml"
        path.write_text("id: TEST\nstatus: draft\n", encoding="utf-8")
        rewrite_frontmatter(path, {"id": "TEST", "status": "active"})
        text = path.read_text(encoding="utf-8")
        assert "id: TEST" in text
        assert "status: active" in text


# ---------------------------------------------------------------------------
# CLI migrate --json
# ---------------------------------------------------------------------------

runner = CliRunner()


class TestMigrateCliJson:
    @pytest.mark.parametrize("fixture_name", ["schema-v0", "schema-v0_9"])
    def test_historical_fixture_migration_preview(self, fixture_name: str) -> None:
        fixture = Path(__file__).parent / "fixtures" / "repositories" / fixture_name
        result = runner.invoke(app, ["migrate", "--repo", str(fixture), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["migrated_count"] == 1

    def test_migrate_json_empty_model(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        model_dir = repo / "model"
        model_dir.mkdir()
        config = repo / "modelops.config.yaml"
        config.write_text("schema_version: 0.1\n", encoding="utf-8")

        result = runner.invoke(app, ["migrate", "--repo", str(repo), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["migrated_count"] == 0
        assert data["skipped_count"] == 0
        assert data["migrated_files"] == []
        assert "schema_version" in data

    def test_migrate_json_no_model_path(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        result = runner.invoke(app, ["migrate", "--repo", str(repo), "--json"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def test_migrate_dry_run_json_with_old_schema(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        model_dir = repo / "model"
        model_dir.mkdir()
        config = repo / "modelops.config.yaml"
        config.write_text("schema_version: 0.1\n", encoding="utf-8")

        obj = model_dir / "DOMAIN-TEST.md"
        frontmatter = (
            "---\n"
            "id: DOMAIN-TEST\n"
            "type: MasterDataDomain\n"
            "status: draft\n"
            "schema_version: 0.1\n"
            "---\n"
        )
        obj.write_text(frontmatter, encoding="utf-8")

        result = runner.invoke(app, ["migrate", "--repo", str(repo), "--dry-run", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["migrated_count"] >= 1
        assert len(data["migrated_files"]) >= 1
        assert data["migrated_files"][0]["file"] == "DOMAIN-TEST.md"
        assert "old_version" in data["migrated_files"][0]
        assert "new_version" in data["migrated_files"][0]
        # Verify file was NOT changed in dry-run
        text = obj.read_text(encoding="utf-8")
        assert "schema_version: 0.1" in text

    def test_migrate_defaults_to_preview(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        obj = model_dir / "DOMAIN-TEST.md"
        obj.write_text(
            "---\n"
            "id: DOMAIN-TEST\n"
            "type: MasterDataDomain\n"
            "status: draft\n"
            "schema_version: 0.1\n"
            "---\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["migrate", "--repo", str(repo), "--json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["dry_run"] is True
        assert "schema_version: 0.1" in obj.read_text(encoding="utf-8")

    def test_migrate_apply_preserves_unknown_metadata_and_writes_receipt(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        obj = model_dir / "DOMAIN-TEST.md"
        obj.write_text(
            "---\n"
            "id: DOMAIN-TEST\n"
            "type: MasterDataDomain\n"
            "status: draft\n"
            "name: Test\n"
            "schema_version: 0.1\n"
            "custom_field: retain-me\n"
            "---\n\n# Body\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["migrate", "--repo", str(repo), "--apply", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["receipt"]
        assert (repo / data["receipt"]).exists()
        text = obj.read_text(encoding="utf-8")
        assert "schema_version: '1.0'" in text
        assert "custom_field: retain-me" in text
        assert "# Body" in text

    def test_migrate_rejects_future_version_without_writing(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        obj = model_dir / "DOMAIN-TEST.md"
        original = (
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\n"
            "schema_version: 99.0\n---\n"
        )
        obj.write_text(original, encoding="utf-8")
        result = runner.invoke(app, ["migrate", "--repo", str(repo), "--apply", "--json"])
        assert result.exit_code == 1
        assert json.loads(result.output)["unsupported_files"] == ["model/DOMAIN-TEST.md"]
        assert obj.read_text(encoding="utf-8") == original

    def test_migrate_rolls_back_when_index_rebuild_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        obj = model_dir / "DOMAIN-TEST.md"
        original = (
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n"
            "schema_version: 0.1\nunknown: preserved\n---\n\n# Body\n"
        )
        obj.write_text(original, encoding="utf-8")
        monkeypatch.setattr(
            "modelops_core.commands.migrate_audit._build_index",
            lambda **_: (_ for _ in ()).throw(OSError("boom")),
        )

        result = runner.invoke(app, ["migrate", "--repo", str(repo), "--apply", "--json"])
        assert result.exit_code == 1
        assert json.loads(result.output)["rolled_back"] is True
        assert obj.read_text(encoding="utf-8") == original

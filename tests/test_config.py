"""Tests for config.py, paths.py, and error classes (issue #187)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from modelops_core.config import (
    RepoConfig,
    ResourceLimits,
    Settings,
    load_repo_config,
    load_resource_limits,
    load_settings,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.errors import (
    IndexError,
    ModelOpsError,
    PatchError,
    PathTraversalError,
    RepositoryError,
    ResourceLimitExceeded,
    ValidationError,
)
from modelops_core.paths import resolve_allowed_path


class TestRepoConfig:
    def test_defaults(self) -> None:
        config = RepoConfig()
        assert config.name == "Untitled Repository"
        assert config.description == ""
        assert config.version == "1.0.0"
        assert config.schema_version == "1.0"
        assert config.model_path == "model"
        assert config.generated_path == "generated"
        assert config.data_path == "data"
        assert config.enabled_domain_packs == []
        assert isinstance(config.resource_limits, ResourceLimits)

    def test_from_dict(self) -> None:
        config = RepoConfig(
            name="Test Repo",
            description="A test repository",
            version="2.0.0",
            schema_version="1.0",
            model_path="custom_model",
            generated_path="custom_generated",
            data_path="custom_data",
            enabled_domain_packs=["sap", "generic"],
        )
        assert config.name == "Test Repo"
        assert config.description == "A test repository"
        assert config.version == "2.0.0"
        assert config.model_path == "custom_model"
        assert config.generated_path == "custom_generated"
        assert config.data_path == "custom_data"
        assert config.enabled_domain_packs == ["sap", "generic"]


class TestResourceLimits:
    def test_defaults(self) -> None:
        limits = ResourceLimits()
        assert limits.max_file_size_bytes == 50 * 1024 * 1024
        assert limits.max_profile_rows == 500_000
        assert limits.max_profile_columns == 1_000
        assert limits.max_trace_depth == 5
        assert limits.max_index_objects == 10_000
        assert limits.max_export_objects == 10_000
        assert limits.max_import_rows == 100_000
        assert limits.max_context_objects == 50
        assert limits.max_context_relationships == 100
        assert limits.max_response_size_bytes == 10 * 1024 * 1024
        assert limits.profile_sample_interval is None

    def test_custom_values(self) -> None:
        limits = ResourceLimits(
            max_file_size_bytes=1024,
            max_profile_rows=100,
            max_trace_depth=3,
            profile_sample_interval=10,
        )
        assert limits.max_file_size_bytes == 1024
        assert limits.max_profile_rows == 100
        assert limits.max_trace_depth == 3
        assert limits.profile_sample_interval == 10
        # Unchanged defaults
        assert limits.max_index_objects == 10_000


class TestSettings:
    def test_defaults(self) -> None:
        settings = Settings()
        assert settings.environment == "local"
        assert settings.log_level == "INFO"

    def test_is_dev(self) -> None:
        assert Settings(environment="dev").is_dev() is True
        assert Settings(environment="production").is_dev() is False

    def test_is_production(self) -> None:
        assert Settings(environment="production").is_production() is True
        assert Settings(environment="local").is_production() is False


class TestLoadSettings:
    def test_default_without_env(self, monkeypatch) -> None:
        monkeypatch.delenv("MODELOPS_ENVIRONMENT", raising=False)
        monkeypatch.delenv("MODELOPS_LOG_LEVEL", raising=False)
        settings = load_settings()
        assert settings.environment == "local"
        assert settings.log_level == "INFO"

    def test_from_env_vars(self, monkeypatch) -> None:
        monkeypatch.setenv("MODELOPS_ENVIRONMENT", "production")
        monkeypatch.setenv("MODELOPS_LOG_LEVEL", "DEBUG")
        settings = load_settings()
        assert settings.environment == "production"
        assert settings.log_level == "DEBUG"


class TestLoadRepoConfig:
    def test_valid_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yaml"
        config_file.write_text(
            yaml.safe_dump(
                {
                    "name": "Test Repo",
                    "version": "2.0.0",
                    "resource_limits": {"max_index_objects": 42},
                }
            ),
            encoding="utf-8",
        )
        config = load_repo_config(tmp_path)
        assert config is not None
        assert config.name == "Test Repo"
        assert config.version == "2.0.0"
        assert config.resource_limits.max_index_objects == 42

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert load_repo_config(tmp_path) is None

    def test_invalid_yaml_returns_none(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yaml"
        config_file.write_text("not: [valid yaml: :", encoding="utf-8")
        assert load_repo_config(tmp_path) is None

    def test_non_dict_yaml_returns_none(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yaml"
        config_file.write_text("just_a_string", encoding="utf-8")
        assert load_repo_config(tmp_path) is None

    def test_dot_yml_fallback(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yml"
        config_file.write_text(
            yaml.safe_dump({"name": "YML Repo"}),
            encoding="utf-8",
        )
        config = load_repo_config(tmp_path)
        assert config is not None
        assert config.name == "YML Repo"

    def test_yaml_takes_precedence_over_yml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "modelops.config.yaml"
        yml_file = tmp_path / "modelops.config.yml"
        yaml_file.write_text(
            yaml.safe_dump({"name": "YAML Repo"}),
            encoding="utf-8",
        )
        yml_file.write_text(
            yaml.safe_dump({"name": "YML Repo"}),
            encoding="utf-8",
        )
        config = load_repo_config(tmp_path)
        assert config is not None
        assert config.name == "YAML Repo"

    def test_workspace_name_used_when_name_missing(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yaml"
        config_file.write_text(
            yaml.safe_dump({"workspace_name": "Customer BP Example"}),
            encoding="utf-8",
        )
        config = load_repo_config(tmp_path)
        assert config is not None
        assert config.name == "Customer BP Example"

    def test_name_takes_precedence_over_workspace_name(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yaml"
        config_file.write_text(
            yaml.safe_dump({"name": "Official Name", "workspace_name": "Legacy Name"}),
            encoding="utf-8",
        )
        config = load_repo_config(tmp_path)
        assert config is not None
        assert config.name == "Official Name"


class TestResolvePaths:
    def test_resolve_model_path_with_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yaml"
        config_file.write_text(
            yaml.safe_dump({"model_path": "custom_model"}),
            encoding="utf-8",
        )
        path = resolve_model_path(tmp_path)
        assert path == tmp_path / "custom_model"

    def test_resolve_model_path_without_config(self, tmp_path: Path) -> None:
        path = resolve_model_path(tmp_path)
        assert path == tmp_path / "model"

    def test_resolve_generated_path_with_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yaml"
        config_file.write_text(
            yaml.safe_dump({"generated_path": "custom_generated"}),
            encoding="utf-8",
        )
        path = resolve_generated_path(tmp_path)
        assert path == tmp_path / "custom_generated"

    def test_resolve_generated_path_without_config(self, tmp_path: Path) -> None:
        path = resolve_generated_path(tmp_path)
        assert path == tmp_path / "generated"


class TestLoadResourceLimits:
    def test_with_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "modelops.config.yaml"
        config_file.write_text(
            yaml.safe_dump({"resource_limits": {"max_trace_depth": 7}}),
            encoding="utf-8",
        )
        limits = load_resource_limits(tmp_path)
        assert limits.max_trace_depth == 7
        assert limits.max_index_objects == 10_000

    def test_without_config_uses_defaults(self, tmp_path: Path) -> None:
        limits = load_resource_limits(tmp_path)
        assert limits.max_file_size_bytes == 50 * 1024 * 1024


class TestResolveAllowedPath:
    def test_within_allowed_root(self, tmp_path: Path) -> None:
        target = tmp_path / "subdir" / "file.txt"
        target.parent.mkdir(parents=True)
        target.write_text("hello")
        result = resolve_allowed_path(target, allowed_roots=[tmp_path])
        assert result == target.resolve()

    def test_outside_allowed_root_raises(self, tmp_path: Path) -> None:
        other = tmp_path / ".." / "other"
        with pytest.raises(PathTraversalError):
            resolve_allowed_path(other, allowed_roots=[tmp_path / "safe"])

    def test_default_roots_includes_cwd_and_tmp(self) -> None:
        # Any path under cwd should succeed
        result = resolve_allowed_path(".")
        assert result == Path.cwd().resolve()

    def test_custom_allowed_roots(self, tmp_path: Path) -> None:
        root_a = tmp_path / "a"
        root_b = tmp_path / "b"
        root_a.mkdir()
        root_b.mkdir()
        target = root_b / "file.txt"
        target.write_text("hello")
        result = resolve_allowed_path(target, allowed_roots=[root_a, root_b])
        assert result == target.resolve()


class TestExceptions:
    def test_validation_error_is_model_ops_error(self) -> None:
        exc = ValidationError("bad")
        assert isinstance(exc, ModelOpsError)

    def test_patch_error_is_model_ops_error(self) -> None:
        exc = PatchError("bad")
        assert isinstance(exc, ModelOpsError)

    def test_repository_error_is_model_ops_error(self) -> None:
        exc = RepositoryError("bad")
        assert isinstance(exc, ModelOpsError)

    def test_index_error_is_model_ops_error(self) -> None:
        exc = IndexError("bad")
        assert isinstance(exc, ModelOpsError)

    def test_path_traversal_error_is_model_ops_error(self) -> None:
        exc = PathTraversalError("bad")
        assert isinstance(exc, ModelOpsError)

    def test_resource_limit_exceeded_stores_fields(self) -> None:
        exc = ResourceLimitExceeded("max_index_objects", "too many")
        assert exc.resource == "max_index_objects"
        assert exc.message == "too many"
        assert isinstance(exc, ModelOpsError)
        assert str(exc) == "too many"

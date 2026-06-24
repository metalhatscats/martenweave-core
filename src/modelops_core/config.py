"""Configuration loader for Martenweave Core."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ResourceLimits(BaseModel):
    """Configurable runtime resource limits for local-first operation.

    Defaults are chosen for a normal developer laptop (8–16 GB RAM).
    All limits can be overridden in ``modelops.config.yaml``.
    """

    max_file_size_bytes: int = Field(
        default=50 * 1024 * 1024, description="Maximum dataset file size (50 MB)"
    )
    max_profile_rows: int = Field(default=500_000, description="Maximum rows to profile per file")
    max_profile_columns: int = Field(
        default=1_000, description="Maximum columns to profile per file"
    )
    max_trace_depth: int = Field(default=5, description="Maximum graph traversal depth")
    max_index_objects: int = Field(
        default=10_000, description="Maximum canonical objects in a single index build"
    )
    max_export_objects: int = Field(default=10_000, description="Maximum objects per export type")
    max_import_rows: int = Field(
        default=100_000, description="Maximum rows to import per spreadsheet sheet"
    )
    max_context_objects: int = Field(
        default=50, description="Maximum objects in an AI context bundle"
    )
    max_context_relationships: int = Field(
        default=100, description="Maximum relationships in an AI context bundle"
    )
    max_response_size_bytes: int = Field(
        default=10 * 1024 * 1024, description="Maximum CLI/API response payload (10 MB)"
    )
    profile_sample_interval: int | None = Field(
        default=None,
        description=("If set, profile every Nth row for large files instead of a full scan."),
    )


class RepoConfig(BaseModel):
    """Repository-level configuration from modelops.config.yaml."""

    name: str = "Untitled Repository"
    description: str = ""
    version: str = "1.0.0"
    schema_version: str = "1.0"
    model_path: str = "model"
    generated_path: str = "generated"
    data_path: str = "data"
    enabled_domain_packs: list[str] = []
    min_approvers: int = Field(
        default=2,
        ge=1,
        description="Minimum unique approvers required for high-risk ChangeRequests.",
    )
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)


class Settings(BaseModel):
    """Runtime settings."""

    environment: str = Field(default="local")
    log_level: str = Field(default="INFO")

    def is_dev(self) -> bool:
        return self.environment == "dev"

    def is_production(self) -> bool:
        return self.environment == "production"


def load_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        environment=os.environ.get("MODELOPS_ENVIRONMENT", "local"),
        log_level=os.environ.get("MODELOPS_LOG_LEVEL", "INFO"),
    )


def load_repo_config(repo_root: Path) -> RepoConfig | None:
    """Load modelops.config.yaml from repository root if present."""
    config_path = repo_root / "modelops.config.yaml"
    if not config_path.exists():
        config_path = repo_root / "modelops.config.yml"
    if not config_path.exists():
        return None

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        return RepoConfig(**raw)
    except Exception:
        return None


def resolve_model_path(repo_root: Path) -> Path:
    """Resolve the canonical model directory for a repository."""
    config = load_repo_config(repo_root)
    if config is not None:
        return repo_root / config.model_path
    return repo_root / "model"


def resolve_generated_path(repo_root: Path) -> Path:
    """Resolve the generated artifacts directory for a repository."""
    config = load_repo_config(repo_root)
    if config is not None:
        return repo_root / config.generated_path
    return repo_root / "generated"


def load_resource_limits(repo_root: Path) -> ResourceLimits:
    """Return the resource limits for a repository, falling back to defaults."""
    config = load_repo_config(repo_root)
    if config is not None:
        return config.resource_limits
    return ResourceLimits()

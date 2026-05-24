"""Configuration loader for ModelOps MDM Core."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class RepoConfig(BaseModel):
    """Repository-level configuration from modelops.config.yaml."""

    name: str = "Untitled Repository"
    description: str = ""
    version: str = "1.0.0"
    model_path: str = "model"
    generated_path: str = "generated"
    data_path: str = "data"
    enabled_domain_packs: list[str] = []


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

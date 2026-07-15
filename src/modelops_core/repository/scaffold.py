"""Scaffold a new model repository from a template or minimal defaults."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from modelops_core.config import RepoConfig

_TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates" / "model_spines"


def available_templates() -> list[str]:
    """Return the names of available model-spine templates."""
    if not _TEMPLATES_DIR.is_dir():
        return []
    return sorted(path.name for path in _TEMPLATES_DIR.iterdir() if path.is_dir())


def init_repository(
    path: Path,
    name: str = "My Model Repository",
    template: str | None = None,
) -> Path:
    """Create a new model repository at ``path``.

    Args:
        path: Directory to scaffold. Created if missing.
        name: Repository display name written to ``modelops.config.yaml``.
        template: Optional model-spine template name to copy.

    Returns:
        The resolved repository root path.

    Raises:
        ValueError: If the requested template does not exist.
    """
    target = path.resolve()
    target.mkdir(parents=True, exist_ok=True)

    model_dir = target / "model"
    model_dir.mkdir(exist_ok=True)

    generated_dir = target / "generated"
    generated_dir.mkdir(exist_ok=True)

    data_dir = target / "data" / "samples"
    data_dir.mkdir(parents=True, exist_ok=True)

    config = RepoConfig(name=name)
    config_path = target / "modelops.config.yaml"
    config_path.write_text(
        yaml.safe_dump(config.model_dump(), default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    if template:
        template_path = _TEMPLATES_DIR / template
        if not template_path.exists():
            available = ", ".join(available_templates())
            raise ValueError(f"Template not found: '{template}'. Available: {available}")

        template_model = template_path / "model"
        if template_model.exists():
            for src_file in template_model.iterdir():
                if src_file.is_file():
                    shutil.copy2(src_file, model_dir / src_file.name)

        template_config = template_path / "modelops.config.yaml"
        if template_config.exists():
            shutil.copy2(template_config, config_path)

        template_readme = template_path / "README.md"
        if template_readme.exists():
            shutil.copy2(template_readme, target / "README.md")
    else:
        example_md = model_dir / "DOMAIN-EXAMPLE.md"
        example_md.write_text(
            "---\n"
            "id: DOMAIN-EXAMPLE\n"
            "type: MasterDataDomain\n"
            "status: draft\n"
            'schema_version: "1.0"\n'
            "name: Example Domain\n"
            "---\n\n"
            "# Example Domain\n\n"
            "This is a placeholder domain object.\n",
            encoding="utf-8",
        )

    return target

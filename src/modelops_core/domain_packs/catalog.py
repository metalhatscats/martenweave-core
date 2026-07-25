"""Built-in domain-pack catalog and repository helpers."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from modelops_core.config import load_repo_config, resolve_generated_path, resolve_model_path
from modelops_core.diff import DiffResult, diff_repositories
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation import ValidationSummary, validate_objects


@dataclass(frozen=True)
class BuiltinDomainPack:
    """Built-in, synthetic domain-pack reference repository."""

    pack_id: str
    title: str
    description: str
    source_repo: Path


@dataclass(frozen=True)
class DomainPackBuildResult:
    """Result of building a built-in domain pack into a target repository."""

    pack: BuiltinDomainPack
    output_repo: Path
    include_generated: bool


@dataclass(frozen=True)
class DomainPackValidationResult:
    """Validation result for a domain-pack repository."""

    repo_root: Path
    object_count: int
    enabled_domain_packs: list[str]
    summary: ValidationSummary


_REPO_ROOT = Path(__file__).resolve().parents[3]
_BUILTIN_DOMAIN_PACKS: dict[str, BuiltinDomainPack] = {
    "sap-business-partner": BuiltinDomainPack(
        pack_id="sap-business-partner",
        title="SAP Business Partner Reference",
        description=(
            "Synthetic SAP Business Partner / Customer / Vendor reference repository "
            "for governed local demos."
        ),
        source_repo=_REPO_ROOT / "examples" / "sap_bp_customer_vendor_reference",
    ),
}


def list_builtin_domain_packs() -> list[BuiltinDomainPack]:
    """Return the built-in domain-pack catalog in stable order."""
    return [_BUILTIN_DOMAIN_PACKS[key] for key in sorted(_BUILTIN_DOMAIN_PACKS)]


def get_builtin_domain_pack(pack_id: str) -> BuiltinDomainPack:
    """Return a built-in domain pack by identifier."""
    pack = _BUILTIN_DOMAIN_PACKS.get(pack_id.lower())
    if pack is None:
        supported = ", ".join(sorted(_BUILTIN_DOMAIN_PACKS))
        raise ValueError(f"Unknown domain pack '{pack_id}'. Supported values: {supported}.")
    return pack


def resolve_domain_pack_reference(reference: str) -> tuple[str | None, Path]:
    """Resolve a domain-pack reference from a built-in ID or local repository path."""
    path = Path(reference)
    if path.exists():
        return None, path.resolve()
    pack = get_builtin_domain_pack(reference)
    return pack.pack_id, pack.source_repo.resolve()


def build_builtin_domain_pack(
    pack_id: str,
    output_repo: Path,
    *,
    include_generated: bool = False,
) -> DomainPackBuildResult:
    """Copy a built-in domain-pack reference repository to *output_repo*."""
    pack = get_builtin_domain_pack(pack_id)
    output_repo = output_repo.resolve()
    if output_repo.exists():
        if output_repo.is_file():
            raise ValueError(f"Output path must be a directory: {output_repo}")
        if any(output_repo.iterdir()):
            raise ValueError(
                f"Output repository must be empty to avoid overwriting existing work: {output_repo}"
            )
    else:
        output_repo.mkdir(parents=True, exist_ok=True)

    shutil.copy2(pack.source_repo / "modelops.config.yaml", output_repo / "modelops.config.yaml")
    shutil.copy2(pack.source_repo / "README.md", output_repo / "README.md")
    shutil.copytree(pack.source_repo / "model", output_repo / "model", dirs_exist_ok=True)
    generated_path = output_repo / "generated"
    generated_path.mkdir(parents=True, exist_ok=True)
    if include_generated and (pack.source_repo / "generated").exists():
        shutil.copytree(
            pack.source_repo / "generated",
            generated_path,
            dirs_exist_ok=True,
        )
    return DomainPackBuildResult(
        pack=pack,
        output_repo=output_repo,
        include_generated=include_generated,
    )


def validate_domain_pack_repo(repo_root: Path) -> DomainPackValidationResult:
    """Validate a domain-pack repository using its configured enabled packs."""
    repo_root = repo_root.resolve()
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)
    parsed_objects = [parse_file(path) for path in files]
    config = load_repo_config(repo_root)
    enabled = config.enabled_domain_packs if config is not None else []
    summary = validate_objects(parsed_objects, enabled)
    return DomainPackValidationResult(
        repo_root=repo_root,
        object_count=len(parsed_objects),
        enabled_domain_packs=enabled,
        summary=summary,
    )


def diff_domain_pack_repos(base_repo: Path, head_repo: Path) -> DiffResult:
    """Diff two domain-pack repositories using their canonical model paths."""
    return diff_repositories(resolve_model_path(base_repo), resolve_model_path(head_repo))


def generated_artifact_exists(repo_root: Path) -> bool:
    """Return True when a copied/built domain-pack repo already contains generated artifacts."""
    generated_path = resolve_generated_path(repo_root)
    return generated_path.exists() and any(generated_path.iterdir())

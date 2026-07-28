"""Safe deterministic portable model-package creation and verification."""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from modelops_core import __version__
from modelops_core.config import load_repo_config, resolve_model_path
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation import validate_objects

_FORMAT_VERSION = "1.0"
_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not name.startswith(("/", "\\\\"))
        and "\\\\" not in name
        and not (len(name) >= 2 and name[1] == ":")
    )


def _package_files(repo_root: Path) -> dict[str, bytes]:
    model_path = resolve_model_path(repo_root)
    files = {
        f"model/{Path(path).relative_to(model_path).as_posix()}": Path(path).read_bytes()
        for path in scan_repository(model_path)
    }
    config = repo_root / "modelops.config.yaml"
    if config.is_file():
        files["config/modelops.config.yaml"] = config.read_bytes()
    readme = repo_root / "README.md"
    if readme.is_file():
        files["docs/README.md"] = readme.read_bytes()
    return files


def create_package(repo_root: Path, output: Path) -> dict[str, Any]:
    """Create a portable package after deterministic canonical validation."""
    model_path = resolve_model_path(repo_root)
    objects = [parse_file(path) for path in scan_repository(model_path)]
    config = load_repo_config(repo_root)
    summary = validate_objects(objects, config.enabled_domain_packs if config else None)
    if not summary.is_valid:
        raise ValueError(
            f"Cannot package invalid repository ({summary.error_count} validation errors)."
        )
    content = _package_files(repo_root)
    counts = Counter(item.frontmatter.get("type", "Unknown") for item in objects)
    manifest = {
        "package_format_version": _FORMAT_VERSION,
        "tool_version": __version__,
        "repository": {"name": config.name if config else repo_root.name},
        "validation": {"is_valid": True, "error_count": 0, "warning_count": summary.warning_count},
        "object_counts": dict(sorted(counts.items())),
        "excluded_by_default": [
            "data/",
            ".env",
            "generated/",
            "uploads/",
            "patch-transactions/",
            "provider traces",
        ],
        "files": {name: _sha256(data) for name, data in sorted(content.items())},
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    integrity = {"manifest_sha256": _sha256(manifest_bytes), "files": manifest["files"]}
    all_content = {
        "manifest.json": manifest_bytes,
        "integrity.json": (json.dumps(integrity, sort_keys=True) + "\n").encode(),
        **content,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(all_content.items()):
            info = zipfile.ZipInfo(name, _FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return manifest


def inspect_package(package: Path) -> dict[str, Any]:
    """Read package metadata without extracting any archive member."""
    with zipfile.ZipFile(package) as archive:
        if any(not _safe_member(name) for name in archive.namelist()):
            raise ValueError("Unsafe archive member path.")
        if "manifest.json" not in archive.namelist() or "integrity.json" not in archive.namelist():
            raise ValueError("Invalid package: manifest.json and integrity.json are required.")
        return json.loads(archive.read("manifest.json"))


def verify_package(package: Path) -> dict[str, Any]:
    """Verify archive paths plus manifest and member checksums without extraction."""
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        if any(not _safe_member(name) for name in names):
            raise ValueError("Unsafe archive member path.")
        manifest_bytes, integrity_bytes = (
            archive.read("manifest.json"),
            archive.read("integrity.json"),
        )
        manifest, integrity = json.loads(manifest_bytes), json.loads(integrity_bytes)
        if integrity.get("manifest_sha256") != _sha256(manifest_bytes):
            raise ValueError("Package manifest checksum mismatch.")
        for name, expected in manifest.get("files", {}).items():
            if not _safe_member(name):
                raise ValueError(f"Unsafe manifest member path: {name}")
            if name not in names or _sha256(archive.read(name)) != expected:
                raise ValueError(f"Package checksum mismatch: {name}")
    return {
        "valid": True,
        "file_count": len(manifest["files"]),
        "format": manifest["package_format_version"],
    }

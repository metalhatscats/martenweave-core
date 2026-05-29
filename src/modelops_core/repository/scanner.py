"""Canonical file discovery scanner."""

from __future__ import annotations

from pathlib import Path

# Directories to skip during repository scan.
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        "generated",
        "data",
        "imports",
        "schemas",
        "apps",
        "docs",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".next",
        "__pycache__",
    }
)


def scan_repository(root: str | Path) -> list[str]:
    """Recursively discover canonical ``.md``, ``.yaml``, and ``.yml`` files.

    Args:
        root: Repository root directory.

    Returns:
        Sorted list of absolute file paths.
    """
    root_path = Path(root).resolve()
    files: list[str] = []

    for path in root_path.rglob("*"):
        if path.is_dir():
            rel_parts = path.relative_to(root_path).parts
            if path.name in _SKIP_DIRS:
                continue
            # Also skip hidden directories
            if any(part.startswith(".") for part in rel_parts):
                continue
            continue

        if path.suffix.lower() in {".md", ".yaml", ".yml"}:
            rel_parts = path.relative_to(root_path).parts
            # Skip if any parent directory is in the skip list
            if any(part in _SKIP_DIRS for part in rel_parts):
                continue
            # Skip files inside hidden directories
            if any(part.startswith(".") for part in rel_parts):
                continue
            files.append(str(path.resolve()))

    return sorted(files)

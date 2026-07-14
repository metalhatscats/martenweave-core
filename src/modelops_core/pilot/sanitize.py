"""Sanitize a migration assessment package for external sharing.

Removes raw datasets, blocks unsupported binaries, and redacts
machine-specific paths and email addresses from text artifacts while
leaving the source package untouched.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core import __version__

_ALLOWED_SUFFIXES: frozenset[str] = frozenset({".md", ".json", ".xlsx"})
_TEXT_SUFFIXES: frozenset[str] = frozenset({".md", ".json"})

# Absolute paths: Unix (/...) or Windows (C:\...).
_UNIX_PATH_RE = re.compile(r"(/[A-Za-z0-9_\-.]+(?:/[A-Za-z0-9_\-.]+)+)")
_WINDOWS_PATH_RE = re.compile(r"([A-Za-z]:\\(?:[^\\\s]+(?:\\[^\\\s]+)*))")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def _redact_text(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Redact absolute paths and emails from *text*.

    Returns the redacted text plus a deterministic list of redaction records.
    """
    redactions: list[dict[str, Any]] = []
    result = text

    result, path_count = _UNIX_PATH_RE.subn("<redacted-path>", result)
    result, win_count = _WINDOWS_PATH_RE.subn("<redacted-path>", result)
    total_path = path_count + win_count
    if total_path:
        redactions.append({"type": "path", "count": total_path})

    result, email_count = _EMAIL_RE.subn("<redacted-email>", result)
    if email_count:
        redactions.append({"type": "email", "count": email_count})

    return result, redactions


def _is_under_raw_dataset_dir(rel: Path) -> bool:
    """Return True when the relative path sits under a raw dataset folder."""
    return any(part == "dataset_readiness" for part in rel.parts)


def sanitize_assessment(
    input_dir: Path,
    output_dir: Path,
    *,
    exclude_raw_datasets: bool = True,
) -> dict[str, Any]:
    """Create a shareable, sanitized copy of an assessment package.

    Args:
        input_dir: Directory containing the original assessment outputs.
        output_dir: Directory where sanitized outputs will be written.
        exclude_raw_datasets: When True, drop files under ``dataset_readiness/``.

    Returns:
        A sanitization manifest dict with ``included_files``, ``excluded_files``,
        ``blocked_files``, and ``redactions``.

    Raises:
        ValueError: If unsupported binary files are present in the input.
    """
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    included_files: list[str] = []
    excluded_files: list[str] = []
    blocked_files: list[dict[str, str]] = []
    redactions: list[dict[str, Any]] = []

    for src_path in sorted(input_dir.rglob("*")):
        if not src_path.is_file():
            continue

        rel = src_path.relative_to(input_dir)
        rel_posix = rel.as_posix()

        if exclude_raw_datasets and _is_under_raw_dataset_dir(rel):
            excluded_files.append(rel_posix)
            continue

        suffix = src_path.suffix.lower()
        if suffix not in _ALLOWED_SUFFIXES:
            blocked_files.append({"path": rel_posix, "reason": "unsupported file type"})
            continue

        dest_path = output_dir / rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if suffix in _TEXT_SUFFIXES:
            text = src_path.read_text(encoding="utf-8")
            redacted, file_redactions = _redact_text(text)
            dest_path.write_text(redacted, encoding="utf-8")
            if file_redactions:
                redactions.append({"file": rel_posix, "redactions": file_redactions})
        else:
            shutil.copy2(src_path, dest_path)

        included_files.append(rel_posix)

    if blocked_files:
        names = ", ".join(b["path"] for b in blocked_files)
        raise ValueError(f"Blocked unsupported file(s): {names}")

    manifest: dict[str, Any] = {
        "tool": "martenweave",
        "version": __version__,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "included_files": sorted(included_files),
        "excluded_files": sorted(excluded_files),
        "blocked_files": blocked_files,
        "redactions": sorted(redactions, key=lambda r: r.get("file", "")),
    }

    manifest_path = output_dir / "sanitization-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest

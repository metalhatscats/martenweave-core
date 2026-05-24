"""Canonical file parser for Markdown/YAML frontmatter and YAML-only files."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ParsedObject:
    """Result of parsing a single canonical file."""

    source_path: str
    content_hash: str
    frontmatter: dict[str, Any] | None
    body: str | None
    parser_error: str | None


def _compute_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_file(file_path: str | Path) -> ParsedObject:
    """Parse a canonical file based on its extension.

    * ``.md`` → Markdown with optional YAML frontmatter.
    * ``.yaml`` / ``.yml`` → YAML-only file.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".md":
        return _parse_markdown(path)
    if suffix in (".yaml", ".yml"):
        return _parse_yaml(path)

    return ParsedObject(
        source_path=str(path),
        content_hash="",
        frontmatter=None,
        body=None,
        parser_error=f"Unsupported file extension: {suffix}",
    )


def _parse_markdown(path: Path) -> ParsedObject:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ParsedObject(
            source_path=str(path),
            content_hash="",
            frontmatter=None,
            body=None,
            parser_error=f"Failed to read file: {exc}",
        )

    content_hash = _compute_hash(raw)

    if not raw.startswith("---"):
        return ParsedObject(
            source_path=str(path),
            content_hash=content_hash,
            frontmatter=None,
            body=raw,
            parser_error=None,
        )

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return ParsedObject(
            source_path=str(path),
            content_hash=content_hash,
            frontmatter=None,
            body=raw,
            parser_error=None,
        )

    frontmatter_raw = parts[1].strip()
    body = parts[2].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_raw) if frontmatter_raw else {}
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as exc:
        return ParsedObject(
            source_path=str(path),
            content_hash=content_hash,
            frontmatter=None,
            body=raw,
            parser_error=f"Invalid YAML frontmatter: {exc}",
        )

    return ParsedObject(
        source_path=str(path),
        content_hash=content_hash,
        frontmatter=frontmatter,
        body=body,
        parser_error=None,
    )


def _parse_yaml(path: Path) -> ParsedObject:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ParsedObject(
            source_path=str(path),
            content_hash="",
            frontmatter=None,
            body=None,
            parser_error=f"Failed to read file: {exc}",
        )

    content_hash = _compute_hash(raw)

    try:
        frontmatter = yaml.safe_load(raw)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as exc:
        return ParsedObject(
            source_path=str(path),
            content_hash=content_hash,
            frontmatter=None,
            body=None,
            parser_error=f"Invalid YAML: {exc}",
        )

    return ParsedObject(
        source_path=str(path),
        content_hash=content_hash,
        frontmatter=frontmatter,
        body=None,
        parser_error=None,
    )

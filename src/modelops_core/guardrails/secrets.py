"""Secret redaction and scanning utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Patterns that match common secret values.
# Each tuple is (pattern_name, regex, redaction_replacement).
_SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    # API keys with explicit prefixes
    (
        "api_key",
        re.compile(
            r"(?i)(api[_-]?key\s*[=:]\s*)['\"]?([a-z0-9_\-]{16,})['\"]?",
        ),
        r"\1***REDACTED***",
    ),
    # Generic secret / password
    (
        "secret",
        re.compile(
            r"(?i)(secret\s*[=:]\s*)['\"]?([^\s'\";]{8,})['\"]?",
        ),
        r"\1***REDACTED***",
    ),
    (
        "password",
        re.compile(
            r"(?i)(password\s*[=:]\s*)['\"]?([^\s'\";]{8,})['\"]?",
        ),
        r"\1***REDACTED***",
    ),
    # Bearer / access tokens
    (
        "bearer_token",
        re.compile(
            r"(?i)(bearer\s+)['\"]?([a-z0-9_\-\.]{20,})['\"]?",
        ),
        r"\1***REDACTED***",
    ),
    (
        "access_token",
        re.compile(
            r"(?i)(access[_-]?token\s*[=:]\s*)['\"]?([a-z0-9_\-\.]{20,})['\"]?",
        ),
        r"\1***REDACTED***",
    ),
    # AWS keys
    (
        "aws_access_key_id",
        re.compile(
            r"(?i)(aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*)['\"]?([A-Z0-9]{20})['\"]?",
        ),
        r"\1***REDACTED***",
    ),
    (
        "aws_secret_access_key",
        re.compile(
            r"(?i)(aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*)['\"]?([a-zA-Z0-9/+=]{40})['\"]?",
        ),
        r"\1***REDACTED***",
    ),
    # Private key blocks
    (
        "private_key_block",
        re.compile(
            r"(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)[\s\S]*?"
            r"(-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)",
        ),
        r"\1\n***REDACTED***\n\2",
    ),
    # Google API key (AIza...)
    (
        "google_api_key",
        re.compile(r"(AIza[0-9A-Za-z_\-]{35})",),
        r"***REDACTED***",
    ),
    # Moonshot / OpenAI keys (sk-...)
    (
        "sk_api_key",
        re.compile(
            r"(sk-[a-zA-Z0-9]{20,})"),
        r"***REDACTED***",
    ),
]

# Patterns used for scanning (lighter weight, focused on finding secrets).
_SCAN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "api_key",
        re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)['\"]?([a-z0-9_\-]{16,})['\"]?"),
    ),
    (
        "secret",
        re.compile(r"(?i)(secret\s*[=:]\s*)['\"]?([^\s'\";]{8,})['\"]?"),
    ),
    (
        "password",
        re.compile(r"(?i)(password\s*[=:]\s*)['\"]?([^\s'\";]{8,})['\"]?"),
    ),
    (
        "bearer_token",
        re.compile(r"(?i)(bearer\s+)['\"]?([a-z0-9_\-\.]{20,})['\"]?"),
    ),
    (
        "access_token",
        re.compile(r"(?i)(access[_-]?token\s*[=:]\s*)['\"]?([a-z0-9_\-\.]{20,})['\"]?"),
    ),
    (
        "aws_access_key_id",
        re.compile(r"(?i)(aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*)['\"]?([A-Z0-9]{20})['\"]?"),
    ),
    (
        "aws_secret_access_key",
        re.compile(
            r"(?i)(aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*)"
            r"['\"]?([a-zA-Z0-9/+=]{40})['\"]?"
        ),
    ),
    (
        "private_key_block",
        re.compile(
            r"(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
        ),
    ),
    (
        "google_api_key",
        re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    ),
    (
        "sk_api_key",
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    ),
]

# Files and paths to skip during repo scanning.
_SKIP_PATHS: set[str] = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "generated",
    ".DS_Store",
}

# Extensions to skip (binary or known safe).
_SKIP_EXTENSIONS: set[str] = {
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".db", ".sqlite", ".sqlite3",
    ".zip", ".tar", ".gz", ".bz2", ".7z",
}

# Maximum file size to scan (1 MB).
_MAX_SCAN_BYTES = 1_048_576


@dataclass
class SecretFinding:
    """A single secret finding in a scanned text or file."""

    pattern_name: str
    line_number: int
    line_text: str
    file_path: str | None = None


def redact(text: str, placeholder: str = "***REDACTED***") -> str:
    """Redact sensitive values from *text* using known patterns.

    The default *placeholder* replaces detected secret values while
    preserving the surrounding context (e.g. ``API_KEY=***REDACTED***``).
    """
    result = text
    for _name, pattern, replacement in _SENSITIVE_PATTERNS:
        # Allow caller override via placeholder only for simple replacements.
        if placeholder != "***REDACTED***":
            # For group-based replacements, substitute the placeholder.
            if r"\1" in replacement:
                replacement = replacement.replace("***REDACTED***", placeholder)
            else:
                replacement = placeholder
        result = pattern.sub(replacement, result)
    return result


def redact_dict(data: Any, placeholder: str = "***REDACTED***") -> Any:
    """Recursively redact secrets from a dict, list, or string.

    Returns a new structure with the same shape; immutable values are
    left untouched except for strings, which are passed through
    :func:`redact`.
    """
    if isinstance(data, dict):
        return {
            k: redact_dict(v, placeholder=placeholder) for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact_dict(item, placeholder=placeholder) for item in data]
    if isinstance(data, str):
        return redact(data, placeholder=placeholder)
    return data


def scan_text(text: str, file_path: str | None = None) -> list[SecretFinding]:
    """Scan *text* for potential secrets and return findings.

    This is a heuristic scan; false positives are possible for
    test fixtures or documentation examples.
    """
    findings: list[SecretFinding] = []
    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        for pattern_name, pattern in _SCAN_PATTERNS:
            if pattern.search(line):
                # Skip lines that look like comments showing placeholders.
                if _is_placeholder_line(line):
                    continue
                findings.append(
                    SecretFinding(
                        pattern_name=pattern_name,
                        line_number=line_number,
                        line_text=line.rstrip("\n\r"),
                        file_path=file_path,
                    )
                )
                # Only report first match per line.
                break
    return findings


def scan_file(path: Path) -> list[SecretFinding]:
    """Scan a single file for potential secrets."""
    if path.suffix.lower() in _SKIP_EXTENSIONS:
        return []
    try:
        stat = path.stat()
        if stat.st_size > _MAX_SCAN_BYTES:
            return []
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return []
    return scan_text(text, file_path=str(path))


def scan_repo(repo_root: Path) -> list[SecretFinding]:
    """Recursively scan a repository for potential secrets.

    Skips known build artifact directories, virtual environments,
    and binary files.
    """
    findings: list[SecretFinding] = []
    for item in repo_root.rglob("*"):
        if not item.is_file():
            continue
        if any(part in _SKIP_PATHS for part in item.parts):
            continue
        findings.extend(scan_file(item))
    return findings


def _is_placeholder_line(line: str) -> bool:
    """Return True if *line* contains only a documented placeholder."""
    stripped = line.strip().lower()
    # Comment lines with <your-key>, <your token>, etc.
    if stripped.startswith("#") or stripped.startswith("//"):
        if any(marker in stripped for marker in ("<your", "<example>", "placeholder", "xxx")):
            return True
    # Values that are clearly placeholders.
    if any(marker in stripped for marker in ("<your-key>", "<your token>", "<password>")):
        return True
    return False

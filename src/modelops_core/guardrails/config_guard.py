"""Configuration guardrails for environment and repository settings."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from modelops_core.guardrails.secrets import scan_text


class ConfigGuardMode(StrEnum):
    """Config guard scan modes."""

    LOCAL = "local"
    RELEASE = "release"


class FileStatus(StrEnum):
    """Git classification for files with guardrail findings."""

    TRACKED = "tracked"
    UNTRACKED = "untracked"
    IGNORED = "ignored"
    UNKNOWN = "unknown"


@dataclass
class GuardrailIssue:
    """A single guardrail issue found in configuration."""

    code: str
    message: str
    file_path: str | None = None
    line_number: int | None = None
    severity: str = "WARNING"
    file_status: str | None = None


class _GitFileClassifier:
    """Classify files relative to the current Git worktree."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self._is_git_repo = self._git(["rev-parse", "--is-inside-work-tree"]).returncode == 0

    def classify(self, path: str | Path | None) -> str | None:
        """Return tracked, untracked, ignored, or unknown for a repository file."""
        if path is None:
            return None
        if not self._is_git_repo:
            return FileStatus.UNKNOWN.value

        try:
            path_obj = Path(path)
            absolute_path = path_obj if path_obj.is_absolute() else self.repo_root / path_obj
            relative_path = absolute_path.resolve().relative_to(self.repo_root).as_posix()
        except (OSError, ValueError):
            return FileStatus.UNKNOWN.value

        if self._git(["ls-files", "--error-unmatch", "--", relative_path]).returncode == 0:
            return FileStatus.TRACKED.value
        if self._git(["check-ignore", "-q", "--", relative_path]).returncode == 0:
            return FileStatus.IGNORED.value
        if absolute_path.exists():
            return FileStatus.UNTRACKED.value
        return FileStatus.UNKNOWN.value

    def _git(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
        )


def _normalize_mode(mode: ConfigGuardMode | str) -> ConfigGuardMode:
    if isinstance(mode, ConfigGuardMode):
        return mode
    return ConfigGuardMode(mode)


def _annotate_file_status(
    issues: list[GuardrailIssue], classifier: _GitFileClassifier
) -> list[GuardrailIssue]:
    for issue in issues:
        issue.file_status = classifier.classify(issue.file_path)
    return issues


def validate_env_file(path: Path) -> list[GuardrailIssue]:
    """Validate a ``.env`` file for secret leakage and structural issues.

    Checks:
    - No hardcoded secrets (heuristic scan).
    - All lines use ``KEY=value`` format (no spaces around ``=``).
    - No empty keys.
    - Keys follow UPPER_SNAKE_CASE convention.
    """
    issues: list[GuardrailIssue] = []
    if not path.exists():
        return issues

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        issues.append(
            GuardrailIssue(
                code="ENV_UNREADABLE",
                message=f"Could not read .env file: {exc}",
                file_path=str(path),
                severity="ERROR",
            )
        )
        return issues

    # Secret scan
    secret_findings = scan_text(text, file_path=str(path))
    for finding in secret_findings:
        issues.append(
            GuardrailIssue(
                code="ENV_SECRET_DETECTED",
                message=f"Potential secret ({finding.pattern_name}) on line {finding.line_number}",
                file_path=str(path),
                line_number=finding.line_number,
                severity="ERROR",
            )
        )

    # Structural validation
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in stripped:
            issues.append(
                GuardrailIssue(
                    code="ENV_MISSING_EQUALS",
                    message=f"Line missing '=' delimiter: {stripped[:40]}",
                    file_path=str(path),
                    line_number=line_number,
                    severity="WARNING",
                )
            )
            continue

        key, _sep, _value = stripped.partition("=")
        key = key.strip()

        if not key:
            issues.append(
                GuardrailIssue(
                    code="ENV_EMPTY_KEY",
                    message="Empty key before '='",
                    file_path=str(path),
                    line_number=line_number,
                    severity="WARNING",
                )
            )
            continue

        if " " in key:
            issues.append(
                GuardrailIssue(
                    code="ENV_KEY_HAS_SPACES",
                    message=f"Key contains spaces: {key}",
                    file_path=str(path),
                    line_number=line_number,
                    severity="WARNING",
                )
            )

        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            issues.append(
                GuardrailIssue(
                    code="ENV_KEY_NON_STANDARD",
                    message=f"Key '{key}' should use UPPER_SNAKE_CASE",
                    file_path=str(path),
                    line_number=line_number,
                    severity="INFO",
                )
            )

    return issues


def validate_repo_config(path: Path) -> list[GuardrailIssue]:
    """Validate a ``modelops.config.yaml`` for embedded secrets.

    Checks:
    - Heuristic secret scan on the raw text.
    - No keys that look like credential paths (e.g. ``private_key_file``).
    """
    issues: list[GuardrailIssue] = []
    if not path.exists():
        return issues

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        issues.append(
            GuardrailIssue(
                code="CONFIG_UNREADABLE",
                message=f"Could not read config file: {exc}",
                file_path=str(path),
                severity="ERROR",
            )
        )
        return issues

    secret_findings = scan_text(text, file_path=str(path))
    for finding in secret_findings:
        issues.append(
            GuardrailIssue(
                code="CONFIG_SECRET_DETECTED",
                message=f"Potential secret ({finding.pattern_name}) on line {finding.line_number}",
                file_path=str(path),
                line_number=finding.line_number,
                severity="ERROR",
            )
        )

    # Check for credential-related keys
    credential_keys = re.compile(r"(?i)(password|secret|token|private_key|api_key)")
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = credential_keys.search(line)
        if match and not line.strip().startswith("#"):
            issues.append(
                GuardrailIssue(
                    code="CONFIG_CREDENTIAL_KEY",
                    message=f"Credential key '{match.group(0)}' should not be in config file",
                    file_path=str(path),
                    line_number=line_number,
                    severity="WARNING",
                )
            )

    return issues


def validate_gitignore(repo_root: Path) -> list[GuardrailIssue]:
    """Validate ``.gitignore`` has recommended secret-blocking patterns.

    Checks for presence of patterns that prevent common secret files
    from being committed.
    """
    issues: list[GuardrailIssue] = []
    gitignore = repo_root / ".gitignore"
    if not gitignore.exists():
        issues.append(
            GuardrailIssue(
                code="GITIGNORE_MISSING",
                message="No .gitignore found in repository root",
                file_path=str(repo_root),
                severity="WARNING",
            )
        )
        return issues

    try:
        text = gitignore.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        issues.append(
            GuardrailIssue(
                code="GITIGNORE_UNREADABLE",
                message=f"Could not read .gitignore: {exc}",
                file_path=str(gitignore),
                severity="ERROR",
            )
        )
        return issues

    lines = {line.strip() for line in text.splitlines()}

    required_patterns = [
        (".env", "Environment variable files"),
        ("*.pem", "PEM certificate / key files"),
        ("*.key", "Private key files"),
        ("id_rsa", "SSH private key"),
        ("id_ed25519", "SSH Ed25519 private key"),
    ]

    for pattern, description in required_patterns:
        if pattern not in lines:
            issues.append(
                GuardrailIssue(
                    code="GITIGNORE_MISSING_PATTERN",
                    message=f"Missing pattern '{pattern}' ({description})",
                    file_path=str(gitignore),
                    severity="WARNING",
                )
            )

    return issues


def run_all_checks(
    repo_root: Path, mode: ConfigGuardMode | str = ConfigGuardMode.LOCAL
) -> dict[str, list[GuardrailIssue]]:
    """Run all configuration guardrail checks for a repository.

    Returns a mapping from check name to list of issues.
    """
    _normalize_mode(mode)
    results: dict[str, list[GuardrailIssue]] = {}
    classifier = _GitFileClassifier(repo_root)

    env_path = repo_root / ".env"
    results["env_file"] = _annotate_file_status(validate_env_file(env_path), classifier)

    config_path = repo_root / "modelops.config.yaml"
    if not config_path.exists():
        config_path = repo_root / "modelops.config.yml"
    results["repo_config"] = _annotate_file_status(validate_repo_config(config_path), classifier)

    results["gitignore"] = _annotate_file_status(validate_gitignore(repo_root), classifier)

    # Scan the whole repo for secrets (excluding known safe paths).
    from modelops_core.guardrails.secrets import scan_repo

    secret_findings = scan_repo(repo_root)
    # Convert SecretFinding to GuardrailIssue
    repo_secret_issues: list[GuardrailIssue] = []
    for finding in secret_findings:
        # Skip the .env file (already checked) and test fixtures.
        if finding.file_path:
            fp = Path(finding.file_path)
            name = fp.name
            if ".env" in name or name.startswith("test_") or "fixtures" in name:
                continue
            if any(part == "__pycache__" for part in fp.parts):
                continue
        repo_secret_issues.append(
            GuardrailIssue(
                code="REPO_SECRET_DETECTED",
                message=(
                    f"Potential {finding.pattern_name} in {finding.file_path}:{finding.line_number}"
                ),
                file_path=finding.file_path,
                line_number=finding.line_number,
                severity="ERROR",
                file_status=classifier.classify(finding.file_path),
            )
        )
    results["repo_secrets"] = repo_secret_issues

    return results


def has_blocking_issues(
    results: dict[str, list[GuardrailIssue]], mode: ConfigGuardMode | str = ConfigGuardMode.LOCAL
) -> bool:
    """Return True if any check produced an ERROR-level issue."""
    normalized_mode = _normalize_mode(mode)
    for issues in results.values():
        for issue in issues:
            if (
                normalized_mode == ConfigGuardMode.RELEASE
                and issue.file_status == FileStatus.IGNORED.value
            ):
                continue
            if issue.severity == "ERROR":
                return True
    return False

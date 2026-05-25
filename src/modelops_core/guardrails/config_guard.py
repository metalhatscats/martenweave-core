"""Configuration guardrails for environment and repository settings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from modelops_core.guardrails.secrets import scan_text


@dataclass
class GuardrailIssue:
    """A single guardrail issue found in configuration."""

    code: str
    message: str
    file_path: str | None = None
    line_number: int | None = None
    severity: str = "WARNING"


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


def run_all_checks(repo_root: Path) -> dict[str, list[GuardrailIssue]]:
    """Run all configuration guardrail checks for a repository.

    Returns a mapping from check name to list of issues.
    """
    results: dict[str, list[GuardrailIssue]] = {}

    env_path = repo_root / ".env"
    results["env_file"] = validate_env_file(env_path)

    config_path = repo_root / "modelops.config.yaml"
    if not config_path.exists():
        config_path = repo_root / "modelops.config.yml"
    results["repo_config"] = validate_repo_config(config_path)

    results["gitignore"] = validate_gitignore(repo_root)

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
                    f"Potential {finding.pattern_name} in "
                    f"{finding.file_path}:{finding.line_number}"
                ),
                file_path=finding.file_path,
                line_number=finding.line_number,
                severity="ERROR",
            )
        )
    results["repo_secrets"] = repo_secret_issues

    return results


def has_blocking_issues(results: dict[str, list[GuardrailIssue]]) -> bool:
    """Return True if any check produced an ERROR-level issue."""
    for issues in results.values():
        for issue in issues:
            if issue.severity == "ERROR":
                return True
    return False

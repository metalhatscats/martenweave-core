"""Tests for secret redaction and configuration guardrails."""

from __future__ import annotations

import subprocess
from pathlib import Path

from modelops_core.guardrails.config_guard import (
    ConfigGuardMode,
    FileStatus,
    GuardrailIssue,
    has_blocking_issues,
    run_all_checks,
    validate_env_file,
    validate_gitignore,
    validate_repo_config,
)
from modelops_core.guardrails.secrets import (
    redact,
    redact_dict,
    scan_file,
    scan_repo,
    scan_text,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# redact
# ---------------------------------------------------------------------------


class TestRedact:
    def test_redacts_api_key(self) -> None:
        text = "API_KEY=sk-abc123def456ghi789"
        result = redact(text)
        assert "***REDACTED***" in result
        assert "sk-abc123" not in result

    def test_redacts_password(self) -> None:
        text = "DB_PASSWORD=SuperSecret123!"
        result = redact(text)
        assert "***REDACTED***" in result
        assert "SuperSecret" not in result

    def test_redacts_bearer_token(self) -> None:
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact(text)
        assert "***REDACTED***" in result
        assert "eyJhbGci" not in result

    def test_redacts_aws_secret(self) -> None:
        text = "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        result = redact(text)
        assert "***REDACTED***" in result
        assert "wJalrXUtn" not in result

    def test_redacts_google_api_key(self) -> None:
        text = "GOOGLE_API_KEY=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"
        result = redact(text)
        assert "***REDACTED***" in result
        assert "AIzaSyDd" not in result

    def test_redacts_private_key_block(self) -> None:
        text = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB7MhgwKVPSmwaFkYLv\n"
            "-----END RSA PRIVATE KEY-----"
        )
        result = redact(text)
        assert "***REDACTED***" in result
        assert "MIIEpAIBAA" not in result

    def test_redacts_custom_placeholder(self) -> None:
        text = "API_KEY=sk-abcdefghijklmnopqrstuvwxyz"
        result = redact(text, placeholder="[HIDDEN]")
        assert "[HIDDEN]" in result

    def test_leaves_safe_text_untouched(self) -> None:
        text = "MODELOPS_ENVIRONMENT=local\nMODELOPS_LOG_LEVEL=INFO"
        result = redact(text)
        assert result == text

    def test_redacts_multiple_secrets(self) -> None:
        text = "API_KEY=sk-abcdefghijklmnopqrstuvwxyz\nDB_PASSWORD=Secret456789"
        result = redact(text)
        assert result.count("***REDACTED***") == 2


# ---------------------------------------------------------------------------
# redact_dict
# ---------------------------------------------------------------------------


class TestRedactDict:
    def test_redacts_nested_dict(self) -> None:
        data = {
            "config": {
                "api_key": "sk-abcdefghijklmnopqrstuvwxyz",
                "host": "localhost",
            },
            "passwords": [
                "DB_PASSWORD=pass1longer",
                "DB_PASSWORD=pass2longer",
            ],
        }
        result = redact_dict(data)
        assert "***REDACTED***" in result["config"]["api_key"]
        assert result["config"]["host"] == "localhost"
        assert all("***REDACTED***" in p for p in result["passwords"])

    def test_leaves_non_strings_alone(self) -> None:
        data = {"count": 42, "flag": True, "ratio": 3.14}
        assert redact_dict(data) == data

    def test_empty_dict(self) -> None:
        assert redact_dict({}) == {}


# ---------------------------------------------------------------------------
# scan_text
# ---------------------------------------------------------------------------


class TestScanText:
    def test_finds_api_key(self) -> None:
        text = "API_KEY=sk-abc123def456ghi789"
        findings = scan_text(text)
        assert len(findings) == 1
        assert findings[0].pattern_name == "api_key"
        assert findings[0].line_number == 1

    def test_finds_password(self) -> None:
        text = "password=SuperSecret123!"
        findings = scan_text(text)
        assert any(f.pattern_name == "password" for f in findings)

    def test_finds_private_key(self) -> None:
        text = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----"
        findings = scan_text(text)
        assert any(f.pattern_name == "private_key_block" for f in findings)

    def test_skips_placeholder_comments(self) -> None:
        text = "# API_KEY=<your-key>\n# password=<password>"
        findings = scan_text(text)
        assert not findings

    def test_skips_example_placeholders(self) -> None:
        text = "API_KEY=<example>\nSECRET=xxx"
        findings = scan_text(text)
        assert not findings

    def test_no_false_positives_on_safe_text(self) -> None:
        text = "MODELOPS_ENVIRONMENT=local\nMODELOPS_LOG_LEVEL=INFO"
        findings = scan_text(text)
        assert not findings

    def test_returns_file_path(self) -> None:
        findings = scan_text("API_KEY=sk-abcdefghijklmnopqrstuvwxyz", file_path="/tmp/.env")
        assert findings[0].file_path == "/tmp/.env"


# ---------------------------------------------------------------------------
# scan_file
# ---------------------------------------------------------------------------


class TestScanFile:
    def test_scans_file_with_secret(self, tmp_path: Path) -> None:
        path = tmp_path / "config.txt"
        path.write_text("API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
        findings = scan_file(path)
        assert len(findings) == 1
        assert findings[0].pattern_name == "api_key"

    def test_skips_binary_extensions(self, tmp_path: Path) -> None:
        path = tmp_path / "image.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        assert scan_file(path) == []

    def test_skips_oversized_files(self, tmp_path: Path) -> None:
        path = tmp_path / "huge.log"
        path.write_text("x" * 2_000_000, encoding="utf-8")
        assert scan_file(path) == []


# ---------------------------------------------------------------------------
# scan_repo
# ---------------------------------------------------------------------------


class TestScanRepo:
    def test_scans_repo_and_finds_secret(self, tmp_path: Path) -> None:
        (tmp_path / "config.env").write_text(
            "API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8"
        )
        findings = scan_repo(tmp_path)
        assert any(f.pattern_name == "api_key" for f in findings)

    def test_skips_venv(self, tmp_path: Path) -> None:
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "secrets.txt").write_text("API_KEY=sk-secret\n", encoding="utf-8")
        findings = scan_repo(tmp_path)
        assert not any(f.pattern_name == "api_key" for f in findings)

    def test_skips_pycache(self, tmp_path: Path) -> None:
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "secrets.txt").write_text("API_KEY=sk-secret\n", encoding="utf-8")
        findings = scan_repo(tmp_path)
        assert not any(f.pattern_name == "api_key" for f in findings)

    def test_skips_packaged_workbench_runtime(self, tmp_path: Path) -> None:
        runtime = tmp_path / "src" / "modelops_core" / "workbench_static" / "assets"
        runtime.mkdir(parents=True)
        (runtime / "index.js").write_text("password=third-party-runtime-value", encoding="utf-8")

        assert scan_repo(tmp_path) == []


# ---------------------------------------------------------------------------
# validate_env_file
# ---------------------------------------------------------------------------


class TestValidateEnvFile:
    def test_no_issues_for_example_env(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("MODELOPS_ENVIRONMENT=local\nMODELOPS_LOG_LEVEL=INFO\n", encoding="utf-8")
        issues = validate_env_file(env)
        assert not issues

    def test_detects_secret_in_env(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
        issues = validate_env_file(env)
        assert any(i.code == "ENV_SECRET_DETECTED" for i in issues)

    def test_detects_missing_equals(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("MODELOPS_ENVIRONMENT local\n", encoding="utf-8")
        issues = validate_env_file(env)
        assert any(i.code == "ENV_MISSING_EQUALS" for i in issues)

    def test_detects_empty_key(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("=value\n", encoding="utf-8")
        issues = validate_env_file(env)
        assert any(i.code == "ENV_EMPTY_KEY" for i in issues)

    def test_detects_key_with_spaces(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("MY KEY=value\n", encoding="utf-8")
        issues = validate_env_file(env)
        assert any(i.code == "ENV_KEY_HAS_SPACES" for i in issues)

    def test_warns_non_standard_key(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("myKey=value\n", encoding="utf-8")
        issues = validate_env_file(env)
        assert any(i.code == "ENV_KEY_NON_STANDARD" for i in issues)

    def test_missing_file_is_fine(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        assert validate_env_file(env) == []


# ---------------------------------------------------------------------------
# validate_repo_config
# ---------------------------------------------------------------------------


class TestValidateRepoConfig:
    def test_no_issues_for_clean_config(self, tmp_path: Path) -> None:
        config = tmp_path / "modelops.config.yaml"
        config.write_text(
            "name: Test Repo\nversion: 1.0.0\nmodel_path: model\n",
            encoding="utf-8",
        )
        issues = validate_repo_config(config)
        assert not issues

    def test_detects_secret_in_config(self, tmp_path: Path) -> None:
        config = tmp_path / "modelops.config.yaml"
        config.write_text(
            "name: Test\nextra: API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n",
            encoding="utf-8",
        )
        issues = validate_repo_config(config)
        assert any(i.code == "CONFIG_SECRET_DETECTED" for i in issues)

    def test_warns_credential_key(self, tmp_path: Path) -> None:
        config = tmp_path / "modelops.config.yaml"
        config.write_text("name: Test\ndb_password: hunter2\n", encoding="utf-8")
        issues = validate_repo_config(config)
        assert any(i.code == "CONFIG_CREDENTIAL_KEY" for i in issues)

    def test_missing_file_is_fine(self, tmp_path: Path) -> None:
        config = tmp_path / "modelops.config.yaml"
        assert validate_repo_config(config) == []


# ---------------------------------------------------------------------------
# validate_gitignore
# ---------------------------------------------------------------------------


class TestValidateGitignore:
    def test_no_issues_for_complete_gitignore(self, tmp_path: Path) -> None:
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".env\n*.pem\n*.key\nid_rsa\nid_ed25519\n", encoding="utf-8")
        issues = validate_gitignore(tmp_path)
        assert not issues

    def test_warns_missing_patterns(self, tmp_path: Path) -> None:
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".env\n", encoding="utf-8")
        issues = validate_gitignore(tmp_path)
        assert any(i.code == "GITIGNORE_MISSING_PATTERN" for i in issues)

    def test_warns_missing_gitignore(self, tmp_path: Path) -> None:
        issues = validate_gitignore(tmp_path)
        assert any(i.code == "GITIGNORE_MISSING" for i in issues)


# ---------------------------------------------------------------------------
# run_all_checks
# ---------------------------------------------------------------------------


class TestRunAllChecks:
    def test_runs_all_checks(self, tmp_path: Path) -> None:
        # Create a minimal repo
        (tmp_path / ".gitignore").write_text(".env\n*.pem\n*.key\n", encoding="utf-8")
        (tmp_path / "modelops.config.yaml").write_text(
            "name: Test\nversion: 1.0.0\n", encoding="utf-8"
        )
        results = run_all_checks(tmp_path)
        assert "env_file" in results
        assert "repo_config" in results
        assert "gitignore" in results
        assert "repo_secrets" in results

    def test_finds_secret_in_repo(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text(".env\n*.pem\n*.key\n", encoding="utf-8")
        (tmp_path / "modelops.config.yaml").write_text("name: Test\n", encoding="utf-8")
        (tmp_path / "leaked.txt").write_text(
            "API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8"
        )
        results = run_all_checks(tmp_path)
        assert any(i.code == "REPO_SECRET_DETECTED" for i in results["repo_secrets"])

    def test_classifies_tracked_untracked_and_ignored_findings(self, tmp_path: Path) -> None:
        _git(tmp_path, "init")
        (tmp_path / ".gitignore").write_text(
            ".env\n*.pem\n*.key\nid_rsa\nid_ed25519\n", encoding="utf-8"
        )
        (tmp_path / "tracked.txt").write_text(
            "API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8"
        )
        (tmp_path / "untracked.txt").write_text(
            "API_KEY=sk-bcdefghijklmnopqrstuvwxyz\n", encoding="utf-8"
        )
        (tmp_path / ".env").write_text("API_KEY=sk-cdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
        _git(tmp_path, "add", ".gitignore", "tracked.txt")

        results = run_all_checks(tmp_path)

        repo_secret_statuses = {
            Path(issue.file_path or "").name: issue.file_status for issue in results["repo_secrets"]
        }
        assert repo_secret_statuses["tracked.txt"] == FileStatus.TRACKED.value
        assert repo_secret_statuses["untracked.txt"] == FileStatus.UNTRACKED.value
        assert any(
            issue.code == "ENV_SECRET_DETECTED" and issue.file_status == FileStatus.IGNORED.value
            for issue in results["env_file"]
        )

    def test_release_mode_does_not_block_ignored_env_secret(self, tmp_path: Path) -> None:
        _git(tmp_path, "init")
        (tmp_path / ".gitignore").write_text(
            ".env\n*.pem\n*.key\nid_rsa\nid_ed25519\n", encoding="utf-8"
        )
        (tmp_path / ".env").write_text("API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
        _git(tmp_path, "add", ".gitignore")

        results = run_all_checks(tmp_path, mode=ConfigGuardMode.RELEASE)

        assert has_blocking_issues(results) is True
        assert has_blocking_issues(results, mode=ConfigGuardMode.RELEASE) is False

    def test_release_mode_blocks_untracked_secret(self, tmp_path: Path) -> None:
        _git(tmp_path, "init")
        (tmp_path / ".gitignore").write_text(
            ".env\n*.pem\n*.key\nid_rsa\nid_ed25519\n", encoding="utf-8"
        )
        (tmp_path / "untracked.txt").write_text(
            "API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8"
        )
        _git(tmp_path, "add", ".gitignore")

        results = run_all_checks(tmp_path, mode=ConfigGuardMode.RELEASE)

        assert any(
            issue.file_status == FileStatus.UNTRACKED.value for issue in results["repo_secrets"]
        )
        assert has_blocking_issues(results, mode=ConfigGuardMode.RELEASE) is True


# ---------------------------------------------------------------------------
# has_blocking_issues
# ---------------------------------------------------------------------------


class TestHasBlockingIssues:
    def test_true_when_error_present(self) -> None:
        results = {"check": [GuardrailIssue(code="X", message="bad", severity="ERROR")]}
        assert has_blocking_issues(results) is True

    def test_false_when_only_warnings(self) -> None:
        results = {"check": [GuardrailIssue(code="X", message="warn", severity="WARNING")]}
        assert has_blocking_issues(results) is False

    def test_false_when_empty(self) -> None:
        assert has_blocking_issues({}) is False

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

CLI = [sys.executable, "-m", "modelops_core.cli"]


@pytest.fixture(scope="module")
def help_output() -> str:
    result = subprocess.run(
        CLI + ["--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _extract_commands_section(help_text: str) -> str:
    clean = _strip_ansi(help_text)
    lines = clean.splitlines()
    start: int | None = None
    end: int | None = None
    for i, line in enumerate(lines):
        if start is None and re.search(r"Commands\s*─+", line):
            start = i + 1
        elif start is not None and line.startswith("╰"):
            end = i
            break
    if start is None or end is None:
        raise ValueError("Could not locate Commands table in --help output")
    return "\n".join(lines[start:end])


def _parse_commands(help_text: str) -> set[str]:
    section = _extract_commands_section(help_text)
    commands: set[str] = set()
    for line in section.splitlines():
        # Only match the first column of the table: descriptions start uppercase.
        match = re.match(r"^│\s+([a-z][a-z0-9\-]*)\s{2,}[A-Z]", line)
        if match:
            commands.add(match.group(1))
    return commands


EXPECTED_TOP_LEVEL_COMMANDS = {
    "init",
    "profile-dataset",
    "gaps",
    "import-drive",
    "import-sheet",
    "sources",
    "source-show",
    "infer-model",
    "validate",
    "build-index",
    "clean",
    "index-fresh",
    "health",
    "doctor",
    "scorecard",
    "readiness",
    "object-card",
    "model-summary",
    "owners",
    "analyze",
    "risk-report",
    "gap-report",
    "trace",
    "impact",
    "propose-patch",
    "agent",
    "serve",
    "workbench",
    "mcp",
    "import-model-sheet",
    "import-excel-review",
    "export-model",
    "export-schema",
    "export-sheets",
    "git-bundle",
    "publish-issue",
    "publish-pr",
    "audit-log",
    "usage-report",
    "docs-build",
    "config-guard",
    "diff",
    "search",
    "query",
    "migrate",
    "ai-provider",
    "agent-loop",
    "issue-draft",
    "change-request",
    "notifications",
    "decisions",
    "proposal",
    "assessment",
    "run",
    "diagnostics",
    "review-pack",
    "executive-summary",
    "pilot-preflight",
    "assessment-review",
    "pilot-outcome",
    "demo-bundle",
}

EXPECTED_GROUPS = {
    "agent": {"product-owner", "readiness"},
    "run": {"dataset-readiness", "migration-assessment"},
    "issue-draft": {"create"},
    "change-request": {"create", "list", "show", "update-status", "approve", "reject"},
    "notifications": {"preview", "list"},
    "decisions": {"list", "show", "report"},
    "proposal": {
        "list",
        "show",
        "accept",
        "reject",
        "validate",
        "impact",
        "diff",
        "apply",
        "report",
        "review-bundle",
    },
    "assessment": {"run", "sanitize"},
    "diagnostics": {"export"},
    "review-pack": {"create"},
    "demo-bundle": {"build"},
}


def test_expected_top_level_commands_present(help_output: str) -> None:
    commands = _parse_commands(help_output)
    missing = EXPECTED_TOP_LEVEL_COMMANDS - commands
    assert not missing, f"Missing top-level commands: {missing}"


def test_no_unexpected_top_level_commands(help_output: str) -> None:
    commands = _parse_commands(help_output)
    extra = commands - EXPECTED_TOP_LEVEL_COMMANDS
    assert not extra, f"Unexpected top-level commands: {extra}"


@pytest.mark.parametrize("group, expected", EXPECTED_GROUPS.items())
def test_group_subcommands(group: str, expected: set[str]) -> None:
    result = subprocess.run(
        CLI + [group, "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, result.stderr
    subcommands = _parse_commands(result.stdout)
    missing = expected - subcommands
    extra = subcommands - expected
    assert not missing, f"{group}: missing subcommands {missing}"
    assert not extra, f"{group}: unexpected subcommands {extra}"

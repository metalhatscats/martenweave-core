"""Tests for the Development AI Factory harness (./factory).

The harness is a stdlib-only script at the repository root; tests invoke it via
subprocess so they exercise the real command surface agents rely on.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FACTORY = REPO_ROOT / "factory"

ISSUES_FIXTURE = [
    {
        "number": 12,
        "title": "Fix broken readiness gate",
        "labels": ["bug", "agent-ready"],
        "createdAt": "2026-07-10T09:00:00Z",
    },
    {
        "number": 7,
        "title": "Sync README with new CLI",
        "labels": ["documentation", "agent-ready"],
        "createdAt": "2026-07-01T09:00:00Z",
    },
    {
        "number": 20,
        "title": "Uncategorised chore",
        "labels": ["agent-ready"],
        "createdAt": "2026-06-01T09:00:00Z",
    },
]


def run_factory(*args: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FACTORY), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.fixture
def issues_file(tmp_path: Path) -> Path:
    path = tmp_path / "issues.json"
    path.write_text(json.dumps(ISSUES_FIXTURE), encoding="utf-8")
    return path


def test_help_lists_all_commands() -> None:
    proc = run_factory("--help")
    assert proc.returncode == 0
    for command in ("audit", "plan", "run-next", "review", "validate", "release-check"):
        assert command in proc.stdout


def test_audit_quick_json() -> None:
    proc = run_factory("audit", "--quick", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["command"] == "audit"
    names = {r["name"] for r in payload["results"]}
    assert "git status" in names
    assert "factory docs" in names
    assert payload["ok"] is True


def test_plan_ranks_correctness_first(issues_file: Path) -> None:
    proc = run_factory("plan", "--issues-json", str(issues_file), "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    ranked = payload["data"]["ranked"]
    assert [i["number"] for i in ranked] == [12, 7, 20]
    assert ranked[0]["rank_class"] == "correctness"
    assert ranked[1]["rank_class"] == "docs-drift"
    assert "Recommended next task: #12" in payload["data"]["summary"]


def test_plan_empty_backlog(tmp_path: Path) -> None:
    empty = tmp_path / "empty.json"
    empty.write_text("[]", encoding="utf-8")
    proc = run_factory("plan", "--issues-json", str(empty), "--json")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "No open agent-ready issues" in payload["data"]["summary"]


def test_run_next_brief_assigns_agent(issues_file: Path) -> None:
    proc = run_factory("run-next", "--issues-json", str(issues_file), "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    brief = payload["data"]["brief"]
    assert brief["issue"] == 12
    assert brief["responsible_agent"] == "docs/factory/agents/core-development.md"
    assert "implementation-planning" in brief["skills_to_load"]


def test_review_json_reports_changed_files() -> None:
    proc = run_factory("review", "--json")
    assert proc.returncode in (0, 1), proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert isinstance(payload["data"]["changed_files"], list)
    assert isinstance(payload["data"]["critical_review_checklist"], list)
    assert len(payload["data"]["critical_review_checklist"]) >= 10


def test_review_clean_tree_passes() -> None:
    proc = run_factory("review", "--json")
    payload = json.loads(proc.stdout)
    protected = next(r for r in payload["results"] if r["name"] == "protected paths")
    # No test may leave protected-path changes behind; canonical data edits must
    # always show up as violations instead of passing silently.
    for violation in protected["tail"]:
        assert "model/" in violation or violation.startswith(
            (".github/workflows/", "LICENSE", "NOTICE", ".env", "generated/")
        )


def test_validate_rejects_unknown_gate() -> None:
    proc = run_factory("validate", "--gates", "nonsense", "--json")
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False


def test_validate_docs_gates() -> None:
    proc = run_factory("validate", "--gates", "docs", "--json", timeout=300)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    names = {r["name"] for r in payload["results"]}
    assert "G10 doc commands" in names
    assert "G10 skills structure" in names
    assert payload["ok"] is True

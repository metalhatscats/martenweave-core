"""Meta-tests pinning the installed-wheel first-value smoke contract (issue #625).

The smoke itself (`scripts/release_smoke_wheel_first_value.sh`) builds a wheel,
creates an isolated virtualenv, and installs dependencies from PyPI, so it runs
as release evidence and in CI — not in the default pytest suite.  These cheap
tests keep the script aligned with the acceptance criteria it must prove.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "release_smoke_wheel_first_value.sh"
HELPER = SCRIPT.with_suffix(".py")


def _combined_text() -> str:
    return SCRIPT.read_text(encoding="utf-8") + HELPER.read_text(encoding="utf-8")


def test_first_value_smoke_script_exists_and_is_executable() -> None:
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111
    assert SCRIPT.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")
    assert HELPER.is_file()


def test_first_value_smoke_uses_only_an_installed_wheel_and_temp_dir() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "mktemp -d" in text
    assert "-m build --wheel" in text
    assert "-m venv" in text
    assert "pip install" in text
    # Installs the built wheel only — never a source checkout of the repo.
    assert 'pip install --quiet "${WHEEL}"' in text
    assert 'pip install "${REPO_ROOT}"' not in text
    assert "pip install ." not in text


def test_first_value_smoke_runs_documented_start_path() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "start first_value.csv --no-open --json" in text


def test_first_value_smoke_asserts_every_result_surface() -> None:
    text = _combined_text()
    for marker in (
        # Workspace manifest, profile, report, and unapplied proposal.
        "start_manifest.json",
        "dataset profile",
        "readiness.md",
        "Total gap count",
        "draft_proposal",
        "pending_review",
        # Template discovery/validation.
        "available_templates",
        "--template sap_bp_customer_migration",
        # Report summary and manifest share verdict and finding count.
        "## Verdict:",
        # Local API/Workbench capability result, not just static assets.
        "/api/v1/capabilities",
        "/api/v1/start-result",
        "start_result",
        "load_start_result",
        "workbench",
    ):
        assert marker in text, marker


def test_first_value_smoke_failure_output_names_user_visible_contracts() -> None:
    text = HELPER.read_text(encoding="utf-8")
    assert "FAIL [" in text
    assert "OK   [" in text


def test_first_value_smoke_helper_is_stdlib_only() -> None:
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.split(".")[0])
    imports.discard("__future__")
    # The first-party package under test is imported lazily by the loader check.
    imports.discard("modelops_core")
    assert imports <= set(sys.stdlib_module_names)

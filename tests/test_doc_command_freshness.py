"""Tests for docs command-snippet freshness validation (#467)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_script():
    """Load scripts/validate_doc_commands.py without requiring scripts/__init__.py."""
    repo_root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "validate_doc_commands",
        repo_root / "scripts" / "validate_doc_commands.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_doc_commands"] = module
    spec.loader.exec_module(module)
    return module


validate_doc_commands = _load_script()
_extract_command_path = validate_doc_commands._extract_command_path
_get_valid_commands = validate_doc_commands._get_valid_commands
_find_invalid_snippets = validate_doc_commands._find_invalid_snippets


class TestExtractCommandPath:
    def test_extracts_simple_command(self) -> None:
        valid = {"validate", "build-index", "health"}
        assert _extract_command_path("modelops validate --repo ./x", 0, valid) == "validate"

    def test_extracts_subcommand(self) -> None:
        valid = {"agent", "agent readiness", "agent product-owner"}
        assert (
            _extract_command_path("modelops agent readiness --repo ./x", 0, valid)
            == "agent readiness"
        )

    def test_stops_at_positional_argument(self) -> None:
        valid = {"profile-dataset"}
        assert (
            _extract_command_path(
                "modelops profile-dataset tests/fixtures/sample.csv --repo ./x", 0, valid
            )
            == "profile-dataset"
        )

    def test_unknown_first_token(self) -> None:
        valid = {"validate"}
        assert (
            _extract_command_path("modelops stale-command --repo ./x", 0, valid) == "stale-command"
        )

    def test_ignores_modelops_core_references(self) -> None:
        valid = {"validate"}
        assert (
            _extract_command_path("from modelops_core.config import load_repo_config", 0, valid)
            is None
        )

    def test_ignores_modelops_config_file_references(self) -> None:
        valid = {"validate"}
        assert _extract_command_path("Edit `modelops.config.yaml` to configure", 0, valid) is None


class TestValidCommands:
    def test_real_cli_has_expected_commands(self) -> None:
        commands = _get_valid_commands()
        assert "validate" in commands
        assert "build-index" in commands
        assert "health" in commands
        assert "scorecard" in commands
        assert "agent readiness" in commands
        assert "proposal apply" in commands


class TestScriptIntegration:
    def test_script_reports_invalid_command(self, tmp_path: Path) -> None:
        doc = tmp_path / "bad.md"
        doc.write_text("Run `modelops stale-command --repo ./x`.\n", encoding="utf-8")
        invalid = _find_invalid_snippets(doc, _get_valid_commands())
        assert len(invalid) == 1
        assert invalid[0][2] == "stale-command"

    def test_script_ignores_marked_invalid_command(self, tmp_path: Path) -> None:
        doc = tmp_path / "ignored.md"
        doc.write_text(
            "<!-- modelops-freshness-ignore -->\nRun `modelops stale-command --repo ./x`.\n",
            encoding="utf-8",
        )
        invalid = _find_invalid_snippets(doc, _get_valid_commands())
        assert len(invalid) == 0

    def test_script_ignores_global_marker(self, tmp_path: Path) -> None:
        doc = tmp_path / "ignored.md"
        doc.write_text(
            "<!-- modelops-freshness-ignore: all -->\n\nRun `modelops stale-command --repo ./x`.\n",
            encoding="utf-8",
        )
        invalid = _find_invalid_snippets(doc, _get_valid_commands())
        assert len(invalid) == 0

    def test_script_accepts_valid_command(self, tmp_path: Path) -> None:
        doc = tmp_path / "good.md"
        doc.write_text("Run `modelops validate --repo ./x`.\n", encoding="utf-8")
        invalid = _find_invalid_snippets(doc, _get_valid_commands())
        assert len(invalid) == 0

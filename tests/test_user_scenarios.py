"""Tests for the user scenario catalog (#496)."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def scenario_doc() -> Path:
    """Path to the authoritative scenario catalog."""
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "docs" / "product" / "USER_SCENARIOS.md"


class TestUserScenarioCatalog:
    def test_catalog_exists(self, scenario_doc: Path) -> None:
        assert scenario_doc.exists()

    def test_catalog_contains_required_sections(self, scenario_doc: Path) -> None:
        text = scenario_doc.read_text(encoding="utf-8")
        required = [
            "# Martenweave User Scenario Catalog",
            "## Status legend",
            "## Scenario catalog",
            "## Coverage matrix",
            "## First five pilot-ready scenarios",
            "## UI screen-to-scenario mapping",
        ]
        for heading in required:
            assert heading in text, f"Missing section: {heading}"

    def test_catalog_contains_all_twelve_scenarios(self, scenario_doc: Path) -> None:
        text = scenario_doc.read_text(encoding="utf-8")
        for n in range(1, 13):
            assert f"S{n:02d}" in text, f"Missing scenario S{n:02d}"

    def test_status_legend_lists_all_statuses(self, scenario_doc: Path) -> None:
        text = scenario_doc.read_text(encoding="utf-8")
        legend_start = text.index("## Status legend")
        legend_end = text.index("## Scenario catalog")
        legend = text[legend_start:legend_end]
        for status in ("complete", "partial", "mocked", "missing"):
            assert f"`{status}`" in legend

    def test_first_five_pilot_ready_scenarios_listed(self, scenario_doc: Path) -> None:
        text = scenario_doc.read_text(encoding="utf-8")
        section_start = text.index("## First five pilot-ready scenarios")
        section = text[section_start:]
        expected = ["S01", "S04", "S05", "S08", "S03"]
        for scenario in expected:
            assert scenario in section, f"Missing pilot scenario {scenario}"

    def test_matrix_links_every_ui_route(self, scenario_doc: Path) -> None:
        text = scenario_doc.read_text(encoding="utf-8")
        matrix_start = text.index("## UI screen-to-scenario mapping")
        matrix = text[matrix_start:]
        routes = [
            "`home`",
            "`models`",
            "`object`",
            "`lineage`",
            "`gaps`",
            "`proposals`",
            "`proposal`",
            "`reports`",
            "`changelog`",
            "`settings`",
        ]
        for route in routes:
            assert route in matrix, f"Missing UI route {route}"

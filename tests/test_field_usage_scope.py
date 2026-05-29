"""Tests for field usage and scope metadata (#91)."""

from __future__ import annotations

from pathlib import Path

from modelops_core.repository.parser import parse_file
from modelops_core.validation.pipeline import validate_objects


class TestAttributeUsageSchema:
    def test_usage_type_and_scope_parsed(self, tmp_path: Path) -> None:
        obj_file = tmp_path / "USE-TEST-01.md"
        obj_file.write_text(
            "---\n"
            "id: USE-TEST-01\n"
            "type: AttributeUsage\n"
            "status: draft\n"
            "name: Test Usage\n"
            "attribute: ATTR-TEST-01\n"
            "usage_type: primary\n"
            "scope: global\n"
            "---\n\n"
            "# Test\n",
            encoding="utf-8",
        )
        parsed = parse_file(obj_file)
        assert parsed.frontmatter is not None
        assert parsed.frontmatter.get("usage_type") == "primary"
        assert parsed.frontmatter.get("scope") == "global"


class TestAttributeUsageValidation:
    def test_warns_when_usage_type_missing(self, tmp_path: Path) -> None:
        obj_file = tmp_path / "USE-TEST-02.md"
        obj_file.write_text(
            "---\n"
            "id: USE-TEST-02\n"
            "type: AttributeUsage\n"
            "status: active\n"
            "name: Test Usage Missing Type\n"
            "attribute: ATTR-TEST-01\n"
            "---\n\n"
            "# Test\n",
            encoding="utf-8",
        )
        parsed = parse_file(obj_file)
        summary = validate_objects([parsed])
        codes = {r.code for r in summary.results}
        assert "ATTRIBUTE_USAGE_MISSING_TYPE" in codes

    def test_no_warning_when_usage_type_present(self, tmp_path: Path) -> None:
        obj_file = tmp_path / "USE-TEST-03.md"
        obj_file.write_text(
            "---\n"
            "id: USE-TEST-03\n"
            "type: AttributeUsage\n"
            "status: active\n"
            "name: Test Usage With Type\n"
            "attribute: ATTR-TEST-01\n"
            "usage_type: secondary\n"
            "---\n\n"
            "# Test\n",
            encoding="utf-8",
        )
        parsed = parse_file(obj_file)
        summary = validate_objects([parsed])
        codes = {r.code for r in summary.results}
        assert "ATTRIBUTE_USAGE_MISSING_TYPE" not in codes

    def test_no_warning_for_inactive_usage(self, tmp_path: Path) -> None:
        obj_file = tmp_path / "USE-TEST-04.md"
        obj_file.write_text(
            "---\n"
            "id: USE-TEST-04\n"
            "type: AttributeUsage\n"
            "status: retired\n"
            "name: Retired Usage\n"
            "attribute: ATTR-TEST-01\n"
            "---\n\n"
            "# Test\n",
            encoding="utf-8",
        )
        parsed = parse_file(obj_file)
        summary = validate_objects([parsed])
        codes = {r.code for r in summary.results}
        assert "ATTRIBUTE_USAGE_MISSING_TYPE" not in codes

"""Tests for ValueList and ValueMapping governance validation."""

from __future__ import annotations

from pathlib import Path

from modelops_core.validation.pipeline import validate_objects
from modelops_core.validation.result import ValidationSeverity


def _make_obj(source_path: Path, frontmatter: dict) -> object:
    from modelops_core.repository.parser import ParsedObject

    return ParsedObject(
        source_path=str(source_path),
        content_hash="abc",
        frontmatter=frontmatter,
        body="",
        parser_error=None,
    )


def test_lov_empty_warning() -> None:
    obj = _make_obj(
        Path("VLIST-EMPTY.md"),
        {
            "id": "VLIST-EMPTY",
            "type": "ValueList",
            "status": "active",
            "name": "Empty List",
            "entries": [],
        },
    )
    summary = validate_objects([obj])
    codes = {r.code for r in summary.results}
    assert "LOV_EMPTY" in codes
    assert any(
        r.code == "LOV_EMPTY" and r.severity == ValidationSeverity.WARNING for r in summary.results
    )


def test_lov_no_entries_field_warning() -> None:
    obj = _make_obj(
        Path("VLIST-NO-ENTRIES.md"),
        {
            "id": "VLIST-NO-ENTRIES",
            "type": "ValueList",
            "status": "active",
            "name": "No Entries",
        },
    )
    summary = validate_objects([obj])
    codes = {r.code for r in summary.results}
    assert "LOV_EMPTY" in codes


def test_lov_with_entries_no_warning() -> None:
    obj = _make_obj(
        Path("VLIST-OK.md"),
        {
            "id": "VLIST-OK",
            "type": "ValueList",
            "status": "active",
            "name": "OK List",
            "entries": [
                {"code": "A", "label": "Alpha"},
            ],
        },
    )
    summary = validate_objects([obj])
    codes = {r.code for r in summary.results}
    assert "LOV_EMPTY" not in codes


def test_value_mapping_empty_warning() -> None:
    obj = _make_obj(
        Path("VMAP-EMPTY.md"),
        {
            "id": "VMAP-EMPTY",
            "type": "ValueMapping",
            "status": "active",
            "name": "Empty Mapping",
            "entries": [],
        },
    )
    summary = validate_objects([obj])
    codes = {r.code for r in summary.results}
    assert "VALUE_MAPPING_EMPTY" in codes


def test_value_mapping_invalid_source_code() -> None:
    vl = _make_obj(
        Path("VLIST-SRC.md"),
        {
            "id": "VLIST-SRC",
            "type": "ValueList",
            "status": "active",
            "name": "Source",
            "entries": [{"code": "A"}],
        },
    )
    vm = _make_obj(
        Path("VMAP-BAD.md"),
        {
            "id": "VMAP-BAD",
            "type": "ValueMapping",
            "status": "active",
            "name": "Bad Mapping",
            "source_value_list": "VLIST-SRC",
            "target_value_list": "VLIST-TGT",
            "entries": [
                {"source_code": "X", "target_code": "Y"},
            ],
        },
    )
    summary = validate_objects([vl, vm])
    codes = {r.code for r in summary.results}
    assert "VALUE_MAPPING_SOURCE_CODE_INVALID" in codes
    assert "VALUE_MAPPING_TARGET_CODE_INVALID" in codes
    assert any(
        r.code == "VALUE_MAPPING_SOURCE_CODE_INVALID" and r.severity == ValidationSeverity.ERROR
        for r in summary.results
    )


def test_value_mapping_valid_codes() -> None:
    vl_src = _make_obj(
        Path("VLIST-SRC.md"),
        {
            "id": "VLIST-SRC",
            "type": "ValueList",
            "status": "active",
            "name": "Source",
            "entries": [{"code": "A"}, {"code": "B"}],
        },
    )
    vl_tgt = _make_obj(
        Path("VLIST-TGT.md"),
        {
            "id": "VLIST-TGT",
            "type": "ValueList",
            "status": "active",
            "name": "Target",
            "entries": [{"code": "1"}, {"code": "2"}],
        },
    )
    vm = _make_obj(
        Path("VMAP-OK.md"),
        {
            "id": "VMAP-OK",
            "type": "ValueMapping",
            "status": "active",
            "name": "OK Mapping",
            "source_value_list": "VLIST-SRC",
            "target_value_list": "VLIST-TGT",
            "entries": [
                {"source_code": "A", "target_code": "1"},
                {"source_code": "B", "target_code": "2"},
            ],
        },
    )
    summary = validate_objects([vl_src, vl_tgt, vm])
    codes = {r.code for r in summary.results}
    assert "VALUE_MAPPING_SOURCE_CODE_INVALID" not in codes
    assert "VALUE_MAPPING_TARGET_CODE_INVALID" not in codes


def test_lov_ownership_warning() -> None:
    obj = _make_obj(
        Path("VLIST-NO-OWNER.md"),
        {
            "id": "VLIST-NO-OWNER",
            "type": "ValueList",
            "status": "active",
            "name": "No Owner",
            "entries": [{"code": "A"}],
        },
    )
    summary = validate_objects([obj])
    codes = {r.code for r in summary.results}
    assert "OWNERSHIP_MISSING" in codes


def test_value_list_parent_reference_valid() -> None:
    parent = _make_obj(
        Path("VLIST-PARENT.md"),
        {
            "id": "VLIST-PARENT",
            "type": "ValueList",
            "status": "active",
            "name": "Parent",
            "entries": [{"code": "A"}],
        },
    )
    child = _make_obj(
        Path("VLIST-CHILD.md"),
        {
            "id": "VLIST-CHILD",
            "type": "ValueList",
            "status": "active",
            "name": "Child",
            "parent_value_list": "VLIST-PARENT",
            "entries": [{"code": "A"}],
        },
    )
    summary = validate_objects([parent, child])
    codes = {r.code for r in summary.results}
    assert "REFERENCE_BROKEN" not in codes


def test_value_list_parent_reference_broken() -> None:
    child = _make_obj(
        Path("VLIST-CHILD.md"),
        {
            "id": "VLIST-CHILD",
            "type": "ValueList",
            "status": "active",
            "name": "Child",
            "parent_value_list": "VLIST-MISSING",
            "entries": [{"code": "A"}],
        },
    )
    summary = validate_objects([child])
    codes = {r.code for r in summary.results}
    assert "REFERENCE_BROKEN" in codes


def test_lov_duplicate_code_error() -> None:
    obj = _make_obj(
        Path("VLIST-DUP.md"),
        {
            "id": "VLIST-DUP",
            "type": "ValueList",
            "status": "active",
            "name": "Duplicate Code",
            "entries": [
                {"code": "01", "label": "Wholesale"},
                {"code": "01", "label": "Duplicate Wholesale"},
            ],
        },
    )
    summary = validate_objects([obj])
    codes = {r.code for r in summary.results}
    assert "LOV_DUPLICATE_CODE" in codes
    assert any(
        r.code == "LOV_DUPLICATE_CODE" and r.severity == ValidationSeverity.ERROR
        for r in summary.results
    )


def test_lov_unique_codes_no_duplicate_error() -> None:
    obj = _make_obj(
        Path("VLIST-UNIQUE.md"),
        {
            "id": "VLIST-UNIQUE",
            "type": "ValueList",
            "status": "active",
            "name": "Unique Codes",
            "entries": [
                {"code": "01", "label": "Wholesale"},
                {"code": "02", "label": "Retail"},
            ],
        },
    )
    summary = validate_objects([obj])
    codes = {r.code for r in summary.results}
    assert "LOV_DUPLICATE_CODE" not in codes

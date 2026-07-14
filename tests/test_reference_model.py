"""Tests for the SAP BP/Customer/Vendor reference model example."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.repository.parser import parse_file
from modelops_core.repository.scanner import scan_repository
from modelops_core.validation.pipeline import validate_objects

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = REPO_ROOT / "examples" / "sap_bp_customer_vendor_reference" / "model"
REPO_DIR = REPO_ROOT / "examples" / "sap_bp_customer_vendor_reference"


def _count_by_type(type_id: str) -> int:
    return sum(1 for p in MODEL_DIR.glob("*.md") if f"type: {type_id}" in p.read_text())


def test_reference_model_directory_exists() -> None:
    assert MODEL_DIR.exists(), f"Expected model directory at {MODEL_DIR}"
    assert (REPO_DIR / "modelops.config.yaml").exists()


def test_reference_model_has_minimum_objects() -> None:
    files = list(MODEL_DIR.glob("*.md"))
    assert len(files) >= 300, f"Expected >= 300 canonical files, got {len(files)}"


def test_reference_model_has_minimum_field_endpoints() -> None:
    count = _count_by_type("FieldEndpoint")
    assert count >= 40, f"Expected >= 40 FieldEndpoint files, got {count}"


def test_reference_model_has_minimum_decisions() -> None:
    count = _count_by_type("Decision")
    assert count >= 20, f"Expected >= 20 Decision files, got {count}"


def test_reference_model_has_minimum_issues() -> None:
    count = _count_by_type("Issue")
    assert count >= 20, f"Expected >= 20 Issue files, got {count}"


def test_reference_model_has_minimum_value_lists_and_mappings() -> None:
    count = _count_by_type("ValueList") + _count_by_type("ValueMapping")
    assert count >= 10, f"Expected >= 10 ValueList + ValueMapping files, got {count}"


@pytest.mark.slow
def test_reference_model_passes_validation() -> None:
    paths = scan_repository(str(MODEL_DIR))
    objects = [parse_file(p) for p in paths]
    summary = validate_objects(objects, enabled_domain_packs=["sap"])
    assert summary.is_valid, f"Validation failed: {summary.error_count} errors"

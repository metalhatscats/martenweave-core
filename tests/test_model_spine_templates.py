"""Tests for model spine templates."""

from __future__ import annotations

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.repository.parser import parse_file
from modelops_core.repository.scanner import scan_repository
from modelops_core.validation import validate_objects

runner = CliRunner()
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "model_spines"


def test_business_partner_template_validates() -> None:
    model_path = TEMPLATES_DIR / "business_partner" / "model"
    files = scan_repository(model_path)
    parsed = [parse_file(f) for f in files]
    summary = validate_objects(parsed)
    assert summary.is_valid, summary.results


def test_generic_large_object_template_validates() -> None:
    model_path = TEMPLATES_DIR / "generic_large_object" / "model"
    files = scan_repository(model_path)
    parsed = [parse_file(f) for f in files]
    summary = validate_objects(parsed)
    assert summary.is_valid, summary.results


def test_business_partner_has_expected_structure() -> None:
    model_path = TEMPLATES_DIR / "business_partner" / "model"
    files = scan_repository(model_path)
    parsed = [parse_file(f) for f in files]

    ids = {p.frontmatter.get("id") for p in parsed}
    assert "DOMAIN-BP" in ids
    assert "ENTITY-BUSINESS-PARTNER" in ids
    assert "ENTITY-BP-CENTRAL" in ids
    assert "ENTITY-BP-CUSTOMER" in ids
    assert "ENTITY-BP-SUPPLIER" in ids
    assert "CTX-BP-CENTRAL" in ids
    assert "CTX-BP-CUSTOMER" in ids
    assert "CTX-BP-CUSTOMER-SALES-AREA" in ids
    assert "CTX-BP-COMPANY-CODE" in ids
    assert "CTX-BP-CONTACT-PERSON" in ids
    assert "CTX-BP-ADDRESS" in ids
    assert "CTX-BP-SUPPLIER" in ids
    assert "CTX-BP-PURCHASING" in ids
    assert "CTX-BP-BANK" in ids
    assert "CTX-BP-TAX" in ids

    # Parent hierarchy
    central = next(p for p in parsed if p.frontmatter.get("id") == "ENTITY-BP-CENTRAL")
    assert central.frontmatter.get("parent_entity") == "ENTITY-BUSINESS-PARTNER"


def test_generic_template_has_expected_structure() -> None:
    model_path = TEMPLATES_DIR / "generic_large_object" / "model"
    files = scan_repository(model_path)
    parsed = [parse_file(f) for f in files]

    ids = {p.frontmatter.get("id") for p in parsed}
    assert "DOMAIN-GENERIC" in ids
    assert "ENTITY-GENERIC-OBJECT" in ids
    assert "ENTITY-GENERIC-PERSPECTIVE-A" in ids
    assert "ENTITY-GENERIC-PERSPECTIVE-B" in ids
    assert "CTX-GENERIC-PERSPECTIVE-A" in ids
    assert "CTX-GENERIC-PERSPECTIVE-B" in ids

    # No SAP-specific references
    for p in parsed:
        fm = p.frontmatter or {}
        assert not fm.get("sap_table")
        assert not fm.get("sap_field")


def test_init_with_business_partner_template() -> None:
    with tempfile.TemporaryDirectory() as td:
        result = runner.invoke(app, ["init", td, "--template", "business_partner"])
        assert result.exit_code == 0
        model_dir = Path(td) / "model"
        assert (model_dir / "DOMAIN-BP.md").exists()
        assert (model_dir / "ENTITY-BUSINESS-PARTNER.md").exists()


def test_init_with_generic_template() -> None:
    with tempfile.TemporaryDirectory() as td:
        result = runner.invoke(app, ["init", td, "--template", "generic_large_object"])
        assert result.exit_code == 0
        model_dir = Path(td) / "model"
        assert (model_dir / "DOMAIN-GENERIC.md").exists()
        assert (model_dir / "ENTITY-GENERIC-OBJECT.md").exists()


def test_init_with_unknown_template_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        result = runner.invoke(app, ["init", td, "--template", "nonexistent"])
        assert result.exit_code == 1
        assert "Template not found" in result.output

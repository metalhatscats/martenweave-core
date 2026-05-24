"""Tests for domain pack architecture and generic validation."""

from __future__ import annotations

from pathlib import Path

from modelops_core.domain_packs import get_domain_packs
from modelops_core.domain_packs.sap import SAPDomainPack
from modelops_core.repository import ParsedObject
from modelops_core.validation import validate_objects


def test_generic_validation_runs_without_domain_packs(temp_model_dir: Path) -> None:
    """Generic models validate without requiring SAP-specific metadata."""
    from modelops_core.repository import parse_file, scan_repository

    files = scan_repository(temp_model_dir)
    parsed_objects = [parse_file(f) for f in files]

    # Without domain packs, validation should still pass for generic objects
    summary = validate_objects(parsed_objects)
    assert summary.is_valid

    # With SAP pack enabled, generic objects still pass (no SAP fields)
    summary_with_sap = validate_objects(parsed_objects, enabled_domain_packs=["sap"])
    assert summary_with_sap.is_valid


def test_sap_domain_pack_detects_context_errors() -> None:
    """SAP domain pack catches mismatched context categories."""
    ctx = ParsedObject(
        source_path="CTX.md",
        content_hash="x",
        frontmatter={
            "id": "CTX-TEST",
            "type": "EntityContext",
            "status": "active",
            "context_category": "wrong_category",
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="FEP.md",
        content_hash="x",
        frontmatter={
            "id": "FEP-TEST",
            "type": "FieldEndpoint",
            "status": "active",
            "endpoint_type": "sap_table_field",
            "sap_table": "KNVV",
            "entity_context": "CTX-TEST",
        },
        body=None,
        parser_error=None,
    )

    pack = SAPDomainPack()
    results = pack.validate([ctx, fep], {})
    assert any(r["code"] == "SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA" for r in results)


def test_get_domain_packs_returns_enabled_only() -> None:
    assert get_domain_packs([]) == []
    assert get_domain_packs(None) == []
    packs = get_domain_packs(["sap"])
    assert len(packs) == 1
    assert isinstance(packs[0], SAPDomainPack)


def test_get_domain_packs_ignores_unknown() -> None:
    packs = get_domain_packs(["sap", "nonexistent"])
    assert len(packs) == 1

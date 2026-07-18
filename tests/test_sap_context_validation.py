"""Tests for SAP context validation."""

from __future__ import annotations

from modelops_core.repository.parser import ParsedObject
from modelops_core.validation import validate_objects


def test_knvv_requires_sales_area() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-CUSTOMER-SALES-AREA",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "customer_sales_area",
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-KNVV-KDGRP",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "KNVV",
            "entity_context": "CTX-CUSTOMER-SALES-AREA",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert summary.is_valid


def test_knvv_wrong_context_category() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-WRONG",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "customer_company_code",  # Wrong for KNVV
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-KNVV-KDGRP",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "KNVV",
            "entity_context": "CTX-WRONG",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert not summary.is_valid
    assert any(r.code == "SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA" for r in summary.results)


def test_knb1_requires_company_code() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-COMPANY-CODE",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "customer_company_code",
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-KNB1-BUKRS",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "KNB1",
            "entity_context": "CTX-COMPANY-CODE",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert summary.is_valid


def test_lfa1_requires_vendor_general() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-VENDOR-GENERAL",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "vendor_general",
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-LFA1-NAME1",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "LFA1",
            "entity_context": "CTX-VENDOR-GENERAL",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert summary.is_valid


def test_lfa1_wrong_context_category() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-WRONG",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "vendor_company_code",
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-LFA1-NAME1",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "LFA1",
            "entity_context": "CTX-WRONG",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert not summary.is_valid
    assert any(r.code == "SAP_CONTEXT_LFA1_REQUIRES_VENDOR_GENERAL" for r in summary.results)


def test_lfb1_requires_vendor_company_code() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-VENDOR-COMPANY",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "vendor_company_code",
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-LFB1-AKONT",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "LFB1",
            "entity_context": "CTX-VENDOR-COMPANY",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert summary.is_valid


def test_lfm1_requires_vendor_purchasing_org() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-VENDOR-PURCHASING",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "vendor_purchasing_org",
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-LFM1-ZTERM",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "LFM1",
            "entity_context": "CTX-VENDOR-PURCHASING",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert summary.is_valid


def test_mara_requires_material_general() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-MATERIAL-GENERAL",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "material_general",
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-MARA-MTART",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "MARA",
            "entity_context": "CTX-MATERIAL-GENERAL",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert summary.is_valid


def test_mara_wrong_context_category() -> None:
    ctx = ParsedObject(
        source_path="ctx.md",
        content_hash="abc",
        frontmatter={
            "id": "CTX-WRONG",
            "type": "EntityContext",
            "status": "draft",
            "context_category": "material_plant",  # Wrong for MARA
        },
        body=None,
        parser_error=None,
    )
    fep = ParsedObject(
        source_path="fep.md",
        content_hash="abc",
        frontmatter={
            "id": "FEP-S4-MARA-MTART",
            "type": "FieldEndpoint",
            "status": "draft",
            "endpoint_type": "sap_table_field",
            "sap_table": "MARA",
            "entity_context": "CTX-WRONG",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
    assert not summary.is_valid
    assert any(r.code == "SAP_CONTEXT_MARA_REQUIRES_MATERIAL_GENERAL" for r in summary.results)


def test_extended_table_rules_accept_matching_contexts() -> None:
    cases = [
        ("MARC", "material_plant"),
        ("VBAK", "sales_order_header"),
        ("VBAP", "sales_order_item"),
        ("EKKO", "purchase_order_header"),
        ("EKPO", "purchase_order_item"),
        ("LIKP", "delivery_header"),
        ("LIPS", "delivery_item"),
        ("BKPF", "accounting_document_header"),
        ("BSEG", "accounting_document_item"),
    ]
    for sap_table, context_category in cases:
        ctx = ParsedObject(
            source_path="ctx.md",
            content_hash="abc",
            frontmatter={
                "id": f"CTX-{context_category.upper().replace('_', '-')}",
                "type": "EntityContext",
                "status": "draft",
                "context_category": context_category,
            },
            body=None,
            parser_error=None,
        )
        fep = ParsedObject(
            source_path="fep.md",
            content_hash="abc",
            frontmatter={
                "id": f"FEP-S4-{sap_table}-FIELD",
                "type": "FieldEndpoint",
                "status": "draft",
                "endpoint_type": "sap_table_field",
                "sap_table": sap_table,
                "entity_context": ctx.frontmatter["id"],
            },
            body=None,
            parser_error=None,
        )
        summary = validate_objects([ctx, fep], enabled_domain_packs=["sap"])
        assert summary.is_valid, f"{sap_table} with {context_category} should be valid"

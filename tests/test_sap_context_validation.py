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
    summary = validate_objects([ctx, fep])
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
    summary = validate_objects([ctx, fep])
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
    summary = validate_objects([ctx, fep])
    assert summary.is_valid

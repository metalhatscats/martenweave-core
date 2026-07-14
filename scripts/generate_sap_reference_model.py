"""Deterministic generator for the SAP BP/Customer/Vendor reference model.

Usage:
    python scripts/generate_sap_reference_model.py

The script regenerates the canonical files under
``examples/sap_bp_customer_vendor_reference/model/`` from scratch.
All IDs, object counts, and content are hard-coded so every run is identical.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = REPO_ROOT / "examples" / "sap_bp_customer_vendor_reference" / "model"
CONFIG_PATH = REPO_ROOT / "examples" / "sap_bp_customer_vendor_reference" / "modelops.config.yaml"

DOMAIN_ID = "DOMAIN-SAP-BP-CUSTOMER-VENDOR"
SCHEMA_VERSION = "1.0"
CREATED_AT = "2024-01-15T10:00:00+00:00"


def _dump_yaml(frontmatter: dict[str, Any]) -> str:
    return yaml.dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )


def write_canonical(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    """Write a Markdown file with YAML frontmatter."""
    yaml_text = _dump_yaml(frontmatter).rstrip()
    content = f"---\n{yaml_text}\n---\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def safe_id(text: str) -> str:
    """Turn a human-readable string into a valid canonical ID."""
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
    text = text.upper().replace(" ", "-").replace("/", "-").replace("_", "-")
    result = []
    prev_hyphen = True  # collapse leading duplicates
    for ch in text:
        if ch in allowed:
            if ch == "-":
                if not prev_hyphen:
                    result.append(ch)
                    prev_hyphen = True
            else:
                result.append(ch)
                prev_hyphen = False
    cleaned = "".join(result).strip("-")
    # Strip repeated hyphens in the middle just in case.
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned


def fep_id(table: str, field: str, prefix: str = "S4") -> str:
    return f"FEP-{prefix}-{table}-{safe_id(field)}"


def attr_id(name: str) -> str:
    return f"ATTR-{safe_id(name)}"


def use_id(name: str, context: str) -> str:
    return f"USE-{safe_id(name)}-{safe_id(context.split('-')[-1])}"


def map_id(source: str, target: str) -> str:
    return f"MAP-{safe_id(source)}-TO-{safe_id(target)}"


def main() -> None:
    # Wipe and recreate the model directory.
    if MODEL_DIR.exists():
        shutil.rmtree(MODEL_DIR)
    MODEL_DIR.mkdir(parents=True)

    # ------------------------------------------------------------------
    # Shared reference objects
    # ------------------------------------------------------------------
    write_canonical(
        MODEL_DIR / f"{DOMAIN_ID}.md",
        {
            "id": DOMAIN_ID,
            "type": "MasterDataDomain",
            "status": "active",
            "schema_version": SCHEMA_VERSION,
            "name": "SAP BP / Customer / Vendor",
            "description": (
                "Reference model covering SAP Business Partner, Customer, and Vendor "
                "master data migration to S/4HANA."
            ),
        },
        f"# {DOMAIN_ID}\n\n"
        "Canonical reference domain for SAP Business Partner / Customer / Vendor master data.",
    )

    systems = [
        ("SYS-S4HANA", "SAP S/4HANA", "erp", "Target S/4HANA system for BP, Customer and Vendor."),
        (
            "SYS-LEGACY-ERP",
            "Legacy ERP",
            "legacy",
            "Legacy ERP holding historical customer/vendor data.",
        ),
        ("SYS-LEGACY-CRM", "Legacy CRM", "crm", "Legacy CRM with customer relationship data."),
        (
            "SYS-LEGACY-VENDOR-PORTAL",
            "Legacy Vendor Portal",
            "portal",
            "Legacy vendor self-service portal.",
        ),
        (
            "SYS-MIGRATION-FILE",
            "Migration File",
            "file",
            "Flat-file staging area for migration loads.",
        ),
    ]
    for sys_id, name, sys_type, description in systems:
        write_canonical(
            MODEL_DIR / f"{sys_id}.md",
            {
                "id": sys_id,
                "type": "System",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": name,
                "system_type": sys_type,
                "domain": DOMAIN_ID,
                "description": description,
            },
            f"# {name}\n\n{description}",
        )

    persons = [
        (
            "PERSON-BUSINESS-OWNER",
            "Alex Business Owner",
            "Business Owner",
            "alex.owner@example.com",
        ),
        ("PERSON-DATA-STEWARD", "Dana Data Steward", "Data Steward", "dana.steward@example.com"),
        (
            "PERSON-TECHNICAL-OWNER",
            "Taylor Technical Owner",
            "Technical Owner",
            "taylor.tech@example.com",
        ),
        ("PERSON-SAP-ARCHITECT", "Sam SAP Architect", "Solution Architect", "sam.arch@example.com"),
        (
            "PERSON-MIGRATION-LEAD",
            "Morgan Migration Lead",
            "Migration Lead",
            "morgan.mig@example.com",
        ),
        ("PERSON-FINANCE-OWNER", "Finn Finance Owner", "Finance Owner", "finn.finance@example.com"),
        ("PERSON-SALES-OWNER", "Sasha Sales Owner", "Sales Owner", "sasha.sales@example.com"),
        (
            "PERSON-PURCHASING-OWNER",
            "Pat Purchasing Owner",
            "Purchasing Owner",
            "pat.procure@example.com",
        ),
    ]
    for p_id, name, role, email in persons:
        write_canonical(
            MODEL_DIR / f"{p_id}.md",
            {
                "id": p_id,
                "type": "Person",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": name,
                "role": role,
                "email": email,
                "domain": DOMAIN_ID,
            },
            f"# {name}\n\n{role} for the SAP BP/Customer/Vendor reference model.",
        )

    write_canonical(
        MODEL_DIR / "MIGOBJ-SAP-BP-CUSTOMER-VENDOR.md",
        {
            "id": "MIGOBJ-SAP-BP-CUSTOMER-VENDOR",
            "type": "MigrationObject",
            "status": "active",
            "schema_version": SCHEMA_VERSION,
            "name": "SAP BP / Customer / Vendor Migration",
            "domain": DOMAIN_ID,
            "description": (
                "End-to-end migration of BP, Customer and Vendor master data to S/4HANA."
            ),
        },
        "# SAP BP / Customer / Vendor Migration\n\n"
        "Migration scope covering BP central, customer role, vendor role, contacts, "
        "bank and tax data.",
    )

    # ------------------------------------------------------------------
    # Business entities and contexts
    # ------------------------------------------------------------------
    entities = [
        ("ENTITY-BP-CENTRAL", "BP Central", "Central Business Partner entity."),
        ("ENTITY-CUSTOMER-CENTRAL", "Customer Central", "Customer general data entity."),
        (
            "ENTITY-CUSTOMER-COMPANY-CODE",
            "Customer Company Code",
            "Customer company-code-dependent data.",
        ),
        (
            "ENTITY-CUSTOMER-SALES-AREA",
            "Customer Sales Area",
            "Customer sales-area-dependent data.",
        ),
        (
            "ENTITY-CUSTOMER-PARTNER-FUNCTION",
            "Customer Partner Function",
            "Customer partner function data.",
        ),
        ("ENTITY-CUSTOMER-CONTACT", "Customer Contact", "Customer contact person data."),
        ("ENTITY-CUSTOMER-BANK", "Customer Bank Details", "Customer bank account data."),
        ("ENTITY-CUSTOMER-TAX", "Customer Tax Numbers", "Customer tax number data."),
        ("ENTITY-VENDOR-CENTRAL", "Vendor Central", "Vendor general data entity."),
        (
            "ENTITY-VENDOR-COMPANY-CODE",
            "Vendor Company Code",
            "Vendor company-code-dependent data.",
        ),
        (
            "ENTITY-VENDOR-PURCHASING-ORG",
            "Vendor Purchasing Organization",
            "Vendor purchasing-org-dependent data.",
        ),
        ("ENTITY-VENDOR-CONTACT", "Vendor Contact", "Vendor contact person data."),
        ("ENTITY-VENDOR-BANK", "Vendor Bank Details", "Vendor bank account data."),
        ("ENTITY-VENDOR-TAX", "Vendor Tax Numbers", "Vendor tax number data."),
        ("ENTITY-ADDRESS", "Address", "Shared address data."),
        ("ENTITY-PAYMENT-TERMS", "Payment Terms", "Shared payment terms entity."),
        ("ENTITY-ACCOUNT-GROUP", "Account Group", "Shared account group entity."),
    ]
    for e_id, name, description in entities:
        write_canonical(
            MODEL_DIR / f"{e_id}.md",
            {
                "id": e_id,
                "type": "BusinessEntity",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": name,
                "domain": DOMAIN_ID,
                "business_owner": "PERSON-BUSINESS-OWNER",
                "data_steward": "PERSON-DATA-STEWARD",
                "description": description,
            },
            f"# {name}\n\n{description}",
        )

    contexts = [
        (
            "CTX-BP-CENTRAL-S4",
            "S/4HANA BP Central",
            "ENTITY-BP-CENTRAL",
            "SYS-S4HANA",
            "BUT000",
            "bp_central",
            "PARTNER",
        ),
        (
            "CTX-CUSTOMER-CENTRAL-S4",
            "S/4HANA Customer Central",
            "ENTITY-CUSTOMER-CENTRAL",
            "SYS-S4HANA",
            "KNA1",
            "customer_general",
            "KUNNR",
        ),
        (
            "CTX-CUSTOMER-COMPANY-CODE-S4",
            "S/4HANA Customer Company Code",
            "ENTITY-CUSTOMER-COMPANY-CODE",
            "SYS-S4HANA",
            "KNB1",
            "customer_company_code",
            "KUNNR + BUKRS",
        ),
        (
            "CTX-CUSTOMER-SALES-AREA-S4",
            "S/4HANA Customer Sales Area",
            "ENTITY-CUSTOMER-SALES-AREA",
            "SYS-S4HANA",
            "KNVV",
            "customer_sales_area",
            "KUNNR + VKORG + VTWEG + SPART",
        ),
        (
            "CTX-CUSTOMER-PARTNER-FUNCTION-S4",
            "S/4HANA Customer Partner Function",
            "ENTITY-CUSTOMER-PARTNER-FUNCTION",
            "SYS-S4HANA",
            "KNVP",
            "customer_partner_function",
            "KUNNR + VKORG + VTWEG + SPART + PARVW",
        ),
        (
            "CTX-CUSTOMER-CONTACT-S4",
            "S/4HANA Customer Contact",
            "ENTITY-CUSTOMER-CONTACT",
            "SYS-S4HANA",
            "KNVK",
            "customer_contact",
            "PARNR",
        ),
        (
            "CTX-CUSTOMER-BANK-S4",
            "S/4HANA Customer Bank",
            "ENTITY-CUSTOMER-BANK",
            "SYS-S4HANA",
            "KNBK",
            "customer_bank",
            "KUNNR + BANKS + BANKL + BANKN",
        ),
        (
            "CTX-CUSTOMER-TAX-S4",
            "S/4HANA Customer Tax",
            "ENTITY-CUSTOMER-TAX",
            "SYS-S4HANA",
            "KNAS",
            "customer_tax",
            "KUNNR + LAND1 + STCEG",
        ),
        (
            "CTX-VENDOR-CENTRAL-S4",
            "S/4HANA Vendor Central",
            "ENTITY-VENDOR-CENTRAL",
            "SYS-S4HANA",
            "LFA1",
            "vendor_general",
            "LIFNR",
        ),
        (
            "CTX-VENDOR-COMPANY-CODE-S4",
            "S/4HANA Vendor Company Code",
            "ENTITY-VENDOR-COMPANY-CODE",
            "SYS-S4HANA",
            "LFB1",
            "vendor_company_code",
            "LIFNR + BUKRS",
        ),
        (
            "CTX-VENDOR-PURCHASING-ORG-S4",
            "S/4HANA Vendor Purchasing Org",
            "ENTITY-VENDOR-PURCHASING-ORG",
            "SYS-S4HANA",
            "LFM1",
            "vendor_purchasing_org",
            "LIFNR + EKORG",
        ),
        (
            "CTX-VENDOR-CONTACT-S4",
            "S/4HANA Vendor Contact",
            "ENTITY-VENDOR-CONTACT",
            "SYS-S4HANA",
            "LFA1",
            "vendor_contact",
            "LIFNR",
        ),
        (
            "CTX-VENDOR-BANK-S4",
            "S/4HANA Vendor Bank",
            "ENTITY-VENDOR-BANK",
            "SYS-S4HANA",
            "LFBK",
            "vendor_bank",
            "LIFNR + BANKS + BANKL + BANKN",
        ),
        (
            "CTX-VENDOR-TAX-S4",
            "S/4HANA Vendor Tax",
            "ENTITY-VENDOR-TAX",
            "SYS-S4HANA",
            "LFAS",
            "vendor_tax",
            "LIFNR + LAND1 + STCEG",
        ),
        (
            "CTX-ADDRESS-S4",
            "S/4HANA Address",
            "ENTITY-ADDRESS",
            "SYS-S4HANA",
            "ADRC",
            "address",
            "ADDRNUMBER",
        ),
        (
            "CTX-PAYMENT-TERMS-S4",
            "S/4HANA Payment Terms",
            "ENTITY-PAYMENT-TERMS",
            "SYS-S4HANA",
            "T052",
            "payment_terms",
            "ZTERM",
        ),
        (
            "CTX-ACCOUNT-GROUP-S4",
            "S/4HANA Account Group",
            "ENTITY-ACCOUNT-GROUP",
            "SYS-S4HANA",
            "T077D",
            "account_group",
            "KTOKK",
        ),
        (
            "CTX-MIGRATION-FILE",
            "Migration File Context",
            "ENTITY-BP-CENTRAL",
            "SYS-MIGRATION-FILE",
            "MIGFILE",
            "file",
            "ROW",
        ),
    ]
    for ctx_id, name, entity, system, table, category, grain in contexts:
        write_canonical(
            MODEL_DIR / f"{ctx_id}.md",
            {
                "id": ctx_id,
                "type": "EntityContext",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": name,
                "domain": DOMAIN_ID,
                "system": system,
                "business_entity": entity,
                "sap_table": table,
                "context_category": category,
                "grain": grain,
            },
            f"# {name}\n\nContext for {table} with grain {grain}.",
        )

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------
    attribute_defs: list[tuple[str, str, str, str | None]] = [
        ("Business Partner Number", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Category", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Grouping", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Name", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Search Term 1", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Search Term 2", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Legal Form", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Foundation Date", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Central Block", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Gender", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Business Partner Tax Number 1", "bp_central", "bp", "CTX-BP-CENTRAL-S4"),
        ("Customer Number", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer Account Group", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer Name", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer Industry Code", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer Tax Number 1", "customer", "customer", "CTX-CUSTOMER-TAX-S4"),
        ("Customer VAT Registration", "customer", "customer", "CTX-CUSTOMER-TAX-S4"),
        ("Customer Country Key", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer Region", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer Postal Code", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer City", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer Street", "customer", "customer", "CTX-CUSTOMER-CENTRAL-S4"),
        ("Customer Company Code", "customer_company", "customer", "CTX-CUSTOMER-COMPANY-CODE-S4"),
        (
            "Customer Reconciliation Account",
            "customer_company",
            "customer",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
        ),
        ("Customer Payment Terms", "customer_company", "customer", "CTX-CUSTOMER-COMPANY-CODE-S4"),
        (
            "Customer Dunning Procedure",
            "customer_company",
            "customer",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
        ),
        (
            "Customer Interest Indicator",
            "customer_company",
            "customer",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
        ),
        ("Customer Lock Flag", "customer_company", "customer", "CTX-CUSTOMER-COMPANY-CODE-S4"),
        ("Customer Deletion Flag", "customer_company", "customer", "CTX-CUSTOMER-COMPANY-CODE-S4"),
        ("Customer Sales Organization", "customer_sales", "customer", "CTX-CUSTOMER-SALES-AREA-S4"),
        (
            "Customer Distribution Channel",
            "customer_sales",
            "customer",
            "CTX-CUSTOMER-SALES-AREA-S4",
        ),
        ("Customer Division", "customer_sales", "customer", "CTX-CUSTOMER-SALES-AREA-S4"),
        ("Customer Group", "customer_sales", "customer", "CTX-CUSTOMER-SALES-AREA-S4"),
        ("Customer Price Group", "customer_sales", "customer", "CTX-CUSTOMER-SALES-AREA-S4"),
        ("Customer Incoterms", "customer_sales", "customer", "CTX-CUSTOMER-SALES-AREA-S4"),
        (
            "Customer Shipping Conditions",
            "customer_sales",
            "customer",
            "CTX-CUSTOMER-SALES-AREA-S4",
        ),
        ("Customer Price List", "customer_sales", "customer", "CTX-CUSTOMER-SALES-AREA-S4"),
        ("Customer Delivery Priority", "customer_sales", "customer", "CTX-CUSTOMER-SALES-AREA-S4"),
        (
            "Customer Partner Function",
            "customer_partner",
            "customer",
            "CTX-CUSTOMER-PARTNER-FUNCTION-S4",
        ),
        (
            "Customer Partner Number",
            "customer_partner",
            "customer",
            "CTX-CUSTOMER-PARTNER-FUNCTION-S4",
        ),
        ("Customer Contact First Name", "customer_contact", "customer", "CTX-CUSTOMER-CONTACT-S4"),
        ("Customer Contact Last Name", "customer_contact", "customer", "CTX-CUSTOMER-CONTACT-S4"),
        ("Customer Contact Phone", "customer_contact", "customer", "CTX-CUSTOMER-CONTACT-S4"),
        ("Customer Bank Country", "customer_bank", "customer", "CTX-CUSTOMER-BANK-S4"),
        ("Customer Bank Key", "customer_bank", "customer", "CTX-CUSTOMER-BANK-S4"),
        ("Customer Bank Account", "customer_bank", "customer", "CTX-CUSTOMER-BANK-S4"),
        ("Vendor Number", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor Account Group", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor Name", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor Industry Code", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor Tax Number 1", "vendor", "vendor", "CTX-VENDOR-TAX-S4"),
        ("Vendor VAT Registration", "vendor", "vendor", "CTX-VENDOR-TAX-S4"),
        ("Vendor Country Key", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor Region", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor Postal Code", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor City", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor Street", "vendor", "vendor", "CTX-VENDOR-CENTRAL-S4"),
        ("Vendor Company Code", "vendor_company", "vendor", "CTX-VENDOR-COMPANY-CODE-S4"),
        ("Vendor Reconciliation Account", "vendor_company", "vendor", "CTX-VENDOR-COMPANY-CODE-S4"),
        ("Vendor Payment Terms", "vendor_company", "vendor", "CTX-VENDOR-COMPANY-CODE-S4"),
        ("Vendor Tolerance Group", "vendor_company", "vendor", "CTX-VENDOR-COMPANY-CODE-S4"),
        ("Vendor Lock Flag", "vendor_company", "vendor", "CTX-VENDOR-COMPANY-CODE-S4"),
        ("Vendor Deletion Flag", "vendor_company", "vendor", "CTX-VENDOR-COMPANY-CODE-S4"),
        (
            "Vendor Purchasing Organization",
            "vendor_purchasing",
            "vendor",
            "CTX-VENDOR-PURCHASING-ORG-S4",
        ),
        ("Vendor Purchasing Block", "vendor_purchasing", "vendor", "CTX-VENDOR-PURCHASING-ORG-S4"),
        ("Vendor Order Currency", "vendor_purchasing", "vendor", "CTX-VENDOR-PURCHASING-ORG-S4"),
        ("Vendor Terms of Payment", "vendor_purchasing", "vendor", "CTX-VENDOR-PURCHASING-ORG-S4"),
        ("Vendor GR-Based IV", "vendor_purchasing", "vendor", "CTX-VENDOR-PURCHASING-ORG-S4"),
        ("Vendor Contact First Name", "vendor_contact", "vendor", "CTX-VENDOR-CONTACT-S4"),
        ("Vendor Contact Last Name", "vendor_contact", "vendor", "CTX-VENDOR-CONTACT-S4"),
        ("Vendor Contact Phone", "vendor_contact", "vendor", "CTX-VENDOR-CONTACT-S4"),
        ("Vendor Bank Country", "vendor_bank", "vendor", "CTX-VENDOR-BANK-S4"),
        ("Vendor Bank Key", "vendor_bank", "vendor", "CTX-VENDOR-BANK-S4"),
        ("Vendor Bank Account", "vendor_bank", "vendor", "CTX-VENDOR-BANK-S4"),
        ("Address Number", "address", "shared", "CTX-ADDRESS-S4"),
        ("Address Street", "address", "shared", "CTX-ADDRESS-S4"),
        ("Address City", "address", "shared", "CTX-ADDRESS-S4"),
        ("Address Postal Code", "address", "shared", "CTX-ADDRESS-S4"),
        ("Address Country", "address", "shared", "CTX-ADDRESS-S4"),
        ("Address Region", "address", "shared", "CTX-ADDRESS-S4"),
        ("Payment Terms Code", "payment_terms", "shared", "CTX-PAYMENT-TERMS-S4"),
        ("Payment Terms Description", "payment_terms", "shared", "CTX-PAYMENT-TERMS-S4"),
        ("Account Group Code", "account_group", "shared", "CTX-ACCOUNT-GROUP-S4"),
        ("Account Group Description", "account_group", "shared", "CTX-ACCOUNT-GROUP-S4"),
    ]

    attribute_ids: list[str] = []
    for attr_name, category, classification, context_id in attribute_defs:
        a_id = attr_id(attr_name)
        attribute_ids.append(a_id)
        write_canonical(
            MODEL_DIR / f"{a_id}.md",
            {
                "id": a_id,
                "type": "Attribute",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": attr_name,
                "domain": DOMAIN_ID,
                "semantic_category": category,
                "data_classification": classification,
                "entity_context": context_id,
                "business_owner": "PERSON-BUSINESS-OWNER",
                "data_steward": "PERSON-DATA-STEWARD",
                "created_at": CREATED_AT,
                "description": f"Business attribute representing {attr_name.lower()}.",
            },
            f"# {attr_name}\n\nBusiness attribute for {attr_name.lower()}.",
        )

    # ------------------------------------------------------------------
    # Field endpoints
    # ------------------------------------------------------------------
    s4_fields: list[tuple[str, str, str, str, str, str]] = [
        # (table, field, attribute name, context, endpoint_type, technical_name)
        (
            "BUT000",
            "PARTNER",
            "Business Partner Number",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-PARTNER",
        ),
        (
            "BUT000",
            "BU_TYPE",
            "Business Partner Category",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-BU_TYPE",
        ),
        (
            "BUT000",
            "BU_GROUP",
            "Business Partner Grouping",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-BU_GROUP",
        ),
        (
            "BUT000",
            "NAME_ORG1",
            "Business Partner Name",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-NAME_ORG1",
        ),
        (
            "BUT000",
            "NAME_ORG2",
            "Business Partner Name",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-NAME_ORG2",
        ),
        (
            "BUT000",
            "NAME_LAST",
            "Business Partner Name",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-NAME_LAST",
        ),
        (
            "BUT000",
            "NAME_FIRST",
            "Business Partner Name",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-NAME_FIRST",
        ),
        (
            "BUT000",
            "BU_SORT1",
            "Business Partner Search Term 1",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-BU_SORT1",
        ),
        (
            "BUT000",
            "BU_SORT2",
            "Business Partner Search Term 2",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-BU_SORT2",
        ),
        (
            "BUT000",
            "LEGAL_ENTY",
            "Business Partner Legal Form",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-LEGAL_ENTY",
        ),
        (
            "BUT000",
            "FOUND_DAT",
            "Business Partner Foundation Date",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-FOUND_DAT",
        ),
        (
            "BUT000",
            "XBLCK",
            "Business Partner Central Block",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-XBLCK",
        ),
        (
            "BUT000",
            "XSEXF",
            "Business Partner Gender",
            "CTX-BP-CENTRAL-S4",
            "sap_table_field",
            "BUT000-XSEXF",
        ),
        (
            "KNA1",
            "KUNNR",
            "Customer Number",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-KUNNR",
        ),
        (
            "KNA1",
            "KTOKK",
            "Customer Account Group",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-KTOKK",
        ),
        (
            "KNA1",
            "NAME1",
            "Customer Name",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-NAME1",
        ),
        (
            "KNA1",
            "BRSCH",
            "Customer Industry Code",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-BRSCH",
        ),
        (
            "KNA1",
            "STCD1",
            "Customer Tax Number 1",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-STCD1",
        ),
        (
            "KNA1",
            "STCEG",
            "Customer VAT Registration",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-STCEG",
        ),
        (
            "KNA1",
            "LAND1",
            "Customer Country Key",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-LAND1",
        ),
        (
            "KNA1",
            "REGIO",
            "Customer Region",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-REGIO",
        ),
        (
            "KNA1",
            "PSTLZ",
            "Customer Postal Code",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-PSTLZ",
        ),
        (
            "KNA1",
            "ORT01",
            "Customer City",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-ORT01",
        ),
        (
            "KNA1",
            "STRAS",
            "Customer Street",
            "CTX-CUSTOMER-CENTRAL-S4",
            "sap_table_field",
            "KNA1-STRAS",
        ),
        (
            "KNB1",
            "BUKRS",
            "Customer Company Code",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
            "sap_table_field",
            "KNB1-BUKRS",
        ),
        (
            "KNB1",
            "AKONT",
            "Customer Reconciliation Account",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
            "sap_table_field",
            "KNB1-AKONT",
        ),
        (
            "KNB1",
            "ZTERM",
            "Customer Payment Terms",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
            "sap_table_field",
            "KNB1-ZTERM",
        ),
        (
            "KNB1",
            "MADAT",
            "Customer Dunning Procedure",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
            "sap_table_field",
            "KNB1-MADAT",
        ),
        (
            "KNB1",
            "VZSKZ",
            "Customer Interest Indicator",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
            "sap_table_field",
            "KNB1-VZSKZ",
        ),
        (
            "KNB1",
            "SPERR",
            "Customer Lock Flag",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
            "sap_table_field",
            "KNB1-SPERR",
        ),
        (
            "KNB1",
            "LOEVM",
            "Customer Deletion Flag",
            "CTX-CUSTOMER-COMPANY-CODE-S4",
            "sap_table_field",
            "KNB1-LOEVM",
        ),
        (
            "KNVV",
            "VKORG",
            "Customer Sales Organization",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-VKORG",
        ),
        (
            "KNVV",
            "VTWEG",
            "Customer Distribution Channel",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-VTWEG",
        ),
        (
            "KNVV",
            "SPART",
            "Customer Division",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-SPART",
        ),
        (
            "KNVV",
            "KDGRP",
            "Customer Group",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-KDGRP",
        ),
        (
            "KNVV",
            "KALKS",
            "Customer Price Group",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-KALKS",
        ),
        (
            "KNVV",
            "INCO1",
            "Customer Incoterms",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-INCO1",
        ),
        (
            "KNVV",
            "VSBED",
            "Customer Shipping Conditions",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-VSBED",
        ),
        (
            "KNVV",
            "PLTYP",
            "Customer Price List",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-PLTYP",
        ),
        (
            "KNVV",
            "LPRI",
            "Customer Delivery Priority",
            "CTX-CUSTOMER-SALES-AREA-S4",
            "sap_table_field",
            "KNVV-LPRI",
        ),
        (
            "KNVP",
            "PARVW",
            "Customer Partner Function",
            "CTX-CUSTOMER-PARTNER-FUNCTION-S4",
            "sap_table_field",
            "KNVP-PARVW",
        ),
        (
            "KNVP",
            "KUNN2",
            "Customer Partner Number",
            "CTX-CUSTOMER-PARTNER-FUNCTION-S4",
            "sap_table_field",
            "KNVP-KUNN2",
        ),
        (
            "LFA1",
            "LIFNR",
            "Vendor Number",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-LIFNR",
        ),
        (
            "LFA1",
            "KTOKK",
            "Vendor Account Group",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-KTOKK",
        ),
        ("LFA1", "NAME1", "Vendor Name", "CTX-VENDOR-CENTRAL-S4", "sap_table_field", "LFA1-NAME1"),
        (
            "LFA1",
            "BRSCH",
            "Vendor Industry Code",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-BRSCH",
        ),
        (
            "LFA1",
            "STCD1",
            "Vendor Tax Number 1",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-STCD1",
        ),
        (
            "LFA1",
            "STCEG",
            "Vendor VAT Registration",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-STCEG",
        ),
        (
            "LFA1",
            "LAND1",
            "Vendor Country Key",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-LAND1",
        ),
        (
            "LFA1",
            "REGIO",
            "Vendor Region",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-REGIO",
        ),
        (
            "LFA1",
            "PSTLZ",
            "Vendor Postal Code",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-PSTLZ",
        ),
        ("LFA1", "ORT01", "Vendor City", "CTX-VENDOR-CENTRAL-S4", "sap_table_field", "LFA1-ORT01"),
        (
            "LFA1",
            "STRAS",
            "Vendor Street",
            "CTX-VENDOR-CENTRAL-S4",
            "sap_table_field",
            "LFA1-STRAS",
        ),
        (
            "LFB1",
            "BUKRS",
            "Vendor Company Code",
            "CTX-VENDOR-COMPANY-CODE-S4",
            "sap_table_field",
            "LFB1-BUKRS",
        ),
        (
            "LFB1",
            "AKONT",
            "Vendor Reconciliation Account",
            "CTX-VENDOR-COMPANY-CODE-S4",
            "sap_table_field",
            "LFB1-AKONT",
        ),
        (
            "LFB1",
            "ZTERM",
            "Vendor Payment Terms",
            "CTX-VENDOR-COMPANY-CODE-S4",
            "sap_table_field",
            "LFB1-ZTERM",
        ),
        (
            "LFB1",
            "TOGRU",
            "Vendor Tolerance Group",
            "CTX-VENDOR-COMPANY-CODE-S4",
            "sap_table_field",
            "LFB1-TOGRU",
        ),
        (
            "LFB1",
            "SPERR",
            "Vendor Lock Flag",
            "CTX-VENDOR-COMPANY-CODE-S4",
            "sap_table_field",
            "LFB1-SPERR",
        ),
        (
            "LFB1",
            "LOEVM",
            "Vendor Deletion Flag",
            "CTX-VENDOR-COMPANY-CODE-S4",
            "sap_table_field",
            "LFB1-LOEVM",
        ),
        (
            "LFM1",
            "EKORG",
            "Vendor Purchasing Organization",
            "CTX-VENDOR-PURCHASING-ORG-S4",
            "sap_table_field",
            "LFM1-EKORG",
        ),
        (
            "LFM1",
            "SPERR",
            "Vendor Purchasing Block",
            "CTX-VENDOR-PURCHASING-ORG-S4",
            "sap_table_field",
            "LFM1-SPERR",
        ),
        (
            "LFM1",
            "WAERS",
            "Vendor Order Currency",
            "CTX-VENDOR-PURCHASING-ORG-S4",
            "sap_table_field",
            "LFM1-WAERS",
        ),
        (
            "LFM1",
            "ZTERM",
            "Vendor Terms of Payment",
            "CTX-VENDOR-PURCHASING-ORG-S4",
            "sap_table_field",
            "LFM1-ZTERM",
        ),
        (
            "LFM1",
            "WEBRE",
            "Vendor GR-Based IV",
            "CTX-VENDOR-PURCHASING-ORG-S4",
            "sap_table_field",
            "LFM1-WEBRE",
        ),
        (
            "ADRC",
            "ADDRNUMBER",
            "Address Number",
            "CTX-ADDRESS-S4",
            "sap_table_field",
            "ADRC-ADDRNUMBER",
        ),
        ("ADRC", "STREET", "Address Street", "CTX-ADDRESS-S4", "sap_table_field", "ADRC-STREET"),
        ("ADRC", "CITY1", "Address City", "CTX-ADDRESS-S4", "sap_table_field", "ADRC-CITY1"),
        (
            "ADRC",
            "POST_CODE1",
            "Address Postal Code",
            "CTX-ADDRESS-S4",
            "sap_table_field",
            "ADRC-POST_CODE1",
        ),
        ("ADRC", "COUNTRY", "Address Country", "CTX-ADDRESS-S4", "sap_table_field", "ADRC-COUNTRY"),
        ("ADRC", "REGION", "Address Region", "CTX-ADDRESS-S4", "sap_table_field", "ADRC-REGION"),
        (
            "T052",
            "ZTERM",
            "Payment Terms Code",
            "CTX-PAYMENT-TERMS-S4",
            "sap_table_field",
            "T052-ZTERM",
        ),
        (
            "T052",
            "TEXT1",
            "Payment Terms Description",
            "CTX-PAYMENT-TERMS-S4",
            "sap_table_field",
            "T052-TEXT1",
        ),
        (
            "T077D",
            "KTOKK",
            "Account Group Code",
            "CTX-ACCOUNT-GROUP-S4",
            "sap_table_field",
            "T077D-KTOKK",
        ),
        (
            "T077D",
            "TXT30",
            "Account Group Description",
            "CTX-ACCOUNT-GROUP-S4",
            "sap_table_field",
            "T077D-TXT30",
        ),
    ]

    # Build a map of (table, field) -> list of attribute names for enrichment decisions.
    fep_attr_lookup: dict[tuple[str, str], str] = {}
    s4_fep_ids: dict[tuple[str, str], str] = {}
    for table, field, attr_name, ctx_id, endpoint_type, tech_name in s4_fields:
        f_id = fep_id(table, field, "S4")
        s4_fep_ids[(table, field)] = f_id
        fep_attr_lookup[(table, field)] = attr_name
        a_id = attr_id(attr_name)
        extra = {}
        if endpoint_type == "sap_table_field":
            extra = {
                "sap_table": table,
                "sap_field": field,
                "technical_name": tech_name,
                "entity_context": ctx_id,
            }
        write_canonical(
            MODEL_DIR / f"{f_id}.md",
            {
                "id": f_id,
                "type": "FieldEndpoint",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": tech_name,
                "domain": DOMAIN_ID,
                "system": "SYS-S4HANA",
                "endpoint_type": endpoint_type,
                "business_attribute": a_id,
                "business_owner": "PERSON-BUSINESS-OWNER",
                "data_steward": "PERSON-DATA-STEWARD",
                "created_at": CREATED_AT,
                "description": f"S/4HANA field endpoint for {attr_name} on {table}.",
                **extra,
            },
            f"# {tech_name}\n\nS/4HANA target field {tech_name} for {attr_name}.",
        )

    # Legacy file endpoints for a subset of fields that we will map.
    legacy_fields = [
        ("LEGACY-CUST-NUMBER", "Legacy Customer Number", "Customer Number", "customer_number"),
        ("LEGACY-CUST-GROUP", "Legacy Customer Group", "Customer Group", "customer_group"),
        (
            "LEGACY-CUST-INDUSTRY",
            "Legacy Customer Industry",
            "Customer Industry Code",
            "industry_code",
        ),
        (
            "LEGACY-CUST-PAYMENT-TERMS",
            "Legacy Customer Payment Terms",
            "Customer Payment Terms",
            "payment_terms",
        ),
        ("LEGACY-CUST-INCOTERMS", "Legacy Customer Incoterms", "Customer Incoterms", "incoterms"),
        (
            "LEGACY-CUST-SHIPPING-COND",
            "Legacy Customer Shipping Conditions",
            "Customer Shipping Conditions",
            "shipping_cond",
        ),
        (
            "LEGACY-CUST-PARTNER-FUNCTION",
            "Legacy Customer Partner Function",
            "Customer Partner Function",
            "partner_function",
        ),
        (
            "LEGACY-CUST-TAX-NUMBER",
            "Legacy Customer Tax Number 1",
            "Customer Tax Number 1",
            "tax_number",
        ),
        ("LEGACY-VEND-NUMBER", "Legacy Vendor Number", "Vendor Number", "vendor_number"),
        (
            "LEGACY-VEND-ACCOUNT-GROUP",
            "Legacy Vendor Account Group",
            "Vendor Account Group",
            "account_group",
        ),
        ("LEGACY-VEND-INDUSTRY", "Legacy Vendor Industry", "Vendor Industry Code", "industry_code"),
        (
            "LEGACY-VEND-PAYMENT-TERMS",
            "Legacy Vendor Payment Terms",
            "Vendor Payment Terms",
            "payment_terms",
        ),
        (
            "LEGACY-VEND-PURCHASING-BLOCK",
            "Legacy Vendor Purchasing Block",
            "Vendor Purchasing Block",
            "purchasing_block",
        ),
        (
            "LEGACY-VEND-ORDER-CURRENCY",
            "Legacy Vendor Order Currency",
            "Vendor Order Currency",
            "order_currency",
        ),
        (
            "LEGACY-VEND-TAX-NUMBER",
            "Legacy Vendor Tax Number 1",
            "Vendor Tax Number 1",
            "tax_number",
        ),
        ("MIGFILE-BP-NUMBER", "Migration File BP Number", "Business Partner Number", "bp_number"),
        (
            "MIGFILE-CUSTOMER-NUMBER",
            "Migration File Customer Number",
            "Customer Number",
            "customer_number",
        ),
        ("MIGFILE-VENDOR-NUMBER", "Migration File Vendor Number", "Vendor Number", "vendor_number"),
        (
            "MIGFILE-CUSTOMER-GROUP",
            "Migration File Customer Group",
            "Customer Group",
            "customer_group",
        ),
        (
            "MIGFILE-VENDOR-ACCOUNT-GROUP",
            "Migration File Vendor Account Group",
            "Vendor Account Group",
            "account_group",
        ),
        (
            "MIGFILE-PAYMENT-TERMS",
            "Migration File Payment Terms",
            "Payment Terms Code",
            "payment_terms",
        ),
        ("MIGFILE-INCOTERMS", "Migration File Incoterms", "Customer Incoterms", "incoterms"),
        ("MIGFILE-COUNTRY", "Migration File Country", "Address Country", "country"),
        ("MIGFILE-REGION", "Migration File Region", "Address Region", "region"),
    ]
    legacy_fep_ids: dict[str, str] = {}
    migfile_fep_ids: dict[str, str] = {}
    for fep_id_val, name, attr_name, _ in legacy_fields:
        if fep_id_val.startswith("LEGACY"):
            system = "SYS-LEGACY-ERP"
            bucket = legacy_fep_ids
        else:
            system = "SYS-MIGRATION-FILE"
            bucket = migfile_fep_ids
        bucket_key = fep_id_val.split("-", 1)[1]
        bucket[bucket_key] = fep_id_val
        a_id = attr_id(attr_name)
        write_canonical(
            MODEL_DIR / f"{fep_id_val}.md",
            {
                "id": fep_id_val,
                "type": "FieldEndpoint",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": name,
                "domain": DOMAIN_ID,
                "system": system,
                "endpoint_type": "file_column",
                "column_name": fep_id_val.split("-")[-1],
                "business_attribute": a_id,
                "business_owner": "PERSON-BUSINESS-OWNER",
                "data_steward": "PERSON-DATA-STEWARD",
                "created_at": CREATED_AT,
                "description": f"{name} source endpoint.",
            },
            f"# {name}\n\nSource column for {attr_name}.",
        )

    # ------------------------------------------------------------------
    # Attribute usages
    # ------------------------------------------------------------------
    usage_count = 0
    for table, field, attr_name, ctx_id, _endpoint_type, _tech_name in s4_fields:
        a_id = attr_id(attr_name)
        f_id = fep_id(table, field, "S4")
        use_id_val = f"USE-{safe_id(attr_name)}-{table}"
        write_canonical(
            MODEL_DIR / f"{use_id_val}.md",
            {
                "id": use_id_val,
                "type": "AttributeUsage",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": f"{attr_name} on {table}",
                "domain": DOMAIN_ID,
                "attribute": a_id,
                "entity_context": ctx_id,
                "field_endpoint": f_id,
                "usage_type": "primary",
                "scope": table.lower(),
            },
            f"# {attr_name} usage on {table}\n\nLinks the attribute to the {table} field endpoint.",
        )
        usage_count += 1

    # ------------------------------------------------------------------
    # Mapping set
    # ------------------------------------------------------------------
    write_canonical(
        MODEL_DIR / "MAPSET-SAP-BP-CUSTOMER-VENDOR.md",
        {
            "id": "MAPSET-SAP-BP-CUSTOMER-VENDOR",
            "type": "MappingSet",
            "status": "active",
            "schema_version": SCHEMA_VERSION,
            "name": "SAP BP / Customer / Vendor Mapping Set",
            "domain": DOMAIN_ID,
            "business_owner": "PERSON-BUSINESS-OWNER",
        },
        "# SAP BP / Customer / Vendor Mapping Set\n\n"
        "Groups all field-level mappings for the reference migration.",
    )

    # ------------------------------------------------------------------
    # Mappings
    # ------------------------------------------------------------------
    mapping_pairs: list[tuple[str, str, str]] = [
        ("LEGACY-CUST-NUMBER", "FEP-S4-KNA1-KUNNR", "Legacy customer number to KNA1-KUNNR"),
        ("LEGACY-CUST-GROUP", "FEP-S4-KNVV-KDGRP", "Legacy customer group to KNVV-KDGRP"),
        ("LEGACY-CUST-INDUSTRY", "FEP-S4-KNA1-BRSCH", "Legacy customer industry to KNA1-BRSCH"),
        (
            "LEGACY-CUST-PAYMENT-TERMS",
            "FEP-S4-KNB1-ZTERM",
            "Legacy customer payment terms to KNB1-ZTERM",
        ),
        ("LEGACY-CUST-INCOTERMS", "FEP-S4-KNVV-INCO1", "Legacy customer incoterms to KNVV-INCO1"),
        (
            "LEGACY-CUST-SHIPPING-COND",
            "FEP-S4-KNVV-VSBED",
            "Legacy customer shipping conditions to KNVV-VSBED",
        ),
        (
            "LEGACY-CUST-PARTNER-FUNCTION",
            "FEP-S4-KNVP-PARVW",
            "Legacy customer partner function to KNVP-PARVW",
        ),
        ("LEGACY-CUST-TAX-NUMBER", "FEP-S4-KNA1-STCD1", "Legacy customer tax number to KNA1-STCD1"),
        ("LEGACY-VEND-NUMBER", "FEP-S4-LFA1-LIFNR", "Legacy vendor number to LFA1-LIFNR"),
        (
            "LEGACY-VEND-ACCOUNT-GROUP",
            "FEP-S4-LFA1-KTOKK",
            "Legacy vendor account group to LFA1-KTOKK",
        ),
        ("LEGACY-VEND-INDUSTRY", "FEP-S4-LFA1-BRSCH", "Legacy vendor industry to LFA1-BRSCH"),
        (
            "LEGACY-VEND-PAYMENT-TERMS",
            "FEP-S4-LFB1-ZTERM",
            "Legacy vendor payment terms to LFB1-ZTERM",
        ),
        (
            "LEGACY-VEND-PURCHASING-BLOCK",
            "FEP-S4-LFM1-SPERR",
            "Legacy vendor purchasing block to LFM1-SPERR",
        ),
        (
            "LEGACY-VEND-ORDER-CURRENCY",
            "FEP-S4-LFM1-WAERS",
            "Legacy vendor order currency to LFM1-WAERS",
        ),
        ("LEGACY-VEND-TAX-NUMBER", "FEP-S4-LFA1-STCD1", "Legacy vendor tax number to LFA1-STCD1"),
        (
            "MIGFILE-BP-NUMBER",
            "FEP-S4-BUT000-PARTNER",
            "Migration file BP number to BUT000-PARTNER",
        ),
        (
            "MIGFILE-CUSTOMER-NUMBER",
            "FEP-S4-KNA1-KUNNR",
            "Migration file customer number to KNA1-KUNNR",
        ),
        (
            "MIGFILE-VENDOR-NUMBER",
            "FEP-S4-LFA1-LIFNR",
            "Migration file vendor number to LFA1-LIFNR",
        ),
        (
            "MIGFILE-CUSTOMER-GROUP",
            "FEP-S4-KNVV-KDGRP",
            "Migration file customer group to KNVV-KDGRP",
        ),
        (
            "MIGFILE-VENDOR-ACCOUNT-GROUP",
            "FEP-S4-LFA1-KTOKK",
            "Migration file vendor account group to LFA1-KTOKK",
        ),
        (
            "MIGFILE-PAYMENT-TERMS",
            "FEP-S4-KNB1-ZTERM",
            "Migration file payment terms to KNB1-ZTERM",
        ),
        ("MIGFILE-INCOTERMS", "FEP-S4-KNVV-INCO1", "Migration file incoterms to KNVV-INCO1"),
        ("MIGFILE-COUNTRY", "FEP-S4-ADRC-COUNTRY", "Migration file country to ADRC-COUNTRY"),
        ("MIGFILE-REGION", "FEP-S4-ADRC-REGION", "Migration file region to ADRC-REGION"),
    ]
    mapping_ids: list[str] = []
    for source_fep_id, target_fep_id, description in mapping_pairs:
        m_id = map_id(source_fep_id, target_fep_id)
        mapping_ids.append(m_id)
        write_canonical(
            MODEL_DIR / f"{m_id}.md",
            {
                "id": m_id,
                "type": "Mapping",
                "status": "draft",
                "schema_version": SCHEMA_VERSION,
                "name": description,
                "domain": DOMAIN_ID,
                "source_endpoint": source_fep_id,
                "target_endpoint": target_fep_id,
                "mapping_set": "MAPSET-SAP-BP-CUSTOMER-VENDOR",
                "business_owner": "PERSON-BUSINESS-OWNER",
                "data_steward": "PERSON-DATA-STEWARD",
                "description": description,
            },
            f"# {description}\n\nField mapping from {source_fep_id} to {target_fep_id}.",
        )

    # ------------------------------------------------------------------
    # Value lists
    # ------------------------------------------------------------------
    value_lists: dict[str, list[dict[str, Any]]] = {
        "VLIST-S4-CUSTOMER-GROUP": [
            {
                "code": "01",
                "label": "Wholesale",
                "description": "Wholesale customers",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "02",
                "label": "Retail",
                "description": "Retail customers",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "03",
                "label": "Export",
                "description": "Export customers",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "04",
                "label": "Internal",
                "description": "Internal group customers",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-LEGACY-CUSTOMER-GROUP": [
            {
                "code": "CH01",
                "label": "Channel 01",
                "description": "Legacy channel 01",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "CH02",
                "label": "Channel 02",
                "description": "Legacy channel 02",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "A17",
                "label": "Area 17",
                "description": "Legacy area 17",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "ZZ",
                "label": "Unknown",
                "description": "Legacy unknown group",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-S4-VENDOR-ACCOUNT-GROUP": [
            {
                "code": "0001",
                "label": "Domestic Vendor",
                "description": "Domestic standard vendor",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "0002",
                "label": "Foreign Vendor",
                "description": "Foreign standard vendor",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "0003",
                "label": "One-Time Vendor",
                "description": "One-time vendor",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "0004",
                "label": "Employee Vendor",
                "description": "Employee vendor",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-LEGACY-VENDOR-ACCOUNT-GROUP": [
            {
                "code": "V01",
                "label": "Vendor 01",
                "description": "Legacy domestic vendor",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "V02",
                "label": "Vendor 02",
                "description": "Legacy foreign vendor",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "V03",
                "label": "Vendor 03",
                "description": "Legacy one-time vendor",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "V99",
                "label": "Vendor 99",
                "description": "Legacy miscellaneous vendor",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-S4-CUSTOMER-ACCOUNT-GROUP": [
            {
                "code": "0001",
                "label": "Sold-To",
                "description": "Sold-to party",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "0002",
                "label": "Ship-To",
                "description": "Ship-to party",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "0003",
                "label": "Bill-To",
                "description": "Bill-to party",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "0004",
                "label": "Payer",
                "description": "Payer party",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-LEGACY-CUSTOMER-ACCOUNT-GROUP": [
            {
                "code": "C01",
                "label": "Customer 01",
                "description": "Legacy sold-to",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "C02",
                "label": "Customer 02",
                "description": "Legacy ship-to",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "C03",
                "label": "Customer 03",
                "description": "Legacy bill-to",
                "sort_order": 3,
                "is_active": True,
            },
        ],
        "VLIST-S4-INDUSTRY-CODE": [
            {
                "code": "1000",
                "label": "Manufacturing",
                "description": "Manufacturing industry",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "2000",
                "label": "Retail",
                "description": "Retail industry",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "3000",
                "label": "Services",
                "description": "Services industry",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "4000",
                "label": "Technology",
                "description": "Technology industry",
                "sort_order": 4,
                "is_active": True,
            },
            {
                "code": "5000",
                "label": "Finance",
                "description": "Finance industry",
                "sort_order": 5,
                "is_active": True,
            },
        ],
        "VLIST-LEGACY-INDUSTRY-CODE": [
            {
                "code": "MFG",
                "label": "Manufacturing",
                "description": "Legacy manufacturing",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "RET",
                "label": "Retail",
                "description": "Legacy retail",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "SRV",
                "label": "Services",
                "description": "Legacy services",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "TECH",
                "label": "Technology",
                "description": "Legacy technology",
                "sort_order": 4,
                "is_active": True,
            },
            {
                "code": "FIN",
                "label": "Finance",
                "description": "Legacy finance",
                "sort_order": 5,
                "is_active": True,
            },
        ],
        "VLIST-S4-PAYMENT-TERMS": [
            {
                "code": "0001",
                "label": "Payable immediately",
                "description": "Payable immediately due net",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "0002",
                "label": "14 days 2%",
                "description": "14 days with 2% discount",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "0003",
                "label": "30 days net",
                "description": "30 days net",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "0004",
                "label": "60 days net",
                "description": "60 days net",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-LEGACY-PAYMENT-TERMS": [
            {
                "code": "PI",
                "label": "Pay immediately",
                "description": "Legacy payable immediately",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "14D2",
                "label": "14 days discount",
                "description": "Legacy 14 days 2%",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "30D",
                "label": "30 days",
                "description": "Legacy 30 days net",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "60D",
                "label": "60 days",
                "description": "Legacy 60 days net",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-S4-INCOTERMS": [
            {
                "code": "EXW",
                "label": "Ex Works",
                "description": "Ex works",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "FOB",
                "label": "Free On Board",
                "description": "Free on board",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "CIF",
                "label": "Cost Insurance Freight",
                "description": "Cost insurance freight",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "DDP",
                "label": "Delivered Duty Paid",
                "description": "Delivered duty paid",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-LEGACY-INCOTERMS": [
            {
                "code": "EX",
                "label": "Ex Works",
                "description": "Legacy ex works",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "FB",
                "label": "Free Board",
                "description": "Legacy free board",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "CF",
                "label": "Cost Freight",
                "description": "Legacy cost freight",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "DP",
                "label": "Duty Paid",
                "description": "Legacy duty paid",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-S4-PARTNER-FUNCTION": [
            {
                "code": "AG",
                "label": "Sold-To",
                "description": "Sold-to party",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "WE",
                "label": "Ship-To",
                "description": "Ship-to party",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "RE",
                "label": "Bill-To",
                "description": "Bill-to party",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "RG",
                "label": "Payer",
                "description": "Payer party",
                "sort_order": 4,
                "is_active": True,
            },
            {
                "code": "SP",
                "label": "Contact Person",
                "description": "Contact person",
                "sort_order": 5,
                "is_active": True,
            },
        ],
        "VLIST-LEGACY-PARTNER-FUNCTION": [
            {
                "code": "SOLD",
                "label": "Sold-To",
                "description": "Legacy sold-to",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "SHIP",
                "label": "Ship-To",
                "description": "Legacy ship-to",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "BILL",
                "label": "Bill-To",
                "description": "Legacy bill-to",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "PAY",
                "label": "Payer",
                "description": "Legacy payer",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-S4-SHIPPING-CONDITION": [
            {
                "code": "01",
                "label": "Standard",
                "description": "Standard shipping",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "02",
                "label": "Express",
                "description": "Express shipping",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "03",
                "label": "Pick-up",
                "description": "Customer pick-up",
                "sort_order": 3,
                "is_active": True,
            },
        ],
        "VLIST-LEGACY-SHIPPING-CONDITION": [
            {
                "code": "STD",
                "label": "Standard",
                "description": "Legacy standard",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "EXP",
                "label": "Express",
                "description": "Legacy express",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "PU",
                "label": "Pick-up",
                "description": "Legacy pick-up",
                "sort_order": 3,
                "is_active": True,
            },
        ],
        "VLIST-S4-COUNTRY": [
            {
                "code": "US",
                "label": "United States",
                "description": "United States",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "DE",
                "label": "Germany",
                "description": "Germany",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "GB",
                "label": "United Kingdom",
                "description": "United Kingdom",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "FR",
                "label": "France",
                "description": "France",
                "sort_order": 4,
                "is_active": True,
            },
        ],
        "VLIST-S4-REGION": [
            {
                "code": "CA",
                "label": "California",
                "description": "California",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "code": "NY",
                "label": "New York",
                "description": "New York",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "code": "BY",
                "label": "Bavaria",
                "description": "Bavaria",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "code": "IDF",
                "label": "Ile-de-France",
                "description": "Ile-de-France",
                "sort_order": 4,
                "is_active": True,
            },
        ],
    }

    for vl_id, entries in value_lists.items():
        write_canonical(
            MODEL_DIR / f"{vl_id}.md",
            {
                "id": vl_id,
                "type": "ValueList",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": vl_id.replace("VLIST-", "").replace("-", " ").title() + " Values",
                "value_list_type": "domain",
                "domain": DOMAIN_ID,
                "data_steward": "PERSON-DATA-STEWARD",
                "entries": entries,
            },
            f"# {vl_id}\n\nAllowed values list.",
        )

    # Link value lists to relevant field endpoints and attributes.
    fep_to_vlist: dict[str, str] = {
        "FEP-S4-KNVV-KDGRP": "VLIST-S4-CUSTOMER-GROUP",
        "FEP-S4-LFA1-KTOKK": "VLIST-S4-VENDOR-ACCOUNT-GROUP",
        "FEP-S4-KNA1-KTOKK": "VLIST-S4-CUSTOMER-ACCOUNT-GROUP",
        "FEP-S4-KNA1-BRSCH": "VLIST-S4-INDUSTRY-CODE",
        "FEP-S4-LFA1-BRSCH": "VLIST-S4-INDUSTRY-CODE",
        "FEP-S4-KNB1-ZTERM": "VLIST-S4-PAYMENT-TERMS",
        "FEP-S4-LFB1-ZTERM": "VLIST-S4-PAYMENT-TERMS",
        "FEP-S4-KNVV-INCO1": "VLIST-S4-INCOTERMS",
        "FEP-S4-KNVP-PARVW": "VLIST-S4-PARTNER-FUNCTION",
        "FEP-S4-KNVV-VSBED": "VLIST-S4-SHIPPING-CONDITION",
        "FEP-S4-ADRC-COUNTRY": "VLIST-S4-COUNTRY",
        "FEP-S4-ADRC-REGION": "VLIST-S4-REGION",
    }

    # Re-write those FEP files with value_list reference.
    for fep_id_val, vl_id in fep_to_vlist.items():
        path = MODEL_DIR / f"{fep_id_val}.md"
        fm: dict[str, Any] = {"value_list": vl_id}
        # We need to read, patch and rewrite. Simpler: read raw, parse, update, rewrite.
        raw = path.read_text(encoding="utf-8")
        parts = raw.split("---", 2)
        existing = yaml.safe_load(parts[1])
        existing["value_list"] = vl_id
        body = parts[2].strip()
        write_canonical(path, existing, body)

    # ------------------------------------------------------------------
    # Value mappings
    # ------------------------------------------------------------------
    value_mappings: list[tuple[str, str, str, list[tuple[str, str, str]]]] = [
        (
            "VMAP-CUSTOMER-GROUP-LEGACY-TO-S4",
            "VLIST-LEGACY-CUSTOMER-GROUP",
            "VLIST-S4-CUSTOMER-GROUP",
            [
                ("CH01", "01", "Channel 01 -> Wholesale"),
                ("CH02", "02", "Channel 02 -> Retail"),
                ("A17", "03", "Area 17 -> Export fallback"),
                ("ZZ", "04", "Unknown -> Internal"),
            ],
        ),
        (
            "VMAP-VENDOR-ACCOUNT-GROUP-LEGACY-TO-S4",
            "VLIST-LEGACY-VENDOR-ACCOUNT-GROUP",
            "VLIST-S4-VENDOR-ACCOUNT-GROUP",
            [
                ("V01", "0001", "Domestic vendor"),
                ("V02", "0002", "Foreign vendor"),
                ("V03", "0003", "One-time vendor"),
                ("V99", "0004", "Misc -> Employee vendor"),
            ],
        ),
        (
            "VMAP-CUSTOMER-ACCOUNT-GROUP-LEGACY-TO-S4",
            "VLIST-LEGACY-CUSTOMER-ACCOUNT-GROUP",
            "VLIST-S4-CUSTOMER-ACCOUNT-GROUP",
            [
                ("C01", "0001", "Sold-to"),
                ("C02", "0002", "Ship-to"),
                ("C03", "0003", "Bill-to"),
            ],
        ),
        (
            "VMAP-INDUSTRY-CODE-LEGACY-TO-S4",
            "VLIST-LEGACY-INDUSTRY-CODE",
            "VLIST-S4-INDUSTRY-CODE",
            [
                ("MFG", "1000", "Manufacturing"),
                ("RET", "2000", "Retail"),
                ("SRV", "3000", "Services"),
                ("TECH", "4000", "Technology"),
                ("FIN", "5000", "Finance"),
            ],
        ),
        (
            "VMAP-PAYMENT-TERMS-LEGACY-TO-S4",
            "VLIST-LEGACY-PAYMENT-TERMS",
            "VLIST-S4-PAYMENT-TERMS",
            [
                ("PI", "0001", "Payable immediately"),
                ("14D2", "0002", "14 days 2%"),
                ("30D", "0003", "30 days net"),
                ("60D", "0004", "60 days net"),
            ],
        ),
        (
            "VMAP-INCOTERMS-LEGACY-TO-S4",
            "VLIST-LEGACY-INCOTERMS",
            "VLIST-S4-INCOTERMS",
            [
                ("EX", "EXW", "Ex works"),
                ("FB", "FOB", "Free on board"),
                ("CF", "CIF", "Cost insurance freight"),
                ("DP", "DDP", "Delivered duty paid"),
            ],
        ),
        (
            "VMAP-PARTNER-FUNCTION-LEGACY-TO-S4",
            "VLIST-LEGACY-PARTNER-FUNCTION",
            "VLIST-S4-PARTNER-FUNCTION",
            [
                ("SOLD", "AG", "Sold-to"),
                ("SHIP", "WE", "Ship-to"),
                ("BILL", "RE", "Bill-to"),
                ("PAY", "RG", "Payer"),
            ],
        ),
        (
            "VMAP-SHIPPING-CONDITION-LEGACY-TO-S4",
            "VLIST-LEGACY-SHIPPING-CONDITION",
            "VLIST-S4-SHIPPING-CONDITION",
            [
                ("STD", "01", "Standard"),
                ("EXP", "02", "Express"),
                ("PU", "03", "Pick-up"),
            ],
        ),
    ]
    for vm_id, source_vl, target_vl, entries in value_mappings:
        entry_list = [
            {
                "source_code": src,
                "target_code": tgt,
                "description": desc,
                "fallback": idx == len(entries) - 1,
            }
            for idx, (src, tgt, desc) in enumerate(entries)
        ]
        write_canonical(
            MODEL_DIR / f"{vm_id}.md",
            {
                "id": vm_id,
                "type": "ValueMapping",
                "status": "draft",
                "schema_version": SCHEMA_VERSION,
                "name": vm_id.replace("VMAP-", "").replace("-", " ").title(),
                "domain": DOMAIN_ID,
                "source_value_list": source_vl,
                "target_value_list": target_vl,
                "business_owner": "PERSON-BUSINESS-OWNER",
                "data_steward": "PERSON-DATA-STEWARD",
                "entries": entry_list,
            },
            f"# {vm_id}\n\nValue mapping from {source_vl} to {target_vl}.",
        )

    # Link value mappings to relevant mappings.
    mapping_to_vmap: dict[str, str] = {
        "MAP-LEGACY-CUST-GROUP-TO-FEP-S4-KNVV-KDGRP": (
            "VMAP-CUSTOMER-GROUP-LEGACY-TO-S4"
        ),
        "MAP-LEGACY-VEND-ACCOUNT-GROUP-TO-FEP-S4-LFA1-KTOKK": (
            "VMAP-VENDOR-ACCOUNT-GROUP-LEGACY-TO-S4"
        ),
        "MAP-LEGACY-CUST-INDUSTRY-TO-FEP-S4-KNA1-BRSCH": (
            "VMAP-INDUSTRY-CODE-LEGACY-TO-S4"
        ),
        "MAP-LEGACY-VEND-INDUSTRY-TO-FEP-S4-LFA1-BRSCH": (
            "VMAP-INDUSTRY-CODE-LEGACY-TO-S4"
        ),
        "MAP-LEGACY-CUST-PAYMENT-TERMS-TO-FEP-S4-KNB1-ZTERM": (
            "VMAP-PAYMENT-TERMS-LEGACY-TO-S4"
        ),
        "MAP-LEGACY-VEND-PAYMENT-TERMS-TO-FEP-S4-LFB1-ZTERM": (
            "VMAP-PAYMENT-TERMS-LEGACY-TO-S4"
        ),
        "MAP-LEGACY-CUST-INCOTERMS-TO-FEP-S4-KNVV-INCO1": (
            "VMAP-INCOTERMS-LEGACY-TO-S4"
        ),
        "MAP-LEGACY-CUST-PARTNER-FUNCTION-TO-FEP-S4-KNVP-PARVW": (
            "VMAP-PARTNER-FUNCTION-LEGACY-TO-S4"
        ),
        "MAP-LEGACY-CUST-SHIPPING-COND-TO-FEP-S4-KNVV-VSBED": (
            "VMAP-SHIPPING-CONDITION-LEGACY-TO-S4"
        ),
    }
    for m_id, vm_id in mapping_to_vmap.items():
        path = MODEL_DIR / f"{m_id}.md"
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        parts = raw.split("---", 2)
        existing = yaml.safe_load(parts[1])
        existing["value_mapping"] = vm_id
        body = parts[2].strip()
        write_canonical(path, existing, body)

    # ------------------------------------------------------------------
    # Validation rules
    # ------------------------------------------------------------------
    validation_defs: list[tuple[str, str, str, str]] = [
        (
            "VAL-CUSTOMER-GROUP-ALLOWED",
            "Customer Group Allowed Values",
            "ATTR-CUSTOMER-GROUP",
            "VLIST-S4-CUSTOMER-GROUP",
        ),
        (
            "VAL-VENDOR-ACCOUNT-GROUP-ALLOWED",
            "Vendor Account Group Allowed Values",
            "ATTR-VENDOR-ACCOUNT-GROUP",
            "VLIST-S4-VENDOR-ACCOUNT-GROUP",
        ),
        (
            "VAL-CUSTOMER-ACCOUNT-GROUP-ALLOWED",
            "Customer Account Group Allowed Values",
            "ATTR-CUSTOMER-ACCOUNT-GROUP",
            "VLIST-S4-CUSTOMER-ACCOUNT-GROUP",
        ),
        (
            "VAL-CUSTOMER-INDUSTRY-ALLOWED",
            "Customer Industry Allowed Values",
            "ATTR-CUSTOMER-INDUSTRY-CODE",
            "VLIST-S4-INDUSTRY-CODE",
        ),
        (
            "VAL-VENDOR-INDUSTRY-ALLOWED",
            "Vendor Industry Allowed Values",
            "ATTR-VENDOR-INDUSTRY-CODE",
            "VLIST-S4-INDUSTRY-CODE",
        ),
        (
            "VAL-CUSTOMER-PAYMENT-TERMS-ALLOWED",
            "Customer Payment Terms Allowed",
            "ATTR-CUSTOMER-PAYMENT-TERMS",
            "VLIST-S4-PAYMENT-TERMS",
        ),
        (
            "VAL-VENDOR-PAYMENT-TERMS-ALLOWED",
            "Vendor Payment Terms Allowed",
            "ATTR-VENDOR-PAYMENT-TERMS",
            "VLIST-S4-PAYMENT-TERMS",
        ),
        (
            "VAL-INCOTERMS-ALLOWED",
            "Incoterms Allowed Values",
            "ATTR-CUSTOMER-INCOTERMS",
            "VLIST-S4-INCOTERMS",
        ),
        (
            "VAL-PARTNER-FUNCTION-ALLOWED",
            "Partner Function Allowed Values",
            "ATTR-CUSTOMER-PARTNER-FUNCTION",
            "VLIST-S4-PARTNER-FUNCTION",
        ),
        (
            "VAL-SHIPPING-CONDITION-ALLOWED",
            "Shipping Condition Allowed Values",
            "ATTR-CUSTOMER-SHIPPING-CONDITIONS",
            "VLIST-S4-SHIPPING-CONDITION",
        ),
        (
            "VAL-COUNTRY-ALLOWED",
            "Country Allowed Values",
            "ATTR-ADDRESS-COUNTRY",
            "VLIST-S4-COUNTRY",
        ),
        ("VAL-REGION-ALLOWED", "Region Allowed Values", "ATTR-ADDRESS-REGION", "VLIST-S4-REGION"),
        ("VAL-CUSTOMER-NUMBER-REQUIRED", "Customer Number Required", "ATTR-CUSTOMER-NUMBER", ""),
        ("VAL-VENDOR-NUMBER-REQUIRED", "Vendor Number Required", "ATTR-VENDOR-NUMBER", ""),
        ("VAL-BP-NUMBER-REQUIRED", "BP Number Required", "ATTR-BUSINESS-PARTNER-NUMBER", ""),
        (
            "VAL-CUSTOMER-TAX-NUMBER-FORMAT",
            "Customer Tax Number Format",
            "ATTR-CUSTOMER-TAX-NUMBER-1",
            "",
        ),
        (
            "VAL-VENDOR-TAX-NUMBER-FORMAT",
            "Vendor Tax Number Format",
            "ATTR-VENDOR-TAX-NUMBER-1",
            "",
        ),
        (
            "VAL-CUSTOMER-VAT-REGISTRATION-FORMAT",
            "Customer VAT Registration Format",
            "ATTR-CUSTOMER-VAT-REGISTRATION",
            "",
        ),
        (
            "VAL-VENDOR-VAT-REGISTRATION-FORMAT",
            "Vendor VAT Registration Format",
            "ATTR-VENDOR-VAT-REGISTRATION",
            "",
        ),
    ]
    for v_id, name, attr_id_val, vl_id in validation_defs:
        fm: dict[str, Any] = {
            "id": v_id,
            "type": "ValidationRule",
            "status": "active",
            "schema_version": SCHEMA_VERSION,
            "name": name,
            "domain": DOMAIN_ID,
            "attribute": attr_id_val,
            "rule_type": "allowed_values" if vl_id else "required",
            "business_owner": "PERSON-BUSINESS-OWNER",
            "data_steward": "PERSON-DATA-STEWARD",
            "description": f"Validation rule for {name.lower()}.",
        }
        if vl_id:
            fm["value_list"] = vl_id
        write_canonical(
            MODEL_DIR / f"{v_id}.md",
            fm,
            f"# {name}\n\nValidation rule ensuring data quality for {attr_id_val}.",
        )

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------
    evidence_items = [
        (
            "EVI-ARCH-001-BP-CENTRAL",
            "BP Central analysis",
            "Architecture analysis supporting BP central decision.",
        ),
        (
            "EVI-DATA-001-CUSTOMER-GROUP",
            "Customer group data profiling",
            "Profiling results for customer group values.",
        ),
        (
            "EVI-DATA-002-VENDOR-ACCOUNT-GROUP",
            "Vendor account group profiling",
            "Profiling results for vendor account group values.",
        ),
        (
            "EVI-DATA-003-PAYMENT-TERMS",
            "Payment terms profiling",
            "Profiling results for payment terms.",
        ),
        (
            "EVI-DATA-004-INDUSTRY-CODE",
            "Industry code profiling",
            "Profiling results for industry codes.",
        ),
        (
            "EVI-MIG-001-DATA-VOLUME",
            "Migration data volume estimate",
            "Estimated data volumes for BP/C/V migration.",
        ),
        (
            "EVI-MIG-002-CUTOVER-WINDOW",
            "Cutover window analysis",
            "Analysis of available cutover windows.",
        ),
        (
            "EVI-RISK-001-DUPLICATE-BP",
            "Duplicate BP risk analysis",
            "Risk analysis for duplicate business partners.",
        ),
        (
            "EVI-RISK-002-TAX-NUMBER-GAPS",
            "Tax number gap analysis",
            "Gap analysis for tax number completeness.",
        ),
        (
            "EVI-CONFIG-001-PARTNER-FUNCTION",
            "Partner function config review",
            "Configuration review for partner functions.",
        ),
    ]
    for e_id, name, description in evidence_items:
        write_canonical(
            MODEL_DIR / f"{e_id}.md",
            {
                "id": e_id,
                "type": "Evidence",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": name,
                "domain": DOMAIN_ID,
                "description": description,
            },
            f"# {name}\n\n{description}",
        )

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------
    decisions = [
        (
            "DEC-ARCH-001-BP-CENTRAL",
            "Business Partner central as canonical master",
            "architecture",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-ARCH-002-CUSTOMER-ROLE",
            "Use Customer role for legacy sold-to/ship-to/bill-to/payer",
            "architecture",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-ARCH-003-VENDOR-ROLE",
            "Use Vendor role for legacy suppliers",
            "architecture",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-DATA-001-CUSTOMER-GROUP-MAP",
            "Map legacy customer groups to S/4 customer groups",
            "data",
            "EVI-DATA-001-CUSTOMER-GROUP",
        ),
        (
            "DEC-DATA-002-VENDOR-ACCOUNT-GROUP-MAP",
            "Map legacy vendor account groups to S/4 groups",
            "data",
            "EVI-DATA-002-VENDOR-ACCOUNT-GROUP",
        ),
        (
            "DEC-DATA-003-PAYMENT-TERMS-HARMONIZE",
            "Harmonize payment terms to S/4 standard",
            "data",
            "EVI-DATA-003-PAYMENT-TERMS",
        ),
        (
            "DEC-DATA-004-INDUSTRY-CODE-MAP",
            "Map legacy industry codes to S/4 industry codes",
            "data",
            "EVI-DATA-004-INDUSTRY-CODE",
        ),
        (
            "DEC-DATA-005-COUNTRY-REGION-ISO",
            "Adopt ISO country/region codes in migration file",
            "data",
            "EVI-DATA-004-INDUSTRY-CODE",
        ),
        (
            "DEC-MIG-001-FILE-STAGING",
            "Use migration file staging for all loads",
            "migration",
            "EVI-MIG-001-DATA-VOLUME",
        ),
        (
            "DEC-MIG-002-CUTOVER-BIG-BANG",
            "Execute big-bang cutover for customer/vendor",
            "migration",
            "EVI-MIG-002-CUTOVER-WINDOW",
        ),
        (
            "DEC-MIG-003-BP-FIRST-ROLE-LATER",
            "Create BP first then assign customer/vendor roles",
            "migration",
            "EVI-MIG-001-DATA-VOLUME",
        ),
        (
            "DEC-GOV-001-DATA-STEWARD-ASSIGN",
            "Assign data steward per domain object",
            "governance",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-GOV-002-OWNER-APPROVAL",
            "Require owner approval for mapping changes",
            "governance",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-TECH-001-CDC-BP-NUMBER",
            "Use CDC to generate BP numbers",
            "technical",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-TECH-002-LEGACY-ID-STORE",
            "Store legacy customer/vendor numbers in reference fields",
            "technical",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-TECH-003-ADDRESS-REUSE",
            "Reuse central address via ADRC",
            "technical",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-QUAL-001-TAX-NUMBER-VALIDATE",
            "Validate tax numbers before load",
            "quality",
            "EVI-RISK-002-TAX-NUMBER-GAPS",
        ),
        (
            "DEC-QUAL-002-DUPLICATE-CHECK",
            "Run duplicate check on BP name/tax",
            "quality",
            "EVI-RISK-001-DUPLICATE-BP",
        ),
        (
            "DEC-QUAL-003-PARTNER-FUNCTION-REQUIRED",
            "Require sold-to and ship-to partner functions",
            "quality",
            "EVI-CONFIG-001-PARTNER-FUNCTION",
        ),
        (
            "DEC-QUAL-004-BANK-DETAILS-VALIDATE",
            "Validate bank details against country rules",
            "quality",
            "EVI-RISK-002-TAX-NUMBER-GAPS",
        ),
        (
            "DEC-QUAL-005-RECON-ACCOUNT-RANGE",
            "Assign reconciliation accounts by account group",
            "quality",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-QUAL-006-ADDRESS-STANDARDIZE",
            "Standardize addresses before migration",
            "quality",
            "EVI-ARCH-001-BP-CENTRAL",
        ),
        (
            "DEC-QUAL-007-PAYMENT-TERMS-DEFAULT",
            "Default payment terms when legacy value missing",
            "quality",
            "EVI-DATA-003-PAYMENT-TERMS",
        ),
        (
            "DEC-QUAL-008-ZERO-BALANCE-CHECK",
            "Exclude vendors with open items from initial load",
            "quality",
            "EVI-RISK-001-DUPLICATE-BP",
        ),
    ]
    for d_id, title, category, evidence in decisions:
        write_canonical(
            MODEL_DIR / f"{d_id}.md",
            {
                "id": d_id,
                "type": "Decision",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "title": title,
                "domain": DOMAIN_ID,
                "decision_category": category,
                "evidence": evidence,
                "business_owner": "PERSON-BUSINESS-OWNER",
                "approver": "PERSON-BUSINESS-OWNER",
                "description": title,
            },
            f"# {title}\n\nApproved decision: {title}.",
        )

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------
    issues = [
        (
            "ISS-DATA-001-CUSTOMER-GROUP-GAP",
            "Customer group configuration gap",
            "high",
            ["ATTR-CUSTOMER-GROUP", "FEP-S4-KNVV-KDGRP", "VMAP-CUSTOMER-GROUP-LEGACY-TO-S4"],
        ),
        (
            "ISS-DATA-002-VENDOR-ACCOUNT-GROUP-GAP",
            "Vendor account group configuration gap",
            "high",
            [
                "ATTR-VENDOR-ACCOUNT-GROUP",
                "FEP-S4-LFA1-KTOKK",
                "VMAP-VENDOR-ACCOUNT-GROUP-LEGACY-TO-S4",
            ],
        ),
        (
            "ISS-DATA-003-PAYMENT-TERMS-GAP",
            "Payment terms mapping incomplete",
            "medium",
            [
                "ATTR-CUSTOMER-PAYMENT-TERMS",
                "ATTR-VENDOR-PAYMENT-TERMS",
                "VMAP-PAYMENT-TERMS-LEGACY-TO-S4",
            ],
        ),
        (
            "ISS-DATA-004-INDUSTRY-CODE-GAP",
            "Industry code coverage gap",
            "medium",
            [
                "ATTR-CUSTOMER-INDUSTRY-CODE",
                "ATTR-VENDOR-INDUSTRY-CODE",
                "VMAP-INDUSTRY-CODE-LEGACY-TO-S4",
            ],
        ),
        (
            "ISS-DATA-005-REGION-CODE-GAP",
            "Legacy region codes not ISO aligned",
            "medium",
            ["ATTR-ADDRESS-REGION", "FEP-S4-ADRC-REGION"],
        ),
        (
            "ISS-DATA-006-COUNTRY-CODE-GAP",
            "Legacy country codes not ISO aligned",
            "medium",
            ["ATTR-ADDRESS-COUNTRY", "FEP-S4-ADRC-COUNTRY"],
        ),
        (
            "ISS-DATA-007-PARTNER-FUNCTION-GAP",
            "Partner function mapping gap",
            "high",
            [
                "ATTR-CUSTOMER-PARTNER-FUNCTION",
                "FEP-S4-KNVP-PARVW",
                "VMAP-PARTNER-FUNCTION-LEGACY-TO-S4",
            ],
        ),
        (
            "ISS-DATA-008-INCOTERMS-GAP",
            "Incoterms mapping gap",
            "medium",
            ["ATTR-CUSTOMER-INCOTERMS", "FEP-S4-KNVV-INCO1", "VMAP-INCOTERMS-LEGACY-TO-S4"],
        ),
        (
            "ISS-DATA-009-SHIPPING-COND-GAP",
            "Shipping condition mapping gap",
            "low",
            [
                "ATTR-CUSTOMER-SHIPPING-CONDITIONS",
                "FEP-S4-KNVV-VSBED",
                "VMAP-SHIPPING-CONDITION-LEGACY-TO-S4",
            ],
        ),
        (
            "ISS-DATA-010-TAX-NUMBER-FORMAT",
            "Tax number format inconsistency",
            "high",
            ["ATTR-CUSTOMER-TAX-NUMBER-1", "ATTR-VENDOR-TAX-NUMBER-1"],
        ),
        (
            "ISS-MIG-001-DATA-VOLUME",
            "High data volume for customer master",
            "high",
            ["MIGOBJ-SAP-BP-CUSTOMER-VENDOR"],
        ),
        (
            "ISS-MIG-002-CUTOVER-RISK",
            "Cutover window shorter than load duration",
            "high",
            ["MIGOBJ-SAP-BP-CUSTOMER-VENDOR"],
        ),
        (
            "ISS-MIG-003-LEGACY-SYSTEM-ACCESS",
            "Legacy ERP access limited during cutover",
            "medium",
            ["SYS-LEGACY-ERP"],
        ),
        (
            "ISS-MIG-004-DATA-STEWARD-AVAILABILITY",
            "Data steward availability during validation",
            "medium",
            ["PERSON-DATA-STEWARD"],
        ),
        (
            "ISS-QUAL-001-DUPLICATE-BP",
            "Duplicate business partner candidates",
            "high",
            ["ATTR-BUSINESS-PARTNER-NAME", "ATTR-BUSINESS-PARTNER-TAX-NUMBER-1"],
        ),
        (
            "ISS-QUAL-002-MISSING-BANK-DETAILS",
            "Customer bank details incomplete",
            "medium",
            ["ATTR-CUSTOMER-BANK-COUNTRY", "ATTR-CUSTOMER-BANK-KEY", "ATTR-CUSTOMER-BANK-ACCOUNT"],
        ),
        (
            "ISS-QUAL-003-MISSING-CONTACT",
            "Customer contact person missing",
            "low",
            ["ATTR-CUSTOMER-CONTACT-FIRST-NAME", "ATTR-CUSTOMER-CONTACT-LAST-NAME"],
        ),
        (
            "ISS-QUAL-004-RECON-ACCOUNT-GAP",
            "Reconciliation account assignment unclear",
            "high",
            ["ATTR-CUSTOMER-RECONCILIATION-ACCOUNT", "ATTR-VENDOR-RECONCILIATION-ACCOUNT"],
        ),
        (
            "ISS-QUAL-005-ADDRESS-STANDARDIZATION",
            "Addresses require standardization",
            "medium",
            ["ATTR-ADDRESS-STREET", "ATTR-ADDRESS-CITY", "ATTR-ADDRESS-POSTAL-CODE"],
        ),
        (
            "ISS-QUAL-006-VENDOR-BLOCKS",
            "Vendor block flags need review",
            "medium",
            ["ATTR-VENDOR-LOCK-FLAG", "ATTR-VENDOR-PURCHASING-BLOCK"],
        ),
        (
            "ISS-QUAL-007-CUSTOMER-BLOCKS",
            "Customer block flags need review",
            "medium",
            ["ATTR-CUSTOMER-LOCK-FLAG", "ATTR-BUSINESS-PARTNER-CENTRAL-BLOCK"],
        ),
        (
            "ISS-QUAL-008-VAT-REGISTRATION-GAPS",
            "VAT registration gaps for EU vendors",
            "high",
            ["ATTR-VENDOR-VAT-REGISTRATION", "ATTR-CUSTOMER-VAT-REGISTRATION"],
        ),
    ]
    for i_id, title, priority, affected in issues:
        write_canonical(
            MODEL_DIR / f"{i_id}.md",
            {
                "id": i_id,
                "type": "Issue",
                "status": "open",
                "schema_version": SCHEMA_VERSION,
                "title": title,
                "domain": DOMAIN_ID,
                "priority": priority,
                "business_owner": "PERSON-BUSINESS-OWNER",
                "affected_objects": affected,
                "description": title,
            },
            f"# {title}\n\nOpen issue tracking {title.lower()}.",
        )

    # ------------------------------------------------------------------
    # Datasets
    # ------------------------------------------------------------------
    datasets = [
        (
            "DS-CUSTOMER-EXTRACT",
            "customer_extract.csv",
            "SYS-LEGACY-ERP",
            "Legacy customer master extract.",
        ),
        (
            "DS-VENDOR-EXTRACT",
            "vendor_extract.csv",
            "SYS-LEGACY-ERP",
            "Legacy vendor master extract.",
        ),
        (
            "DS-CRM-CONTACT-EXTRACT",
            "crm_contacts.csv",
            "SYS-LEGACY-CRM",
            "Legacy CRM contact extract.",
        ),
        (
            "DS-VENDOR-PORTAL-EXTRACT",
            "vendor_portal.csv",
            "SYS-LEGACY-VENDOR-PORTAL",
            "Legacy vendor portal extract.",
        ),
        (
            "DS-MIGRATION-STAGING",
            "migration_staging.csv",
            "SYS-MIGRATION-FILE",
            "Consolidated migration staging file.",
        ),
    ]
    for ds_id, filename, system, description in datasets:
        write_canonical(
            MODEL_DIR / f"{ds_id}.md",
            {
                "id": ds_id,
                "type": "Dataset",
                "status": "active",
                "schema_version": SCHEMA_VERSION,
                "name": filename,
                "domain": DOMAIN_ID,
                "system": system,
                "business_owner": "PERSON-BUSINESS-OWNER",
                "data_steward": "PERSON-DATA-STEWARD",
                "description": description,
            },
            f"# {filename}\n\n{description}",
        )

    # ------------------------------------------------------------------
    # Repository config
    # ------------------------------------------------------------------
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "schema_version": SCHEMA_VERSION,
        "workspace_name": "SAP BP Customer Vendor Reference",
        "description": (
            "Reference model for SAP Business Partner / Customer / Vendor commercial demos."
        ),
        "enabled_domain_packs": ["sap"],
    }
    CONFIG_PATH.write_text(_dump_yaml(config), encoding="utf-8")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    files = sorted(MODEL_DIR.glob("*.md"))
    print(f"Generated {len(files)} canonical objects in {MODEL_DIR}")
    print(f"Repository config written to {CONFIG_PATH}")
    print(f"Attribute usages written: {usage_count}")


if __name__ == "__main__":
    main()

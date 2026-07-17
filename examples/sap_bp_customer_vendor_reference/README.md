# Synthetic SAP Business Partner Migration Reference

This is a deliberately synthetic reference model for demonstrating Martenweave locally. Names,
organizations, codes, records, findings, decisions, interfaces, and example values are fictional;
the model must not be used as SAP implementation advice or production master data.

It models an illustrative migration from legacy CRM and ERP extracts, through a mapping-workbook
and flat-file staging interface, into SAP S/4HANA Business Partner, Customer, and Vendor contexts.
The canonical model includes attributes, entities, SAP table-field endpoints, mappings, evidence,
issues, decisions, ownership, interfaces, transformations, and reviewable proposals. The committed
`generated/` directory is disposable sample output, not canonical truth.

## Reproduce the model slice

Run from the repository root:

```bash
martenweave validate --repo examples/sap_bp_customer_vendor_reference
martenweave build-index --repo examples/sap_bp_customer_vendor_reference --jsonl
martenweave index-fresh --repo examples/sap_bp_customer_vendor_reference
martenweave search "Customer Group" --repo examples/sap_bp_customer_vendor_reference
martenweave trace ATTR-CUSTOMER-GROUP --repo examples/sap_bp_customer_vendor_reference
martenweave impact FEP-S4-KNVV-KDGRP --repo examples/sap_bp_customer_vendor_reference
martenweave health --repo examples/sap_bp_customer_vendor_reference
martenweave gap-report --repo examples/sap_bp_customer_vendor_reference
```

The expected outcome is a valid canonical model with reproducible index, lineage, impact, health,
and model-side gap outputs. Review the `ISS-*`, `EVI-*`, and `DEC-*` objects to follow the evidence
and decision trail. Use `martenweave docs-build` to generate a local read-only viewer; it never
modifies the canonical `model/` files.

For a dataset-readiness and PatchProposal walkthrough with clean and intentionally problematic
input files, use [`docs/demo-quickstart-flow.md`](../../docs/demo-quickstart-flow.md) and the
`examples/customer_bp_model` fixture. That fixture keeps invalid examples outside this golden
reference model so normal validation remains green.

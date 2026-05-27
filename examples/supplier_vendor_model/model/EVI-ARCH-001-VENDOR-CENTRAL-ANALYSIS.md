---
id: EVI-ARCH-001-VENDOR-CENTRAL-ANALYSIS
type: Evidence
status: active
schema_version: "1.0"
title: Vendor Central Architecture Analysis Evidence
domain: DOMAIN-SUPPLIER-VENDOR
---

# Vendor Central Architecture Analysis Evidence

This evidence object captures the architectural analysis for supplier/vendor master data centralization.

## Findings

- LFA1 serves as the central vendor master table in SAP S/4HANA.
- LFB1 holds company-code-dependent data (payment terms, reconciliation account).
- LFM1 holds purchasing-organization-dependent data (purchasing block).
- All three tables share the same vendor number key (LIFNR).

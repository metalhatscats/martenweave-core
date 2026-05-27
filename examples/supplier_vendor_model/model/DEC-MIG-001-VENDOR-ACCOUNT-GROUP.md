---
id: DEC-MIG-001-VENDOR-ACCOUNT-GROUP
type: Decision
status: active
schema_version: "1.0"
title: Legacy vendor account group mapping to S/4HANA
domain: DOMAIN-SUPPLIER-VENDOR
evidence: EVI-MIG-001-ACCOUNT-GROUP-ANALYSIS
decision_category: data_model
data_steward: PERSON-DATA-STEWARD-VENDOR
description: >
  Legacy vendor account group codes (01, 02, 03) map directly to S/4HANA
  target codes (0001, 0002, 0003). Any unmapped legacy codes will be
  routed to the default domestic vendor group 0001 and flagged for review.
---

# Legacy Vendor Account Group Mapping to S/4HANA

This decision records the rationale for mapping legacy vendor account group
codes to S/4HANA target values during migration. Based on the gap analysis
evidence, the direct one-to-one mapping covers all known legacy codes.

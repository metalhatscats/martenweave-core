---
id: ISS-MIG-001-ACCOUNT-GROUP-GAP
type: Issue
status: open
schema_version: "1.0"
title: Legacy vendor account group 04 and 05 unmapped
priority: medium
domain: DOMAIN-SUPPLIER-VENDOR
affected_objects:
  - ATTR-VENDOR-ACCOUNT-GROUP
  - FEP-S4-LFA1-KTOKK
  - VMAP-LEGACY-TO-S4-VENDOR-ACCOUNT-GROUP
  - VLIST-LEGACY-VENDOR-ACCOUNT-GROUP
data_steward: PERSON-DATA-STEWARD-VENDOR
description: >
  Testing revealed that legacy vendor account group codes 04 (Intercompany)
  and 05 (Employee) are not covered by the current value mapping.
  These codes need additional target values or fallback rules.
---

# Legacy Vendor Account Group 04 and 05 Unmapped

During testing, the migration team discovered that vendor account group codes
04 (Intercompany) and 05 (Employee) from the legacy system have no corresponding
target values in S/4HANA. This issue tracks the gap until resolved.

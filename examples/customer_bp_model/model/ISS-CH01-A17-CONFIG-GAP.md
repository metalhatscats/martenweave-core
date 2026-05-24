---
id: ISS-CH01-A17-CONFIG-GAP
type: Issue
status: open
title: CH01 / A17 Customer Group configuration gap
domain: DOMAIN-CUSTOMER-BP
priority: high
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - FEP-S4-KNVV-KDGRP
  - VMAP-CUST-GROUP-LEGACY-TO-S4
  - VAL-CUST-GROUP-ALLOWED-VALUES
description: >
  Testing revealed that Customer Group values for CH01 / A17 are not fully
  covered by the current model. Legacy values may not map cleanly to S/4HANA
  target values, and the allowed-value list may be incomplete.
---

# CH01 / A17 Customer Group Configuration Gap

During testing, the migration team discovered that Customer Group handling
for CH01 / A17 needs additional mapping rules, value list entries, or
configuration exceptions. This issue tracks the gap until resolved.

---
id: VMAP-CUST-GROUP-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: "1.0"
name: Customer Group Legacy-to-S/4 Value Mapping
domain: DOMAIN-CUSTOMER-BP
mapping: MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
source_value_list: VLIST-LEGACY-CUST-GROUP
target_value_list: VLIST-S4-CUST-GROUP
business_owner: PERSON-DATA-STEWARD
technical_owner: PERSON-DATA-STEWARD
entries:
  - source_code: CH01
    target_code: "01"
    description: Direct sales -> Wholesale
  - source_code: CH02
    target_code: "02"
    description: Partner sales -> Retail
  - source_code: A17
    target_code: "03"
    fallback: true
    description: Special legacy -> Export (fallback)
description: >
  Value-level mapping for Customer Group from legacy codes to S/4HANA codes.
  CH01 and A17 require special handling.
---

# Customer Group Legacy-to-S/4 Value Mapping

Maps individual legacy customer group codes to their S/4HANA equivalents.
Special attention needed for CH01 / A17 configuration gaps.

---
id: VMAP-DEMO-NIMBUS-GROUP-TO-HUB
type: ValueMapping
status: active
schema_version: "1.0"
name: Nimbus Sales Group to Atlas Hub Group
domain: DOMAIN-CUSTOMER-MIGRATION
source_value_list: VLIST-DEMO-NIMBUS-GROUPS
target_value_list: VLIST-DEMO-HUB-GROUPS
entries:
  - source_code: PREMIUM
    target_code: TIER_1
  - source_code: GROWTH
    target_code: TIER_2
  - source_code: CORE
    target_code: TIER_3
description: Explicit synthetic normalization of CRM sales labels into hub groups.
---

# Nimbus Sales Group to Atlas Hub Group

The fictional transformation is visible and testable as a separate artifact.

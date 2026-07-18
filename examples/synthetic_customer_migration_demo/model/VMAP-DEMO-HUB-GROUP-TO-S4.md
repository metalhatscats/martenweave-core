---
id: VMAP-DEMO-HUB-GROUP-TO-S4
type: ValueMapping
status: active
schema_version: "1.0"
name: Atlas Hub Group to SAP Customer Group
domain: DOMAIN-CUSTOMER-MIGRATION
source_value_list: VLIST-DEMO-HUB-GROUPS
target_value_list: VLIST-DEMO-S4-GROUPS
entries:
  - source_code: TIER_1
    target_code: A17
  - source_code: TIER_2
    target_code: B02
  - source_code: TIER_3
    target_code: C11
description: Explicit synthetic mapping from controlled hub groups to SAP-like target codes.
---

# Atlas Hub Group to SAP Customer Group

Shows the final code conversion as reviewable model evidence.

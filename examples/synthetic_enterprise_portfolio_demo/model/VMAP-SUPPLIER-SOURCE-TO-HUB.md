---
id: VMAP-SUPPLIER-SOURCE-TO-HUB
type: ValueMapping
status: active
schema_version: "1.0"
name: Supplier source values to hub values
domain: DOMAIN-SUPPLIER
source_value_list: VLIST-SUPPLIER-STATUS
target_value_list: VLIST-SUPPLIER-STATUS
entries:
  - {'source_code': 'ACTIVE', 'target_code': 'ACTIVE'}
  - {'source_code': 'REVIEW', 'target_code': 'REVIEW'}
business_owner: PERSON-SUPPLIER-OWNER
data_steward: PERSON-CHIEF-STEWARD
description: Controlled synthetic value crosswalk for supplier source values.
---

# VMAP-SUPPLIER-SOURCE-TO-HUB

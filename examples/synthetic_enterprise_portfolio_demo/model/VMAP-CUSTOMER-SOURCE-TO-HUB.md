---
id: VMAP-CUSTOMER-SOURCE-TO-HUB
type: ValueMapping
status: active
schema_version: "1.0"
name: Customer source values to hub values
domain: DOMAIN-CUSTOMER
source_value_list: VLIST-CUSTOMER-STATUS
target_value_list: VLIST-CUSTOMER-STATUS
entries:
  - {'source_code': 'ACTIVE', 'target_code': 'ACTIVE'}
  - {'source_code': 'REVIEW', 'target_code': 'REVIEW'}
business_owner: PERSON-CUSTOMER-OWNER
data_steward: PERSON-CHIEF-STEWARD
description: Controlled synthetic value crosswalk for customer source values.
---

# VMAP-CUSTOMER-SOURCE-TO-HUB

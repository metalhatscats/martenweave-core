---
id: VMAP-SHIPPING-CONDITION-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: '1.0'
name: Shipping Condition Legacy To S4
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
source_value_list: VLIST-LEGACY-SHIPPING-CONDITION
target_value_list: VLIST-S4-SHIPPING-CONDITION
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
entries:
- source_code: STD
  target_code: '01'
  description: Standard
  fallback: false
- source_code: EXP
  target_code: '02'
  description: Express
  fallback: false
- source_code: PU
  target_code: '03'
  description: Pick-up
  fallback: true
---

# VMAP-SHIPPING-CONDITION-LEGACY-TO-S4

Value mapping from VLIST-LEGACY-SHIPPING-CONDITION to VLIST-S4-SHIPPING-CONDITION.

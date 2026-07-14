---
id: VMAP-CUSTOMER-GROUP-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: '1.0'
name: Customer Group Legacy To S4
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
source_value_list: VLIST-LEGACY-CUSTOMER-GROUP
target_value_list: VLIST-S4-CUSTOMER-GROUP
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
entries:
- source_code: CH01
  target_code: '01'
  description: Channel 01 -> Wholesale
  fallback: false
- source_code: CH02
  target_code: '02'
  description: Channel 02 -> Retail
  fallback: false
- source_code: A17
  target_code: '03'
  description: Area 17 -> Export fallback
  fallback: false
- source_code: ZZ
  target_code: '04'
  description: Unknown -> Internal
  fallback: true
---

# VMAP-CUSTOMER-GROUP-LEGACY-TO-S4

Value mapping from VLIST-LEGACY-CUSTOMER-GROUP to VLIST-S4-CUSTOMER-GROUP.

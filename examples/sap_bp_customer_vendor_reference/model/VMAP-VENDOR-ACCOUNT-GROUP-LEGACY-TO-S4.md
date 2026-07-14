---
id: VMAP-VENDOR-ACCOUNT-GROUP-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: '1.0'
name: Vendor Account Group Legacy To S4
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
source_value_list: VLIST-LEGACY-VENDOR-ACCOUNT-GROUP
target_value_list: VLIST-S4-VENDOR-ACCOUNT-GROUP
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
entries:
- source_code: V01
  target_code: '0001'
  description: Domestic vendor
  fallback: false
- source_code: V02
  target_code: '0002'
  description: Foreign vendor
  fallback: false
- source_code: V03
  target_code: '0003'
  description: One-time vendor
  fallback: false
- source_code: V99
  target_code: '0004'
  description: Misc -> Employee vendor
  fallback: true
---

# VMAP-VENDOR-ACCOUNT-GROUP-LEGACY-TO-S4

Value mapping from VLIST-LEGACY-VENDOR-ACCOUNT-GROUP to VLIST-S4-VENDOR-ACCOUNT-GROUP.

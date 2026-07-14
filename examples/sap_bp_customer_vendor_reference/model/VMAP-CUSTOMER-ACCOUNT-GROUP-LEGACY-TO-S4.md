---
id: VMAP-CUSTOMER-ACCOUNT-GROUP-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: '1.0'
name: Customer Account Group Legacy To S4
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
source_value_list: VLIST-LEGACY-CUSTOMER-ACCOUNT-GROUP
target_value_list: VLIST-S4-CUSTOMER-ACCOUNT-GROUP
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
entries:
- source_code: C01
  target_code: '0001'
  description: Sold-to
  fallback: false
- source_code: C02
  target_code: '0002'
  description: Ship-to
  fallback: false
- source_code: C03
  target_code: '0003'
  description: Bill-to
  fallback: true
---

# VMAP-CUSTOMER-ACCOUNT-GROUP-LEGACY-TO-S4

Value mapping from VLIST-LEGACY-CUSTOMER-ACCOUNT-GROUP to VLIST-S4-CUSTOMER-ACCOUNT-GROUP.

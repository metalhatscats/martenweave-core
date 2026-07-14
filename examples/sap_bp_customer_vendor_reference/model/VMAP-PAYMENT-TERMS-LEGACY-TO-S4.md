---
id: VMAP-PAYMENT-TERMS-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: '1.0'
name: Payment Terms Legacy To S4
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
source_value_list: VLIST-LEGACY-PAYMENT-TERMS
target_value_list: VLIST-S4-PAYMENT-TERMS
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
entries:
- source_code: PI
  target_code: '0001'
  description: Payable immediately
  fallback: false
- source_code: 14D2
  target_code: '0002'
  description: 14 days 2%
  fallback: false
- source_code: 30D
  target_code: '0003'
  description: 30 days net
  fallback: false
- source_code: 60D
  target_code: '0004'
  description: 60 days net
  fallback: true
---

# VMAP-PAYMENT-TERMS-LEGACY-TO-S4

Value mapping from VLIST-LEGACY-PAYMENT-TERMS to VLIST-S4-PAYMENT-TERMS.

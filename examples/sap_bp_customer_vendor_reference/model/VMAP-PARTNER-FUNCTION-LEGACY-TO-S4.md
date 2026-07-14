---
id: VMAP-PARTNER-FUNCTION-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: '1.0'
name: Partner Function Legacy To S4
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
source_value_list: VLIST-LEGACY-PARTNER-FUNCTION
target_value_list: VLIST-S4-PARTNER-FUNCTION
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
entries:
- source_code: SOLD
  target_code: AG
  description: Sold-to
  fallback: false
- source_code: SHIP
  target_code: WE
  description: Ship-to
  fallback: false
- source_code: BILL
  target_code: RE
  description: Bill-to
  fallback: false
- source_code: PAY
  target_code: RG
  description: Payer
  fallback: true
---

# VMAP-PARTNER-FUNCTION-LEGACY-TO-S4

Value mapping from VLIST-LEGACY-PARTNER-FUNCTION to VLIST-S4-PARTNER-FUNCTION.

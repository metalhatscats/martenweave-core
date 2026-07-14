---
id: VMAP-INCOTERMS-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: '1.0'
name: Incoterms Legacy To S4
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
source_value_list: VLIST-LEGACY-INCOTERMS
target_value_list: VLIST-S4-INCOTERMS
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
entries:
- source_code: EX
  target_code: EXW
  description: Ex works
  fallback: false
- source_code: FB
  target_code: FOB
  description: Free on board
  fallback: false
- source_code: CF
  target_code: CIF
  description: Cost insurance freight
  fallback: false
- source_code: DP
  target_code: DDP
  description: Delivered duty paid
  fallback: true
---

# VMAP-INCOTERMS-LEGACY-TO-S4

Value mapping from VLIST-LEGACY-INCOTERMS to VLIST-S4-INCOTERMS.

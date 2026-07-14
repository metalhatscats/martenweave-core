---
id: VMAP-INDUSTRY-CODE-LEGACY-TO-S4
type: ValueMapping
status: draft
schema_version: '1.0'
name: Industry Code Legacy To S4
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
source_value_list: VLIST-LEGACY-INDUSTRY-CODE
target_value_list: VLIST-S4-INDUSTRY-CODE
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
entries:
- source_code: MFG
  target_code: '1000'
  description: Manufacturing
  fallback: false
- source_code: RET
  target_code: '2000'
  description: Retail
  fallback: false
- source_code: SRV
  target_code: '3000'
  description: Services
  fallback: false
- source_code: TECH
  target_code: '4000'
  description: Technology
  fallback: false
- source_code: FIN
  target_code: '5000'
  description: Finance
  fallback: true
---

# VMAP-INDUSTRY-CODE-LEGACY-TO-S4

Value mapping from VLIST-LEGACY-INDUSTRY-CODE to VLIST-S4-INDUSTRY-CODE.

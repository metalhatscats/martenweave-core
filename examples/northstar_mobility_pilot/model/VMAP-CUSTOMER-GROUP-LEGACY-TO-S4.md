---
id: VMAP-CUSTOMER-GROUP-LEGACY-TO-S4
type: ValueMapping
status: active
schema_version: '1.0'
name: Customer Group Legacy-to-S/4 Value Mapping
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-BP-CUSTOMER
source_value_list: VLIST-LEGACY-CUSTOMER-GROUPS
target_value_list: VLIST-S4-CUSTOMER-GROUPS
business_owner: PERSON-CUSTOMER-STEWARD
technical_owner: PERSON-CUSTOMER-STEWARD
entries:
- source_code: GOLD
  target_code: '04'
  description: Gold tier maps to Strategic Partners.
- source_code: SILVER
  target_code: '02'
  description: Silver tier maps to Retail & Rental.
- source_code: STANDARD
  target_code: '02'
  description: Standard tier maps to Retail & Rental.
- source_code: FLEET
  target_code: '01'
  description: Fleet accounts map to Wholesale Fleet.
description: Value-level conversion from Northstar CRM group codes to S/4HANA groups.
---

# Customer Group Legacy-to-S/4 Value Mapping

Value-level conversion from Northstar CRM group codes to S/4HANA groups.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

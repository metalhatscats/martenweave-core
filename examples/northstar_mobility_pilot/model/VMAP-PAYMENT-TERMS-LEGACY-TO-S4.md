---
id: VMAP-PAYMENT-TERMS-LEGACY-TO-S4
type: ValueMapping
status: active
schema_version: '1.0'
name: Payment Terms Legacy-to-S/4 Value Mapping
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-SUPPLIER
source_value_list: VLIST-LEGACY-PAYMENT-TERMS
target_value_list: VLIST-S4-PAYMENT-TERMS
business_owner: PERSON-SUPPLIER-STEWARD
technical_owner: PERSON-SUPPLIER-STEWARD
entries:
- source_code: P15
  target_code: NT15
  description: 15-day terms.
- source_code: P30
  target_code: NT30
  description: 30-day terms.
- source_code: P45
  target_code: NT45
  description: 45-day terms.
- source_code: P60
  target_code: NT60
  description: 60-day terms.
description: Shared conversion for legacy payment-terms codes used by supplier master, purchase orders,
  and FI open items alike.
---

# Payment Terms Legacy-to-S/4 Value Mapping

Shared conversion for legacy payment-terms codes used by supplier master, purchase orders, and FI open items alike.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

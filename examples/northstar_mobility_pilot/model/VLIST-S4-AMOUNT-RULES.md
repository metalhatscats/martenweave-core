---
id: VLIST-S4-AMOUNT-RULES
type: ValueList
status: active
schema_version: '1.0'
name: Amount and Quantity Rules
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-FINANCE
value_list_type: domain
business_owner: PERSON-GOVERNANCE-REVIEWER
data_steward: PERSON-GOVERNANCE-REVIEWER
entries:
- code: POSITIVE-ONLY
  label: Positive Only
  description: Amount must be greater than zero.
  sort_order: 1
  is_active: true
- code: NON-NEGATIVE
  label: Non Negative
  description: Amount must be zero or greater.
  sort_order: 2
  is_active: true
description: Range contract list for amount and quantity fields; records the allowed sign rather than
  enumerating values.
---

# Amount and Quantity Rules

Range contract list for amount and quantity fields; records the allowed sign rather than enumerating values.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

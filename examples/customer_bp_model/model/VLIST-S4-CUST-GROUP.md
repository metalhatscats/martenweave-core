---
id: VLIST-S4-CUST-GROUP
type: ValueList
status: active
schema_version: "1.0"
name: S/4 Customer Group Values
value_list_type: domain
domain: DOMAIN-CUSTOMER-BP
business_owner: PERSON-DATA-STEWARD
entries:
  - code: "01"
    label: Wholesale
    description: Wholesale customers
    sort_order: 1
    is_default: true
    is_active: true
  - code: "02"
    label: Retail
    description: Retail customers
    sort_order: 2
    is_active: true
  - code: "03"
    label: Export
    description: Export customers
    sort_order: 3
    is_active: true
description: >
  Allowed Customer Group values in the S/4HANA target system.
---

# S/4 Customer Group Value List

Contains the canonical set of Customer Group codes valid in S/4HANA.

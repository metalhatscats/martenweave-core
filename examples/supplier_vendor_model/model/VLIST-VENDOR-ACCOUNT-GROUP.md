---
id: VLIST-VENDOR-ACCOUNT-GROUP
type: ValueList
status: active
schema_version: "1.0"
name: Vendor Account Group Values
value_list_type: domain
domain: DOMAIN-SUPPLIER-VENDOR
data_steward: PERSON-DATA-STEWARD-VENDOR
entries:
  - code: "0001"
    label: Domestic Vendor
    description: Domestic standard vendor
    sort_order: 1
    is_active: true
  - code: "0002"
    label: Foreign Vendor
    description: Foreign standard vendor
    sort_order: 2
    is_active: true
  - code: "0003"
    label: One-Time Vendor
    description: One-time vendor for occasional purchases
    sort_order: 3
    is_active: true
---

# Vendor Account Group Value List

Allowed vendor account group codes in the S/4HANA target system.

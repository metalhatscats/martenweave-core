---
id: VMAP-LEGACY-TO-S4-VENDOR-ACCOUNT-GROUP
type: ValueMapping
status: active
schema_version: "1.0"
name: Legacy to S/4 Vendor Account Group Mapping
domain: DOMAIN-SUPPLIER-VENDOR
value_list: VLIST-VENDOR-ACCOUNT-GROUP
source_value_list: VLIST-LEGACY-VENDOR-ACCOUNT-GROUP
target_value_list: VLIST-VENDOR-ACCOUNT-GROUP
entries:
  - source_code: "01"
    target_code: "0001"
    description: Domestic vendor
    fallback: false
  - source_code: "02"
    target_code: "0002"
    description: Foreign vendor
    fallback: false
  - source_code: "03"
    target_code: "0003"
    description: One-time vendor
    fallback: false
---

# Legacy to S/4 Vendor Account Group Mapping

Maps legacy vendor account group codes to S/4HANA target codes.

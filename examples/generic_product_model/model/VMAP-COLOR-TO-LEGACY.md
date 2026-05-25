---
schema_version: "1.0"
id: VMAP-COLOR-TO-LEGACY
type: ValueMapping
status: active
name: Product Color to Legacy Mapping
domain: DOMAIN-PRODUCT
source_value_list: VLIST-PRODUCT-COLOR
target_value_list: VLIST-PRODUCT-COLOR-LEGACY
business_owner: PERSON-PRODUCT-OWNER
entries:
  - source_code: RED
    target_code: R01
    description: Red -> Legacy R01
  - source_code: GRN
    target_code: G02
    description: Green -> Legacy G02
  - source_code: BLU
    target_code: B03
    description: Blue -> Legacy B03
description: >
  Maps canonical product colors to legacy system codes.
---

# Product Color to Legacy Mapping

Maps canonical colors to legacy warehouse system codes.

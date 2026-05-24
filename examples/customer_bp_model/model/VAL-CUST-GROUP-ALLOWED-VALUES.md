---
id: VAL-CUST-GROUP-ALLOWED-VALUES
type: ValidationRule
status: active
name: Customer Group Allowed Values
domain: DOMAIN-CUSTOMER-BP
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
value_list: VLIST-S4-CUST-GROUP
rule_type: allowed_values
description: >
  Validates that Customer Group values are within the allowed S/4HANA value list.
---

# Customer Group Allowed Values Validation

Ensures every Customer Group value in the migrated data exists in the
S/4HANA allowed value list. Flags unknown or unmapped legacy values.

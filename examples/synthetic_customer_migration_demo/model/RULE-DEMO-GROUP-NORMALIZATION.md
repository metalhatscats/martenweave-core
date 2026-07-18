---
id: RULE-DEMO-GROUP-NORMALIZATION
type: TransformationRule
status: active
schema_version: "1.0"
name: Synthetic Customer Group Normalization
domain: DOMAIN-CUSTOMER-MIGRATION
source_field_endpoint: FEP-DEMO-NIMBUS-SALES-GROUP
target_field_endpoint: FEP-DEMO-HUB-NORMALIZED-GROUP
attribute: ATTR-CUSTOMER-GROUP
rule_type: value_normalization
description: Demo rule that converts fictional CRM labels into controlled hub values before SAP mapping.
---

# Synthetic Customer Group Normalization

Keeps the business transform explicit and independently testable.

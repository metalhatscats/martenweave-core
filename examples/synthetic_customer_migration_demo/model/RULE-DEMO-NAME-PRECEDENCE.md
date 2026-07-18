---
id: RULE-DEMO-NAME-PRECEDENCE
type: TransformationRule
status: active
schema_version: "1.0"
name: Synthetic Golden Name Precedence
domain: DOMAIN-CUSTOMER-MIGRATION
source_field_endpoint: FEP-DEMO-NIMBUS-CUSTOMER-NAME
target_field_endpoint: FEP-DEMO-HUB-GOLDEN-NAME
attribute: ATTR-CUSTOMER-NAME
rule_type: source_precedence
description: Demo rule that prefers the CRM legal name and retains the commerce name as evidence for review.
---

# Synthetic Golden Name Precedence

Uses fictional sources to show that reconciliation logic can be reviewed separately from a load.

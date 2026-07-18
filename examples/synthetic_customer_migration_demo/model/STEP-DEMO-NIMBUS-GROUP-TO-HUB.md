---
id: STEP-DEMO-NIMBUS-GROUP-TO-HUB
type: DataFlowStep
status: active
schema_version: "1.0"
name: Normalize Nimbus Sales Group in Hub
domain: DOMAIN-CUSTOMER-MIGRATION
integration_flow: FLOW-DEMO-NIMBUS-TO-HUB
source_field_endpoint: FEP-DEMO-NIMBUS-SALES-GROUP
target_field_endpoint: FEP-DEMO-HUB-NORMALIZED-GROUP
transformation_rule: RULE-DEMO-GROUP-NORMALIZATION
target_step: STEP-DEMO-HUB-GROUP-TO-S4
step_type: transform
description: Converts a fictional CRM sales label into a controlled hub group.
---

# Normalize Nimbus Sales Group in Hub

The next step sends the explicit controlled group to the SAP target.

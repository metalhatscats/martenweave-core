---
id: STEP-DEMO-NIMBUS-NAME-TO-HUB
type: DataFlowStep
status: active
schema_version: "1.0"
name: Harmonize Nimbus Legal Name in Hub
domain: DOMAIN-CUSTOMER-MIGRATION
integration_flow: FLOW-DEMO-NIMBUS-TO-HUB
source_step: STEP-DEMO-NIMBUS-ID-TO-HUB
source_field_endpoint: FEP-DEMO-NIMBUS-CUSTOMER-NAME
target_field_endpoint: FEP-DEMO-HUB-GOLDEN-NAME
transformation_rule: RULE-DEMO-NAME-PRECEDENCE
step_type: transform
description: Applies the fictional golden-name precedence rule in the controlled hub.
---

# Harmonize Nimbus Legal Name in Hub

Makes the name-precedence transform traceable from CRM to the golden record.

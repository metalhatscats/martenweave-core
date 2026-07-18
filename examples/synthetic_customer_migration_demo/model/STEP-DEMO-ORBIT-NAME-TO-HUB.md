---
id: STEP-DEMO-ORBIT-NAME-TO-HUB
type: DataFlowStep
status: active
schema_version: "1.0"
name: Compare Orbit Display Name in Hub
domain: DOMAIN-CUSTOMER-MIGRATION
integration_flow: FLOW-DEMO-ORBIT-TO-HUB
source_field_endpoint: FEP-DEMO-ORBIT-DISPLAY-NAME
target_field_endpoint: FEP-DEMO-HUB-GOLDEN-NAME
transformation_rule: RULE-DEMO-NAME-PRECEDENCE
step_type: validate
description: Contributes a fictional second source name to the golden-name review.
---

# Compare Orbit Display Name in Hub

Provides a second named source without exposing any real customer data.

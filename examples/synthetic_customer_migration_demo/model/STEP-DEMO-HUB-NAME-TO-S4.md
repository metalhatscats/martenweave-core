---
id: STEP-DEMO-HUB-NAME-TO-S4
type: DataFlowStep
status: active
schema_version: "1.0"
name: Load Golden Name to SAP Customer Master
domain: DOMAIN-CUSTOMER-MIGRATION
integration_flow: FLOW-DEMO-HUB-TO-S4
source_step: STEP-DEMO-NIMBUS-NAME-TO-HUB
source_field_endpoint: FEP-DEMO-HUB-GOLDEN-NAME
target_field_endpoint: FEP-S4-KNA1-NAME1
step_type: load
description: Loads the approved synthetic golden name into the SAP target field.
---

# Load Golden Name to SAP Customer Master

Controlled target step for the fictional customer-name route.

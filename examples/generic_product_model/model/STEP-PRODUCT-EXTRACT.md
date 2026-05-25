---
schema_version: "1.0"
id: STEP-PRODUCT-EXTRACT
type: DataFlowStep
status: active
name: Extract Product Changes
domain: DOMAIN-PRODUCT
integration_flow: FLOW-PRODUCT-TO-ECOMMERCE
target_step: STEP-PRODUCT-TRANSFORM
step_type: extract
---

# Extract Product Changes

Extract step that reads delta product records from the ERP export endpoint.

---
schema_version: "1.0"
id: STEP-PRODUCT-TRANSFORM
type: DataFlowStep
status: active
name: Transform Product Data
domain: DOMAIN-PRODUCT
integration_flow: FLOW-PRODUCT-TO-ECOMMERCE
target_step: STEP-PRODUCT-LOAD
transformation_rule: TRULE-PRODUCT-PRICE-FORMAT
step_type: transform
---

# Transform Product Data

Transform step that applies business rules, currency conversion, and price formatting.

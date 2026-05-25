---
schema_version: "1.0"
id: STEP-PRODUCT-LOAD
type: DataFlowStep
status: active
name: Load Product Data
domain: DOMAIN-PRODUCT
integration_flow: FLOW-PRODUCT-TO-ECOMMERCE
source_step: STEP-PRODUCT-TRANSFORM
step_type: load
---

# Load Product Data

Load step that writes transformed product records into the e-commerce product catalog.

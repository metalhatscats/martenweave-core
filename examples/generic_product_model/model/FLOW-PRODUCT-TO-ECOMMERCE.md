---
schema_version: "1.0"
id: FLOW-PRODUCT-TO-ECOMMERCE
type: IntegrationFlow
status: active
name: Product to E-Commerce Flow
domain: DOMAIN-PRODUCT
source_system: SYSTEM-ERP
target_system: SYSTEM-ECOMMERCE
interface: IFACE-PRODUCT-SYNC
flow_type: batch_file
---

# Product to E-Commerce Flow

Nightly batch flow that extracts product changes from ERP and loads them into the e-commerce platform.

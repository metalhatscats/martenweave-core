---
id: CTX-CUSTOMER-TAX-S4
type: EntityContext
status: active
schema_version: '1.0'
name: S/4HANA Customer Tax
domain: DOMAIN-SAP-BP-CUSTOMER-VENDOR
system: SYS-S4HANA
business_entity: ENTITY-CUSTOMER-TAX
sap_table: KNAS
context_category: customer_tax
grain: KUNNR + LAND1 + STCEG
---

# S/4HANA Customer Tax

Context for KNAS with grain KUNNR + LAND1 + STCEG.

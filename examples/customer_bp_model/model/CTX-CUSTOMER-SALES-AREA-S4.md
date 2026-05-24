---
id: CTX-CUSTOMER-SALES-AREA-S4
type: EntityContext
status: active
name: S/4HANA Customer Sales Area
system: SYS-S4HANA
business_entity: ENTITY-CUSTOMER-SALES-AREA
sap_table: KNVV
context_category: customer_sales_area
grain: KUNNR + VKORG + VTWEG + SPART
description: >
  S/4HANA context for Customer Sales Area. Grain is defined by customer number,
  sales organization, distribution channel, and division.
---

# S/4HANA Customer Sales Area Context

This context represents the S/4HANA implementation of the Customer Sales Area
entity, anchored on table KNVV with the standard SAP grain.

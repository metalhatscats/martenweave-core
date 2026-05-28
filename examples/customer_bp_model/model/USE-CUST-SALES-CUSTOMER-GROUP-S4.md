---
id: USE-CUST-SALES-CUSTOMER-GROUP-S4
type: AttributeUsage
status: active
schema_version: "1.0"
name: Customer Group in S/4 Customer Sales Area
domain: DOMAIN-CUSTOMER-BP
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
entity_context: CTX-CUSTOMER-SALES-AREA-S4
usage_type: primary
scope: sales_area
requiredness: conditional
description: >
  AttributeUsage placing the Customer Group Attribute into the
  S/4HANA Customer Sales Area context. Requiredness may be conditional
  on sales area configuration.
display_name: Customer Group in S/4 Customer Sales Area
---

# Customer Group Attribute Usage

Links the Customer Group business attribute to the S/4HANA Customer Sales Area
context. In this context the attribute maps to the KNVV-KDGRP field endpoint.

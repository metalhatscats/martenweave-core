---
id: FEP-S4-KNVV-KDGRP
type: FieldEndpoint
status: active
schema_version: "1.0"
name: KNVV Customer Group
domain: DOMAIN-CUSTOMER-BP
system: SYS-S4HANA
endpoint_type: sap_table_field
sap_table: KNVV
sap_field: KDGRP
technical_name: KNVV-KDGRP
entity_context: CTX-CUSTOMER-SALES-AREA-S4
business_attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
description: >
  S/4HANA target field for Customer Group in the Customer Sales Area context (KNVV).
  This is a physical field endpoint, not a business attribute.
---

# KNVV-KDGRP Field Endpoint

Physical representation of the Customer Group field on SAP table KNVV.
This field lives in the Customer Sales Area context, not BP Central.

---
id: DQ-SALES-NET-VALUE-COMPLETENESS
type: DataQualityCheck
status: active
schema_version: '1.0'
name: Sales Net Value Completeness
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-SALES
attribute: ATTR-SALES-NET-VALUE
check_type: completeness
description: 'Checks that the agreed net_value column is present and populated in the CRM sales order
  extract. Currently failing: the file ships order_total instead (see ISS-SALES-ORDERS-MISSING-NET-VALUE).'
---

# Sales Net Value Completeness

Checks that the agreed net_value column is present and populated in the CRM sales order extract. Currently failing: the file ships order_total instead (see ISS-SALES-ORDERS-MISSING-NET-VALUE).

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

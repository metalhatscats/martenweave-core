---
id: ISS-SALES-ORDERS-MISSING-NET-VALUE
type: Issue
status: open
schema_version: '1.0'
name: Sales order extract misses mapped net_value column
created_at: '2026-02-02T09:00:00+00:00'
title: Sales order extract misses mapped net_value column
domain: DOMAIN-SALES
priority: high
issue_type: mapping
attribute: ATTR-SALES-NET-VALUE
related_objects:
- FEP-CRM-ORDER-NET-VALUE
- MAP-CRM-ORDER-NET-VALUE-TO-VBAK-NETWR
- DS-CRM-SALES-ORDERS
business_owner: PERSON-GOVERNANCE-REVIEWER
description: The delivered northstar_crm_sales_orders.csv does not contain the agreed, model-mapped net_value
  column; it ships order_total instead. MAP-CRM-ORDER-NET-VALUE-TO-VBAK-NETWR cannot run until the extract
  is corrected or the mapping is re-pointed.
---

# Sales order extract misses mapped net_value column

The delivered northstar_crm_sales_orders.csv does not contain the agreed, model-mapped net_value column; it ships order_total instead. MAP-CRM-ORDER-NET-VALUE-TO-VBAK-NETWR cannot run until the extract is corrected or the mapping is re-pointed.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

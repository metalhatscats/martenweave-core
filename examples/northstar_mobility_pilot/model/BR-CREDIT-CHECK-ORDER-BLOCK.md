---
id: BR-CREDIT-CHECK-ORDER-BLOCK
type: BusinessRule
status: active
schema_version: '1.0'
name: Credit Check Blocks Over-Limit Orders
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-SALES
attribute: ATTR-SHARED-CUSTOMER-CREDIT-LIMIT
rule_type: process
description: Sales orders that would push open receivables beyond the customer credit limit are blocked
  for review. This ties the shared credit attribute to the Sales and Finance contexts.
---

# Credit Check Blocks Over-Limit Orders

Sales orders that would push open receivables beyond the customer credit limit are blocked for review. This ties the shared credit attribute to the Sales and Finance contexts.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

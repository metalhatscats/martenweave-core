---
id: BR-PAYMENT-TERMS-INHERITANCE
type: BusinessRule
status: active
schema_version: '1.0'
name: Payment Terms Inheritance
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-SUPPLIER
attribute: ATTR-SHARED-PAYMENT-TERMS
rule_type: inheritance
description: Purchase orders and FI open items inherit payment terms from the supplier company code unless
  a document-level exception is approved. This is the business rule that makes ATTR-SHARED-PAYMENT-TERMS
  cross-domain.
---

# Payment Terms Inheritance

Purchase orders and FI open items inherit payment terms from the supplier company code unless a document-level exception is approved. This is the business rule that makes ATTR-SHARED-PAYMENT-TERMS cross-domain.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

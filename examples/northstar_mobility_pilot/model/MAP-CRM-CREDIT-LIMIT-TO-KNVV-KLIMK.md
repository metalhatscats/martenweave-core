---
id: MAP-CRM-CREDIT-LIMIT-TO-KNVV-KLIMK
type: Mapping
status: draft
schema_version: '1.0'
name: CRM Credit Limit to KNVV-KLIMK
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-BP-CUSTOMER
source_endpoint: FEP-CRM-CREDIT-LIMIT
target_endpoint: FEP-S4-KNVV-KLIMK
business_owner: PERSON-CUSTOMER-STEWARD
technical_owner: PERSON-INTEGRATION-DEVELOPER
transformation_notes: Direct copy; CRM values are treated as authoritative without conversion. Currency
  assumed EUR.
description: 'CONFLICT: maps CRM credit limits directly (CRM is claimed to be the credit master). Conflicts
  with MAP-VOYAGER-CREDIT-LIMIT-TO-KNVV-KLIMK; tracked in ISS-CREDIT-LIMIT-MAPPING-CONFLICT.'
---

# CRM Credit Limit to KNVV-KLIMK

CONFLICT: maps CRM credit limits directly (CRM is claimed to be the credit master). Conflicts with MAP-VOYAGER-CREDIT-LIMIT-TO-KNVV-KLIMK; tracked in ISS-CREDIT-LIMIT-MAPPING-CONFLICT.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

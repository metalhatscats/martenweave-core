---
id: MAP-VOYAGER-CREDIT-LIMIT-TO-KNVV-KLIMK
type: Mapping
status: draft
schema_version: '1.0'
name: Voyager Credit Limit to KNVV-KLIMK
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-BP-CUSTOMER
source_endpoint: FEP-VOYAGER-CREDIT-LIMIT
target_endpoint: FEP-S4-KNVV-KLIMK
business_owner: PERSON-SUPPLIER-STEWARD
technical_owner: PERSON-INTEGRATION-DEVELOPER
transformation_notes: Convert Voyager credit buckets (LOW/MED/HIGH) to amounts before load; rounding to
  nearest 500. Conflicts with the CRM direct copy.
description: 'CONFLICT: maps Voyager ERP credit limits into the same target field with a different transformation.
  Tracked in ISS-CREDIT-LIMIT-MAPPING-CONFLICT.'
---

# Voyager Credit Limit to KNVV-KLIMK

CONFLICT: maps Voyager ERP credit limits into the same target field with a different transformation. Tracked in ISS-CREDIT-LIMIT-MAPPING-CONFLICT.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

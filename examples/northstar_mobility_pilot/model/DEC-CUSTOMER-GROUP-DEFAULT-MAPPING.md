---
id: DEC-CUSTOMER-GROUP-DEFAULT-MAPPING
type: Decision
status: active
schema_version: '1.0'
name: Unmapped CRM groups default to 02
created_at: '2026-02-02T09:00:00+00:00'
title: Unmapped CRM groups default to 02
domain: DOMAIN-BP-CUSTOMER
attribute: ATTR-CUSTOMER-GROUP
evidence: EVI-CUSTOMER-GROUP-LEGACY-NOTES
decision_category: data_model
business_owner: PERSON-GOVERNANCE-REVIEWER
approver: PERSON-GOVERNANCE-REVIEWER
description: Any legacy customer group without an explicit entry in VMAP-CUSTOMER-GROUP-LEGACY-TO-S4 defaults
  to 02 (Retail & Rental) and is flagged for manual steward review after the pilot load.
---

# Unmapped CRM groups default to 02

Any legacy customer group without an explicit entry in VMAP-CUSTOMER-GROUP-LEGACY-TO-S4 defaults to 02 (Retail & Rental) and is flagged for manual steward review after the pilot load.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

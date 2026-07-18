---
id: ISS-CREDIT-LIMIT-MAPPING-CONFLICT
type: Issue
status: open
schema_version: '1.0'
name: Credit limit mapping conflict (CRM vs Voyager)
created_at: '2026-02-02T09:00:00+00:00'
title: Credit limit mapping conflict (CRM vs Voyager)
domain: DOMAIN-BP-CUSTOMER
priority: high
issue_type: mapping
attribute: ATTR-SHARED-CUSTOMER-CREDIT-LIMIT
related_objects:
- MAP-CRM-CREDIT-LIMIT-TO-KNVV-KLIMK
- MAP-VOYAGER-CREDIT-LIMIT-TO-KNVV-KLIMK
- FEP-S4-KNVV-KLIMK
business_owner: PERSON-GOVERNANCE-REVIEWER
description: 'Two mappings from different legacy sources (Northstar CRM and Voyager ERP) target the same
  S/4 field KNVV-KLIMK with different transformation notes: CRM demands a direct authoritative copy, Voyager
  demands bucket conversion with rounding. Only one can survive cutover; see DEC-CREDIT-LIMIT-SOURCE-PRECEDENCE
  for the proposed resolution.'
---

# Credit limit mapping conflict (CRM vs Voyager)

Two mappings from different legacy sources (Northstar CRM and Voyager ERP) target the same S/4 field KNVV-KLIMK with different transformation notes: CRM demands a direct authoritative copy, Voyager demands bucket conversion with rounding. Only one can survive cutover; see DEC-CREDIT-LIMIT-SOURCE-PRECEDENCE for the proposed resolution.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

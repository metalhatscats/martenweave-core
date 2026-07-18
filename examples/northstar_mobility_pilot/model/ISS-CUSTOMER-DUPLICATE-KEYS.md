---
id: ISS-CUSTOMER-DUPLICATE-KEYS
type: Issue
status: open
schema_version: '1.0'
name: CRM customer extract contains duplicate business keys
created_at: '2026-02-02T09:00:00+00:00'
title: CRM customer extract contains duplicate business keys
domain: DOMAIN-BP-CUSTOMER
priority: medium
issue_type: data_quality
attribute: ATTR-CUSTOMER-ID
related_objects:
- DS-CRM-CUSTOMERS
- DQ-CUSTOMER-DUPLICATE-BUSINESS-KEYS
business_owner: PERSON-GOVERNANCE-REVIEWER
description: northstar_crm_customers.csv contains duplicated customer_id values (C-10007, C-10015) with
  slightly different spellings of the legal name. The duplicates must be merged by the customer data steward
  before load.
---

# CRM customer extract contains duplicate business keys

northstar_crm_customers.csv contains duplicated customer_id values (C-10007, C-10015) with slightly different spellings of the legal name. The duplicates must be merged by the customer data steward before load.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

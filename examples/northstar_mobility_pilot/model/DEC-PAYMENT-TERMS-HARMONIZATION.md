---
id: DEC-PAYMENT-TERMS-HARMONIZATION
type: Decision
status: active
schema_version: '1.0'
name: Harmonize payment terms on NT codes
created_at: '2026-02-02T09:00:00+00:00'
title: Harmonize payment terms on NT codes
domain: DOMAIN-SUPPLIER
attribute: ATTR-SHARED-PAYMENT-TERMS
evidence: EVI-PAYMENT-TERMS-ANALYSIS
decision_category: data_model
business_owner: PERSON-GOVERNANCE-REVIEWER
approver: PERSON-GOVERNANCE-REVIEWER
description: All legacy payment-terms codes are harmonized onto the four NT codes in VLIST-S4-PAYMENT-TERMS.
  The supplier master is the single source; purchase orders and FI items inherit via the shared value
  mapping. Changing the shared attribute therefore requires a three-domain impact review.
---

# Harmonize payment terms on NT codes

All legacy payment-terms codes are harmonized onto the four NT codes in VLIST-S4-PAYMENT-TERMS. The supplier master is the single source; purchase orders and FI items inherit via the shared value mapping. Changing the shared attribute therefore requires a three-domain impact review.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

---
id: DEC-ARCH-001-BP-CENTRAL
type: Decision
status: active
schema_version: "1.0"
title: Business Partner Central as canonical master entity
domain: DOMAIN-CUSTOMER-BP
evidence: EVI-CH01-A17-ANALYSIS
decision_category: architecture
description: >
  Business Partner (BUT000) is the canonical central master data entity
  for customer migration. All customer-specific attributes are modeled
  as extensions via Customer and Customer Sales Area entities.
---

# Business Partner Central as Canonical Master Entity

Business Partner (BUT000) is the canonical central master data entity
for customer migration. Customer-specific attributes are modeled as
extensions via Customer and Customer Sales Area entities.

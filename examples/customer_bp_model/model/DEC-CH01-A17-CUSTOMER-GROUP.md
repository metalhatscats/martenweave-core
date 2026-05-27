---
id: DEC-CH01-A17-CUSTOMER-GROUP
type: Decision
status: active
business_owner: PERSON-BUSINESS-OWNER
data_steward: PERSON-DATA-STEWARD
schema_version: "1.0"
title: Customer Group CH01 / A17 handling decision
domain: DOMAIN-CUSTOMER-BP
related_issue: ISS-CH01-A17-CONFIG-GAP
evidence: EVI-CH01-A17-ANALYSIS
decision_category: data_model
description: >
  Decision on how to handle CH01 / A17 Customer Group values
  during migration. Map unmapped values to default group "00"
  and flag for manual remediation.
---

# Customer Group CH01 / A17 Handling Decision

This decision records the rationale for how CH01 / A17 Customer Group
values will be treated during migration. Based on the gap analysis evidence,
unmapped values will be mapped to default group "00" and flagged for manual
remediation.

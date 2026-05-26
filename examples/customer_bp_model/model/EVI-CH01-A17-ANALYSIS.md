---
id: EVI-CH01-A17-ANALYSIS
type: Evidence
status: active
schema_version: "1.0"
title: CH01 / A17 Customer Group Gap Analysis Evidence
domain: DOMAIN-CUSTOMER-BP
---

# CH01 / A17 Customer Group Gap Analysis Evidence

This evidence object captures the findings from the configuration gap analysis for CH01 / A17 Customer Group values during migration.

## Findings

- 12% of legacy Customer Group values (CH01, A17) have no direct mapping in the target S/4HANA value list.
- Recommended approach: map to default group "00" and flag for manual review.

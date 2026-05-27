---
id: DEC-ARCH-001-VENDOR-CENTRAL
type: Decision
status: active
schema_version: "1.0"
title: LFA1 as canonical central vendor master entity
domain: DOMAIN-SUPPLIER-VENDOR
evidence: EVI-ARCH-001-VENDOR-CENTRAL-ANALYSIS
decision_category: architecture
data_steward: PERSON-DATA-STEWARD-VENDOR
description: >
  LFA1 (Vendor General Data) is the canonical central master data entity
  for supplier migration. Company-code-dependent attributes are modeled
  via LFB1, and purchasing-organization-dependent attributes via LFM1.
---

# LFA1 as Canonical Central Vendor Master Entity

LFA1 is the canonical central master data entity for supplier/vendor migration.
Company-code-specific attributes are modeled as extensions via LFB1,
and purchasing-organization-specific attributes via LFM1.

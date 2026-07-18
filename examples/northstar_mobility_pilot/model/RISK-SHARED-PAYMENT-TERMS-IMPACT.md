---
id: RISK-SHARED-PAYMENT-TERMS-IMPACT
type: Risk
status: active
schema_version: '1.0'
name: Shared payment terms change has three-domain blast radius
created_at: '2026-02-02T09:00:00+00:00'
domain: DOMAIN-SUPPLIER
attribute: ATTR-SHARED-PAYMENT-TERMS
severity: high
likelihood: medium
description: 'Because ATTR-SHARED-PAYMENT-TERMS is reused by Supplier (LFB1-ZTERM), Procurement (EKKO-ZTERM),
  and Finance (BSEG-ZTERM), an uncoordinated change to the attribute or its value list silently impacts
  all three domains. Mitigation: route changes through the harmonization decision and the governance reviewer.'
---

# Shared payment terms impact risk

Because ATTR-SHARED-PAYMENT-TERMS is reused by Supplier (LFB1-ZTERM), Procurement (EKKO-ZTERM), and Finance (BSEG-ZTERM), an uncoordinated change to the attribute or its value list silently impacts all three domains. Mitigation: route changes through the harmonization decision and the governance reviewer.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.

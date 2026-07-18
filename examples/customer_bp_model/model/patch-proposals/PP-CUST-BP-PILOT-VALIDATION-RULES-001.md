---
id: PP-CUST-BP-PILOT-VALIDATION-RULES-001
type: PatchProposal
status: accepted
name: Customer BP pilot validation coverage
title: Add pilot-critical Customer BP validation rules
created_by: ai
created_at: 2026-07-18 09:20:00+00:00
source_evidence: The deterministic pilot readiness gate reports 31.2% validation-rule
  coverage for the Customer BP reference model, below the 40% pilot threshold. Adding
  two rules for the high-risk tax number and foundation date attributes raises the
  model to 43.8% without claiming that every attribute is fully governed.
source_state: proposal
affected_objects:
- ATTR-BP-CUSTOMER-TAX-NUMBER
- ATTR-BP-CENTRAL-FOUNDATION-DATE
validation_status: pending
validation_results: []
operations:
- op: create_object
  object_id: VAL-BP-CUSTOMER-TAX-NUMBER-FORMAT
  object_type: ValidationRule
  reason: Add an explicit reviewable rule for a customer tax identifier before migration.
  after:
    id: VAL-BP-CUSTOMER-TAX-NUMBER-FORMAT
    type: ValidationRule
    status: active
    name: Customer Tax Number Format
    domain: DOMAIN-CUSTOMER-BP
    attribute: ATTR-BP-CUSTOMER-TAX-NUMBER
    rule_type: format
    business_owner: PERSON-BUSINESS-OWNER
    data_steward: PERSON-DATA-STEWARD
    schema_version: '1.0'
    description: Customer tax numbers must satisfy the country-specific format agreed
      for the migration scope before they are loaded into the target system.
- op: create_object
  object_id: VAL-BP-CENTRAL-FOUNDATION-DATE-VALID
  object_type: ValidationRule
  reason: Add an explicit reviewable rule for a business partner foundation date before
    migration.
  after:
    id: VAL-BP-CENTRAL-FOUNDATION-DATE-VALID
    type: ValidationRule
    status: active
    name: Foundation Date Validity
    domain: DOMAIN-CUSTOMER-BP
    attribute: ATTR-BP-CENTRAL-FOUNDATION-DATE
    rule_type: date_validity
    business_owner: PERSON-BUSINESS-OWNER
    data_steward: PERSON-DATA-STEWARD
    schema_version: '1.0'
    description: Foundation dates must be valid dates and cannot be later than the
      migration cutover date agreed for the pilot.
updated_at: '2026-07-18T09:15:54.505971+00:00'
reviewer: product-owner
reviewed_at: '2026-07-18T09:16:11Z'
reviewer_notes: User-authorized pilot-reference improvement; reviewed deterministic
  validation, affected attributes, and country/cutover assumptions.
---

# Customer BP pilot validation coverage

This proposal intentionally closes the minimum evidence gap required for a pilot-ready
reference model. Country-specific formats and the cutover date remain review inputs; no
AI-generated rule is treated as an executable control without human review.

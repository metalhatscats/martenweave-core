---
id: PP-NORTHSTAR-NET-VALUE-VALIDATION-001
type: PatchProposal
status: pending_review
name: Sales net value outlier validation coverage
title: Add outlier validation rule for the blocked sales net value mapping
created_by: ai
created_at: '2026-02-09T09:00:00+00:00'
source_evidence: >-
  ISS-SALES-ORDERS-MISSING-NET-VALUE documents that the CRM sales order extract
  ships order_total instead of the mapped net_value column. While the extract is
  being corrected, an additional outlier-validation rule on the target attribute
  gives reviewers a deterministic tripwire for implausible values once the
  mapping is unblocked.
source_state: proposal
affected_objects:
- ATTR-SALES-NET-VALUE
- FEP-CRM-ORDER-NET-VALUE
- FEP-S4-VBAK-NETWR
validation_status: pending
validation_results: []
operations:
- op: create_object
  object_id: VAL-SALES-NET-VALUE-OUTLIER-CHECK
  object_type: ValidationRule
  reason: Add a reviewable outlier rule for sales order net values before the
    corrected extract is loaded.
  after:
    id: VAL-SALES-NET-VALUE-OUTLIER-CHECK
    type: ValidationRule
    status: draft
    name: Sales Net Value Outlier Check
    domain: DOMAIN-SALES
    attribute: ATTR-SALES-NET-VALUE
    rule_type: range
    business_owner: PERSON-OTC-PROCESS-OWNER
    approver: PERSON-GOVERNANCE-REVIEWER
    schema_version: '1.0'
    description: Net values above the pilot outlier threshold of 250000 must be
      flagged for manual review before they are loaded into VBAK-NETWR.
---

# Sales net value outlier validation coverage

This proposal was drafted by the AI assistant in response to
ISS-SALES-ORDERS-MISSING-NET-VALUE. It only adds a reviewable validation rule;
it does not change the blocked mapping and it requires human approval before
application. All data in this pilot is fictional.

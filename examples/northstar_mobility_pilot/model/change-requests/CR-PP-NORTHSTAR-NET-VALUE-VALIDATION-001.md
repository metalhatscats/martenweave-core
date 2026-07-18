---
id: CR-PP-NORTHSTAR-NET-VALUE-VALIDATION-001
type: ChangeRequest
status: approved
name: 'Change Request: PP-NORTHSTAR-NET-VALUE-VALIDATION-001'
title: 'Change Request: PP-NORTHSTAR-NET-VALUE-VALIDATION-001'
created_at: '2026-02-10T09:00:00+00:00'
requester: PERSON-GOVERNANCE-REVIEWER
affected_objects:
- ATTR-SALES-NET-VALUE
- FEP-CRM-ORDER-NET-VALUE
- FEP-S4-VBAK-NETWR
linked_proposals:
- PP-NORTHSTAR-NET-VALUE-VALIDATION-001
source_patch_proposals:
- PP-NORTHSTAR-NET-VALUE-VALIDATION-001
related_issues:
- ISS-SALES-ORDERS-MISSING-NET-VALUE
approvals:
- approver: PERSON-SOLUTION-ARCHITECT
  decision: approved
  approved_at: '2026-02-10T10:00:00+00:00'
- approver: PERSON-GOVERNANCE-REVIEWER
  decision: approved
  approved_at: '2026-02-10T11:30:00+00:00'
risk_level: high
risk_reasons:
- Affected object 'ATTR-SALES-NET-VALUE' is active
- Linked to 1 proposal(s)
risk_triggering_rules:
- active_object_modified
---

# Change Request: CR-PP-NORTHSTAR-NET-VALUE-VALIDATION-001

Governance approved the remediation plan for the missing net_value column: the
extract will be re-delivered and the outlier validation rule from
PP-NORTHSTAR-NET-VALUE-VALIDATION-001 will be applied afterwards. The proposal
itself remains pending_review until the integration developer confirms the
threshold with the fictional order-to-cash process owner.

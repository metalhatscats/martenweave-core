# Migration Model Readiness Assessment — Engagement Template

> Use this template to scope and deliver a repeatable Martenweave readiness assessment.

## Engagement Scope

| Item | Detail |
|---|---|
| **Objective** | Determine whether the current migration model is ready for build/convert phase. |
| **Duration** | 1–2 weeks (pilot) |
| **Deliverable** | Assessment package + business review + recommendations |
| **Stakeholders** | Data architect, functional lead, business owner, migration lead |
| **Tooling** | Martenweave CLI, Git, Markdown, Excel |

## Objectives

1. **Validate** the canonical model for ID correctness, reference integrity, and SAP context rules.
2. **Measure** readiness through deterministic scorecard metrics.
3. **Identify** gaps in ownership, validation rules, value mappings, and field coverage.
4. **Surface** high-risk fields that could block migration or cause rework.
5. **Document** impact of changes before they are made.
6. **Produce** a business-reviewable artifact (Excel + Markdown) for sign-off.

## Deliverables

| Deliverable | Format | Owner |
|---|---|---|
| Readiness Scorecard | Markdown | Consultant / Architect |
| Gap Report | Markdown | Consultant / Architect |
| High Risk Fields Register | Markdown | Consultant / Architect |
| Impact Reports | Markdown (per object) | Consultant / Architect |
| Business Review Workbook | Excel | Business Stakeholder |
| Recommendations | Markdown | Consultant / Architect |
| Evidence Package | Git commit + artifacts | Shared |

## Suggested Timeline

| Day | Activity |
|---|---|
| 1 | Kickoff, stakeholder interviews, tool setup |
| 2–3 | Model ingestion, validation, index build |
| 4–5 | Gap analysis, risk scoring, impact mapping |
| 6–8 | Business review, ownership assignment, decisions |
| 9–10 | Final recommendations, evidence packaging, closeout |

## How to Use Martenweave Outputs

- **Scorecard** → Share with leadership as a one-page health summary.
- **Gap Report** → Use as a backlog for the modeling team.
- **High Risk Fields** → Prioritize for data cleansing and mapping workshops.
- **Impact Reports** → Review before any model change to avoid surprises.
- **Business Review Workbook** → Let functional leads comment directly in Excel.
- **Recommendations** → Convert into Jira/Azure DevOps tasks.

## Pricing Hypothesis (internal)

- Fixed-price pilot: 1–2 weeks.
- Outcome: go/no-go decision on model readiness + actionable backlog.
- No ongoing SaaS fees; client owns the model repository.

## Success Criteria

- [ ] Model validates with zero ERROR-level findings, or all errors are accepted risks.
- [ ] Every high-risk field has an assigned owner and a remediation plan.
- [ ] Business stakeholders can explain the scorecard without help.
- [ ] Assessment output is committed to version control as audit evidence.

# Delivery Checklist — Migration Model Readiness Assessment

> Use this checklist to ensure every assessment is delivered consistently and completely.

## Pre-Engagement

- [ ] Martenweave CLI installed and working (`martenweave --version`)
- [ ] Example repository cloned or client repository accessible
- [ ] Stakeholder list confirmed (business owner, technical owner, migration lead)
- [ ] Interview questions printed or shared in advance
- [ ] Output directory prepared (local folder or shared drive)

## Model Setup

- [ ] Repository structure follows Martenweave conventions (`model/`, `generated/`, `data/`)
- [ ] `modelops.config.yaml` present and valid
- [ ] Canonical objects use correct ID format (`^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`)
- [ ] Sample datasets are synthetic and privacy-safe
- [ ] Git repository initialized (if not already)

## Validation & Index

- [ ] `martenweave validate --repo <repo>` runs without unhandled exceptions
- [ ] All ERROR-level findings are documented as accepted risks or scheduled for fix
- [ ] `martenweave build-index --repo <repo>` succeeds
- [ ] Index is fresh (rebuilt after the latest model changes)

## Assessment Generation

- [ ] `martenweave assessment run --repo <repo> --out <dir>` completes successfully
- [ ] `01_readiness_scorecard.md` contains readiness level and metrics
- [ ] `02_gap_report.md` contains gap score and gaps by type
- [ ] `03_high_risk_fields.md` contains at least a severity legend
- [ ] `04_impact_reports/` contains impact reports for top risk objects
- [ ] `05_business_review.xlsx` opens correctly in Excel or LibreOffice
- [ ] `06_recommendations.md` contains next steps

## Business Review

- [ ] Business review workbook shared with functional leads
- [ ] Reviewer notes are collected (in Excel or as follow-up issues)
- [ ] Open decisions are recorded as Martenweave `Decision` objects
- [ ] Ownership gaps are assigned to named individuals

## Stakeholder Sign-Off

- [ ] Scorecard reviewed with executive sponsor
- [ ] High risk fields triaged and prioritized
- [ ] Recommendations accepted or amended
- [ ] Go / no-go decision documented

## Evidence Packaging

- [ ] Assessment output committed to Git or archived with version label
- [ ] Git commit hash recorded in the delivery summary
- [ ] All artifacts are deterministic (same input produces same output)
- [ ] No real client data is present in the output folder

## Closeout

- [ ] Final report written (1–2 pages summarizing findings and next steps)
- [ ] Follow-up issues created in the client's issue tracker
- [ ] Re-assessment date scheduled (suggest 2–4 weeks)
- [ ] Lessons learned noted for the next engagement

## Optional Enhancements

- [ ] `martenweave export-model --format xlsx --business-review` used for additional review rounds
- [ ] `martenweave health` and `martenweave scorecard` run separately for ad-hoc checks
- [ ] Impact analysis run for any object the team plans to change
- [ ] Pilot kit templates customized for the client's industry or use case

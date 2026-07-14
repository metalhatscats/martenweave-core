# Design-Partner Pilot Runbook

> A repeatable 1–2 week pilot process for SAP migration teams using Martenweave.
> Companion to `docs/product/ROADMAP_PILOT.md`.
> Version: 0.4.1

---

## Goal

Run a controlled pilot that proves whether Martenweave can turn a real SAP
mapping workbook into a trustworthy, reviewable readiness pack.

The pilot is successful only if the migration team confirms at least one
high-value finding that they would not have caught as quickly by hand.

---

## Required Inputs

Before starting, collect:

| Input | Format | Purpose |
|---|---|---|
| Mapping workbook | `.xlsx` | Source-to-target field mappings, owners, status, decisions. |
| Sample dataset | `.csv` or `.xlsx` | A small, safe extract used for readiness checking. |
| Evidence notes | `.md` or `.txt` | Workshop decisions, open questions, validation report snippets. |
| Validation report (optional) | `.csv` or `.xlsx` | Report of known data-quality issues. |
| Baseline estimates | Plain text | Prior trace time, review effort, onboarding time. |

All inputs must be:
- **Synthetic or anonymized.** No real customer names, account numbers, email
  addresses, or project identifiers.
- **Approved for processing.** The client has agreed that these files may be
  loaded into a local tool on the consultant's machine.
- **Stored inside the pilot working directory only.** Do not commit raw inputs
  to the Martenweave repository or any shared drive without sanitization.

---

## Privacy and Sanitization Pre-Flight

Before running the assessment, complete this checklist:

- [ ] All raw datasets are limited to ≤1,000 rows unless the client explicitly
      approved more.
- [ ] No columns contain names, emails, phone numbers, account numbers, or
      free-text comments that could identify individuals.
- [ ] File names and paths do not reveal client name, project code, or environment.
- [ ] Validation reports and evidence notes have been reviewed for embedded
      credentials, tokens, or internal URLs.
- [ ] A plan exists for producing a sanitized external pack before any artifact
      is shared.

Run the built-in preflight before processing any raw inputs:

```bash
martenweave pilot-preflight \
  --mapping ./inputs/mapping.xlsx \
  --dataset ./inputs/sample.csv \
  --evidence ./inputs/decisions.md \
  --validation-report ./inputs/validation.xlsx \
  --out ./outputs/preflight
```

The preflight produces `outputs/preflight/preflight_report.json` and
`outputs/preflight/preflight_report.md`. It inspects file metadata, sheet and
column names, formulas, hidden sheets, external workbook links, secret-like
patterns, and sensitive column-name indicators. Raw row values are excluded by
default; add `--include-raw-samples` only when you explicitly need sample data
in the report.

If the preflight reports a `blocked` status, resolve the issue before running the
assessment. If it reports `warning`, review each warning and document why the
input is still safe to process.

---

## Setup Steps

1. **Install Martenweave Core**

   ```bash
   python -m venv .venv
   .venv/bin/python -m pip install -e ".[dev]"
   .venv/bin/martenweave --help
   ```

2. **Create or choose a model repository**

   Use the bundled example for the first pilot:

   ```bash
   cp -r examples/customer_bp_model ./pilot-repo
   ```

   Or initialize a fresh repository:

   ```bash
   .venv/bin/martenweave init ./pilot-repo
   ```

3. **Validate the repository**

   ```bash
   .venv/bin/martenweave validate --repo ./pilot-repo
   ```

4. **Run the migration assessment**

   ```bash
   .venv/bin/martenweave run migration-assessment \
     --repo ./pilot-repo \
     --mapping ./inputs/mapping.xlsx \
     --dataset ./inputs/sample.csv \
     --evidence ./inputs/decisions.md \
     --out ./outputs/assessment
   ```

5. **Inspect the output**

   Open:
   - `outputs/assessment/manifest.json` — inputs, stage statuses, artifact checksums.
   - `outputs/assessment/01_readiness_scorecard.md` — overall readiness.
   - `outputs/assessment/02_gap_report.md` — consolidated gaps.
   - `outputs/assessment/03_high_risk_fields.md` — ranked risk items.
   - `outputs/assessment/04_impact_reports/` — impact reports for top risks.
   - `outputs/assessment/05_business_review.xlsx` — reviewable workbook.
   - `outputs/assessment/06_recommendations.md` — next steps.
   - `outputs/assessment/review_pack/` — stakeholder-facing pack.
   - `outputs/assessment/mapping_profile.json` — workbook metadata and row-level
     findings such as missing owners, missing mappings, obsolete fields,
     duplicate target representations, validation coverage gaps, unresolved
     decisions, and conflicting decisions.

---

## Synthetic Pilot Fixture

A fully synthetic, byte-stable SAP Customer / Vendor mapping workbook is shipped
as a repeatable pilot fixture:

- `tests/fixtures/pilot/sap_customer_mapping.xlsx`
- Regenerator: `tests/fixtures/pilot/generate_sap_customer_mapping.py`

The workbook deliberately injects common migration-quality findings so the
assessment output can be validated against known counts:

- Missing owners
- Missing target table/field mappings
- Obsolete source fields
- Duplicate target representations
- Conditional mandatory rules without validation coverage
- Unresolved decisions
- Conflicting decisions on the same topic

Run the fixture through the full assessment:

```bash
.venv/bin/martenweave run migration-assessment \
  --repo examples/customer_bp_model \
  --mapping tests/fixtures/pilot/sap_customer_mapping.xlsx \
  --out /tmp/martenweave-golden-assessment
```

The golden test in `tests/test_pilot_mapping_workbook.py` asserts the expected
count for each finding class and confirms that the assessment stages complete
successfully.

---

## Stakeholder Review Workflow

1. **Triage findings**
   - Open `03_high_risk_fields.md` and the impact reports.
   - Assign each finding to the relevant owner.

2. **Record dispositions**
   - Use `martenweave assessment-review` when available, or a local
     `finding-reviews.json` file with this shape:

     ```json
     {
       "finding_id": "gap:missing_owner:ATTR-CUST-SALES-CUSTOMER-GROUP",
       "disposition": "confirmed",
       "reviewer": "Jane Consultant",
       "note": "Confirmed against mapping workbook v3.",
       "reviewed_at": "2026-07-14T10:00:00Z"
     }
     ```

   - Allowed dispositions: `confirmed`, `false_positive`, `accepted_risk`,
     `deferred`, `resolved`.

3. **Promote confirmed findings**
   - Convert confirmed gaps into issue drafts or PatchProposals through the
     existing `issue-draft` and `proposal` commands.
   - Do not edit canonical model files directly.

4. **Sanitize before sharing**
   - Use `martenweave assessment sanitize` when available, or manually remove
     raw datasets, absolute paths, and client identifiers.

---

## Closeout Template

Complete this template at the end of the pilot.

### Pilot Identification

| Field | Value |
|---|---|
| Pilot name | |
| Domain / migration object | |
| Start date | |
| End date | |
| Lead consultant | |
| Client stakeholders | |

### Inputs Used

| Input | File | Rows / sheets | Approved? |
|---|---|---|---|
| Mapping workbook | | | |
| Sample dataset | | | |
| Evidence notes | | | |
| Validation report | | | |

### Baseline Metrics (manual, do not invent)

| Metric | Prior value | Source |
|---|---|---|
| Time to trace one changed field to all impacts | | |
| Time to prepare a readiness review pack | | |
| Onboarding time for a new migration analyst | | |

### Measured Metrics

| Metric | Value | Source artifact |
|---|---|---|
| Assessment runs | | `manifest.json` |
| Total findings | | `02_gap_report.md` |
| Confirmed findings | | `finding-reviews.json` |
| False positives | | `finding-reviews.json` |
| Accepted risks | | `finding-reviews.json` |
| Time to first usable report | | Pilot notes |
| Repeat assessment runs | | `manifest.json` |

### Reviewer Feedback

- What was the most useful finding?
- What was unclear or noisy?
- Would the team use this again?
- What would need to change before adoption?

### Recommendation

Choose one:

- [ ] **Continue** — pilot produced ≥3 confirmed useful findings and team wants
      to use Martenweave on the next migration object.
- [ ] **Pivot** — some value was shown, but the workflow or scope needs to change.
      Describe the pivot:
- [ ] **Stop** — no confirmed useful findings or the team cannot integrate the
      tool into their process. Describe the blockers:

### Next Steps

1.
2.
3.

---

## Go / Pivot / Stop Criteria

| Decision | Threshold |
|---|---|
| **Go** | ≥3 confirmed useful findings, <30% false-positive rate, and ≥1 stakeholder willing to repeat the workflow. |
| **Pivot** | 1–2 confirmed findings, or >30% false-positive rate, or tooling friction that can be fixed in one iteration. |
| **Stop** | 0 confirmed findings, or the pilot cannot be completed due to missing data/process blockers. |

---

## Sanitized Case-Study Outline

Use this outline only when the client has explicitly approved public sharing.
Do not invent quotes, benchmarks, or cost savings.

1. **Context** — industry, migration object, team size.
2. **Inputs** — generic description (e.g., "SAP Customer master mapping workbook").
3. **Process** — how the assessment was run.
4. **Confirmed findings** — anonymized examples.
5. **Outcome** — continue / pivot / stop recommendation.
6. **Limitations** — what the pilot did not prove.

Never include:
- Client name or project code.
- Real field values or customer data.
- Unverified productivity claims.

---

## Related Documents

- `docs/product/ROADMAP_PILOT.md` — active product roadmap.
- `docs/product/ACCEPTANCE_CRITERIA.md` — MVP acceptance criteria.
- `docs/demo-quickstart-flow.md` — release-grade demo path.

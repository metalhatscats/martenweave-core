# Pilot-First Product Roadmap

> **Active roadmap for martenweave-core.**
> Replaces the feature-led `ROADMAP_V0_1.md` with a workflow-first plan built
> around one repeatable SAP migration pilot.
> Version: 0.4.1

---

## Primary ICP and Workflow

**Primary ideal customer profile (ICP):**
SAP migration data analyst or consultant who needs to turn a messy mapping
workbook and project evidence into a validated, reviewable readiness pack in
1–2 weeks.

**Primary end-to-end workflow (the pilot):**

```text
mapping workbook + evidence
        ↓
pilot-preflight + privacy check
        ↓
validated Martenweave model repository
        ↓
run migration-assessment
        ↓
readiness verdict + gap summary + risk report + impact reports
        ↓
business review workbook + review pack
        ↓
human disposition of findings
        ↓
pilot-outcome report (continue / pivot / stop)
```

Everything outside this loop is explicitly sequenced after the first pilot
unless it unblocks the loop.

---

## Product Principles and Stop Rules

1. **Canonical files are the source of truth.** Assessment outputs and Excel
   workbooks are disposable review interfaces, not the model of record.
2. **AI and imports propose; humans approve.** No automatic mutation of
   canonical files.
3. **Local-first.** No hosted SaaS platform, tenant layer, authentication,
   generic chatbot, workflow engine, or direct SAP write-back in the core.
4. **Trust before expansion.** Do not add new integrations, generic object
   types, large UI expansions, or enterprise features before the first pilot
   produces confirmed useful findings.
5. **Pilot evidence gates:**
   - A feature ships only if it improves the primary workflow or removes a
     blocker to it.
   - A new object type or integration needs a pilot use case that cannot be
     satisfied by existing objects.
   - A UI or API surface must be justified by a repeatable pilot step.

---

## Phases

### Now — First Pilot Loop

Goal: a single consultant can run the primary workflow from a mapping workbook
to a reviewable pack without writing code.

| Issue | Deliverable | Why in Now |
|---|---|---|
| #485 | This roadmap | Aligns all near-term work on one workflow. |
| #486 | `martenweave run migration-assessment` | One command for the end-to-end assessment. |
| #488 | `docs/pilots/design-partner-runbook.md` | Repeatable 1–2 week pilot process. |
| #487 | Realistic SAP mapping workbook fixture + golden test | Proves the workflow against a messy, credible workbook. |
| #494 | `martenweave pilot-preflight` | Privacy and safety check before processing client files. |

**Exit criteria for Now:**
- `run migration-assessment` succeeds on the golden workbook fixture.
- A first-time user can follow the runbook and produce a review pack.
- At least one design partner confirms one high-value finding from the pack.

### After First Pilot — Close the Loop

Goal: measure whether the pack is actually useful and turn confirmed findings
into trackable proposals/issues.

| Issue | Deliverable | Why after pilot |
|---|---|---|
| #490 | `martenweave assessment-review` disposition workflow | Measures usefulness (confirmation / false-positive rate). |
| #493 | `martenweave pilot-outcome` report | Evidence-based continue / pivot / stop decision. |
| #491 | `martenweave assessment sanitize` | Safe external sharing of sanitized packs. |
| #489 | `martenweave bootstrap-assessment` | Start a new pilot from only a workbook. |
| #495 | Deterministic public demo bundle | Reusable proof asset for website/releases. |
| #430 | Evidence ingestion into PatchProposals | Turn notes/reports into reviewable proposals. |
| #427 | Business-review Excel round-trip via PatchProposal | Business stakeholders edit and return proposals. |
| #434 | Scenario templates for `martenweave init` | Faster onboarding for SAP and AMS use cases. |

**Exit criteria for After First Pilot:**
- Confirmation rate and false-positive rate are measured for ≥1 pilot.
- A sanitized demo bundle can be generated deterministically from fixtures.
- At least one pilot produces a clear continue/pivot/stop outcome.

### Later — Scale and Collaboration

Goal: make Martenweave useful for teams and broader domains once the single-user
pilot is proven.

| Issue / Idea | Deliverable | Gate |
|---|---|---|
| #416 | Split `cli.py` monolith into `commands/` package | Blocks product delivery or agent velocity. |
| #428 | Realistic SAP BP / Customer / Vendor reference model | Needed for commercial demos, after pilot trust. |
| #492 | Wire frontend Models search/object detail to live local API | Stable API contract and repeatable pilot first. |
| — | Optional GitHub/GitLab PR workflow | Pilot users ask for shared review. |
| — | Optional Postgres team workspace | Multiple paid pilots need shared state. |
| — | Additional domain packs (vendor, material, finance) | Customer demand in ≥2 pilots. |

**Entry criteria:**
- Primary workflow is repeatable with ≥2 successful pilots.
- No P0 trust bugs remain in the dataset-to-model gap path.
- Clear customer demand justifies the expansion.

---

## Metrics

| Metric | Definition | Target |
|---|---|---|
| Workbook runs | Number of `run migration-assessment` executions on real workbooks | ≥5 in first quarter |
| Confirmed useful findings | Findings reviewers mark `confirmed` / `accepted_risk` | ≥3 per pilot |
| False-positive rate | `false_positive` dispositions / total dispositions | <30% |
| Repeat usage | Pilots that run the assessment ≥2 times | ≥50% |
| Pilot conversion | Pilots that recommend `continue` | ≥1 to start |
| Time to review pack | From clean repo + workbook to first readable pack | <30 minutes |

---

## Trust Blockers Addressed

The `ROADMAP_RECOMMENDATIONS.md` audit identified three P0 trust blockers
(#482 `gaps --check-model` false-positive, #483 scorecard metric logic,
#484 dataset profile/index sync). These must be resolved before the first
pilot is considered successful. They are tracked as closed engineering issues
and should be regression-tested in every release.

---

## Historical Roadmaps

- `ROADMAP_V0_1.md` — historical v0.1 feature list; see this document for
  active sequencing.
- `ROADMAP_RECOMMENDATIONS.md` — product explorer audit that informed this
  roadmap.

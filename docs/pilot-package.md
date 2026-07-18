# Pilot Package and Proof-of-Value Workflow

> A concrete 1–2 week pilot that lets a team prove Martenweave value on one real model or migration object.

---

## Pilot Premise

Validate Martenweave with minimal commitment:
- **One team**, **one migration object** (or one master data domain)
- **1–2 weeks**, **1–2 half-days** of team time
- **No code changes** to existing systems
- **Local-first**: runs on a laptop, no cloud contract needed

---

## What the Prospect Provides

| Item | Format | Why Needed |
|---|---|---|
| Migration object or domain scope | Text description | Defines pilot boundaries |
| Source field list or sample extract | CSV, XLSX, or screenshot | Seed for model inference |
| Target field list (SAP or other) | CSV, XLSX, or table name | Seed for model inference |
| Existing mapping sheet (if any) | Excel | Baseline for gap analysis |
| Business owner name and email | Text | Ownership assignment |
| 1–2 sample records (optional, privacy-safe) | CSV/XLSX | Validation context |

**Out of scope for pilot**: Full ETL, production system access, custom integrations, AI provider setup.

---

## Week 1 Workflow

### Day 1–2: Ingest and Scaffold

1. **Clone or install Martenweave**
   ```bash
   pip install martenweave-core
   martenweave init ./pilot-model --name "Pilot Customer Domain"
   ```

2. **Profile source and target datasets**
   ```bash
   martenweave profile-dataset ./source_sample.csv --repo ./pilot-model
   martenweave profile-dataset ./target_sample.csv --repo ./pilot-model
   ```

3. **Infer draft model objects**
   ```bash
   martenweave infer-model ./pilot-model/generated/dataset_profiles/source_sample.json --repo ./pilot-model
   martenweave infer-model ./pilot-model/generated/dataset_profiles/target_sample.json --repo ./pilot-model
   ```
   Review the generated PatchProposals in `model/patch-proposals/`.

4. **Import existing mapping sheet (if available)**
   ```bash
   martenweave import-model-sheet ./legacy_mappings.xlsx --repo ./pilot-model
   ```

### Day 3–4: Validate and Enrich

1. **Validate the model**
   ```bash
   martenweave validate --repo ./pilot-model
   ```
   Fix any broken references or missing IDs.

2. **Build the index**
   ```bash
   martenweave build-index --repo ./pilot-model --jsonl
   ```

3. **Add ownership and context**
   - Edit canonical files to add `business_owner`, `technical_owner`, `domain`
   - Add `EntityContext` objects for SAP grain (e.g., `customer_sales_area`)

4. **Trace a key field**
   ```bash
   martenweave trace FEP-S4-KNVV-KDGRP --repo ./pilot-model
   ```
   Verify upstream and downstream relationships are visible.

### Day 5: Review and Score

1. **Generate health report**
   ```bash
   martenweave health --repo ./pilot-model
   ```

2. **Generate scorecard**
   ```bash
   martenweave scorecard --repo ./pilot-model
   ```

3. **Export review workbook**
   ```bash
   martenweave export-model --format xlsx --business-review --repo ./pilot-model
   ```

4. **Run impact analysis on a proposed change**
   ```bash
   martenweave impact ATTR-CUST-SALES-CUSTOMER-GROUP --repo ./pilot-model
   ```

---

## Success Metrics

Measure before and after where possible.

| Metric | Before (Baseline) | After (Pilot) | How to Measure |
|---|---|---|---|
| **Documentation coverage** | % of fields documented in existing sheet | % of fields with canonical objects | `martenweave scorecard` |
| **Ownership coverage** | % of objects with named owner | % of objects with named owner | `martenweave scorecard` |
| **Traceability** | Time to trace a field manually | Time via `martenweave trace` | Stopwatch test |
| **Gaps identified** | Unknown | Count of undocumented mappings or missing context | `martenweave health` + manual review |
| **Change readiness** | No structured change process | PatchProposals + ChangeRequests created | Count in `model/` |
| **Team onboarding** | Days to explain model | Minutes to search model | New team member test |

---

## Out of Scope for Pilot

Do not promise these in the pilot:

- Real-time sync with SAP or other systems
- Multi-user concurrent editing (Git merge handles conflicts, but is not real-time)
- Custom AI provider training or fine-tuning
- Production deployment or CI/CD integration
- Role-based access control beyond file-system permissions
- Automated data-quality monitoring

---

## Go / No-Go Criteria

### Go (expand to team or program)

- Scorecard shows >60% ownership coverage
- `martenweave readiness --repo ./pilot-model --profile pilot` reports no blocking gates
- Team can trace a field in under 60 seconds
- At least one ChangeRequest was created and reviewed
- Business owner can read and comment on the exported workbook

The readiness command is an exit criterion, not a shortcut around review. Resolve any blocker
through the normal PatchProposal and ChangeRequest path; high-risk changes retain their required
human approvals.

### No-Go (archive or revisit in 6 months)

- No named business owner willing to maintain the model
- Team has already committed to a competing MDM/catalog tool
- Data is too unstructured or volatile to model
- Security policy forbids Git or Markdown entirely

---

## Pilot Deliverables

At the end of the pilot, the prospect receives:

1. A working Martenweave repository on their laptop
2. A populated SQLite index (`generated/modelops.db`)
3. An Excel review workbook (`generated/model_export.xlsx`)
4. A health report and scorecard (JSON or CLI output)
5. A list of identified gaps and recommended next steps
6. Optional: a Git bundle for sharing (`martenweave git-bundle`)

---

## Pricing Hypothesis for Pilot

- **Evaluation**: Self-service for less than 32 consecutive days under the repository license
- **Pilot**: May be offered at no license fee under a written pilot agreement; optional paid
  facilitation ($2K–$5K) if we run it together
- **Post-pilot team offering**: TBD based on team needs; likely support, templates, assessment
  packs, or future hosted workspace functionality; the Core remains Apache-licensed
- **Enterprise**: TBD; only discussed after team-level success is proven

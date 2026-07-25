# Martenweave Pilot Demo Script

> A repeatable 15-minute walkthrough for showing Martenweave to a stakeholder.
> Use the `examples/customer_bp_model` repository as the demo target.

## Prerequisites

- Python 3.11+ installed
- Martenweave installed: `pip install -e .`
- A terminal open in the Martenweave repository root

## Demo Steps

### 1. Show the model repository (2 min)

```bash
ls examples/customer_bp_model/model
```

Talk through:
- Each `.md` file is a canonical object with YAML frontmatter.
- Objects have stable IDs like `DOMAIN-CUSTOMER-BP` and `ATTR-CUST-SALES-CUSTOMER-GROUP`.
- The model is the source of truth; everything else is generated from it.

### 2. Validate the model (2 min)

```bash
martenweave validate --repo examples/customer_bp_model
```

Talk through:
- Layer 1: every object has a valid ID, type, and status.
- Layer 2: cross-object references are checked (no broken links).
- Layer 3: SAP context rules are enforced (e.g., `KNVV` requires `customer_sales_area`).

### 3. Build the index (1 min)

```bash
martenweave build-index --repo examples/customer_bp_model --jsonl
```

Talk through:
- The SQLite index is disposable. You can delete `generated/` and rebuild it.
- JSONL exports are created for search and lineage.

### 4. Preflight and run the pilot assessment (3 min)

```bash
martenweave pilot-preflight \
  --mapping tests/fixtures/pilot/sap_customer_mapping.xlsx \
  --out /tmp/martenweave-preflight
martenweave run migration-assessment \
  --repo examples/customer_bp_model \
  --mapping tests/fixtures/pilot/sap_customer_mapping.xlsx \
  --out /tmp/martenweave-assessment
```

Talk through:
- This is the core commercial deliverable.
- Open the output folder and walk through each file.

### 5. Walk through assessment outputs (5 min)

```bash
ls /tmp/martenweave-assessment
```

**01_readiness_scorecard.md**
- Readiness level: seed → draft → review → ready.
- Metrics: ownership coverage, validation rule coverage, mapping logic coverage, etc.
- Each metric shows value, target, and status.

**02_gap_report.md**
- Consolidated view of all gaps found across validation, health, analysis, and scorecard.
- Gap score = gaps / total objects (lower is better).

**03_high_risk_fields.md**
- Ranked list of objects with risk reasons.
- Severity: high (blocking), medium (important), low (track).

**04_impact_reports/**
- One impact report per top high-risk object.
- Shows upstream and downstream dependencies.
- Use this before changing anything.

**05_business_review.xlsx**
- Styled Excel workbook with one sheet per object type.
- Includes reviewer notes column and status dropdowns.
- Business stakeholders can review without touching Markdown.

**06_recommendations.md**
- Executive summary and themed next steps.
- Derived directly from scorecard gaps and risk register.

**executive-summary/executive-summary.html, evidence-manifest.json, workbench-workspace.json**
- Client-ready readiness view, checksummed evidence inventory, and disposable local Workbench context.
- These remain generated evidence; none authorizes a canonical model change.

### 6. Compare workbook versions and promote a reviewed finding (2 min)

```bash
martenweave assessment compare-workbooks ./mapping-v1.xlsx ./mapping-v2.xlsx \
  --repo examples/customer_bp_model --out /tmp/martenweave-comparison
martenweave assessment-review set \
  --assessment /tmp/martenweave-assessment/manifest.json \
  --finding-id <finding-id> --disposition confirmed --reviewer migration-lead
martenweave assessment-review promote \
  --assessment /tmp/martenweave-assessment/manifest.json \
  --finding-id <finding-id> --repo examples/customer_bp_model
```

Talk through:
- The comparison is deterministic and evidence-only; it shows changes to mappings and matched model impact.
- A reviewer confirms a finding before promotion; the result is a PatchProposal, not an applied change.

### 7. Show additional commands (2 min)

```bash
martenweave health --repo examples/customer_bp_model
martenweave scorecard --repo examples/customer_bp_model
martenweave impact FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model
```

## Closing Questions

Ask the stakeholder:
1. Which of these gaps are already known to your team?
2. Who would own the business review of field mappings?
3. How do you currently track decisions about SAP field usage?
4. Would an audit-ready evidence package help your migration timeline?

## Next Steps

- Copy the assessment output into a shared folder or version control.
- Schedule a follow-up to assign owners to high-risk items.
- Re-run the assessment after changes to track progress.

# Agent 2 — SAP/MDM Domain Buyer Analysis

> **Role:** SAP/MDM Buyer Analyst for Martenweave Commercial Due Diligence  
> **Date:** 2026-06-09  
> **Version:** 0.4.0 (repo HEAD)  
> **Mandate:** Brutally honest evaluation from the perspective of someone who has done 3+ SAP S/4HANA migrations.

---

## Executive Summary

Martenweave is a **technically competent but commercially immature** product for the SAP migration market. The core engine works — validation, indexing, gap detection, impact analysis, and approval-gated patches are all implemented and tested. But the gap between "works in a demo" and "would be bought by a Deloitte migration lead" is **significant and specific**.

The product has **one genuinely strong wedge** (migration field mapping documentation as an Excel replacement) and **several plausible but unproven** use cases. Its biggest risks are: (1) the SAP domain pack is too thin to feel authoritative, (2) the CLI-only interface is a massive adoption barrier for SAP consultants, and (3) the examples feel like tutorials rather than real project artifacts.

**Verdict:** Not ready for enterprise SAP sales without a pilot-to-product bridge. The open-core strategy is correct, but the paid workflow is unclear.

---

## 1. Concrete SAP Pain Points

### Where Excel Field Mappings Actually Break Down

In real SAP migrations, the Excel mapping workbook is not just a document — it is the **operational system of record** for cutover. Teams maintain 50–200 tabs across multiple workbooks, versioned by email with filenames like `Mappings_v12_FINAL_FINAL_JD.xlsx`. The breakdown points are:

1. **Concurrent editing chaos.** Two consultants open the same workbook. One saves. The other saves 20 minutes later. Changes are silently lost. Git + Markdown frontmatter solves this, but only if the team already uses Git. Most SAP migration teams do not.

2. **No referential integrity.** In Excel, if you rename "Customer Group" to "Customer Classification" in the target sheet, every reference in the mapping, validation, and test-case tabs is now a lie. Martenweave's `REFERENCE_BROKEN` validation (`src/modelops_core/validation/pipeline.py:396`) catches this. **This is a real, paid-worthy feature.**

3. **No traceability.** When an auditor asks "why is KNVV-KDGRP mapped this way?" the answer is usually: "Ask Hans, he left in March." Martenweave's `Decision` and `Evidence` objects (`examples/customer_bp_model/model/DEC-CH01-A17-CUSTOMER-GROUP.md`) are designed for this. But the example decision is 5 lines of placeholder text. A real decision would need to reference a SAP note, a workshop minutes PDF, and a signed-off business rule. **The object model supports this; the examples do not demonstrate it.**

4. **Context loss.** A real KNVV field is not just "Customer Group in Sales Area." It is "Customer Group in Sales Area **for Sales Org CH01, Distribution Channel 01, Division 01, during the CH01-A17 migration wave, after the BP role FLCU01 was activated, with the exception of intercompany customers who use a different value list.**" Martenweave's `EntityContext` (`examples/customer_bp_model/model/CTX-CUSTOMER-SALES-AREA-S4.md`) captures the table and grain, but the example context object has no `wave`, `project_phase`, or `exception_category` fields. **The pain is real; the model is too shallow.**

### Consultant Turnover and Tribal Knowledge

This is the **strongest emotional pain point** Martenweave could sell against. When a senior FI-CO consultant leaves with the only copy of the KNB1-AKONT reconciliation account mapping logic, the project loses 2–4 weeks. Martenweave's canonical file format (Markdown + YAML, Git-friendly) genuinely solves this — if the knowledge was captured before the consultant left.

**The catch:** Capturing knowledge in Martenweave format is **more work** than capturing it in Excel. In Excel, you type the mapping and move on. In Martenweave, you must create:
- A `Domain` object
- An `Attribute` object (semantic meaning)
- A `FieldEndpoint` object (physical field)
- An `EntityContext` object (SAP grain)
- An `AttributeUsage` object (linking semantic to physical)
- A `Mapping` object (source → target)
- Optionally a `ValueList`, `ValidationRule`, `Decision`, and `Issue`

For **one field**, that is 6–10 files. The `examples/customer_bp_model` has 86 files for what a real consultant would model as perhaps 15–20 fields. **The abstraction is correct for governance, but it is a tax on speed during a migration sprint.**

### AMS Teams and "Why Is This Field Mapped This Way?"

AMS (Application Management Services) teams post-go-live genuinely need a field dictionary. But their query pattern is different from migration teams:
- **AMS query:** "User says Customer Group is wrong. What is the business rule? Who owns it? What value list applies?"
- **Migration query:** "Does this source column map to KNVV-KDGRP or KNVV-KDGRP is a different concept?"

Martenweave's `trace` and `impact` commands (`docs/architecture/DATA_LINEAGE_AND_IMPACT_MODEL.md`) serve the AMS use case better than the migration use case. But AMS teams have **small budgets** and usually report into a larger MDM initiative. They are a secondary ICP for a reason.

### Real Cost of a Wrong Field Mapping in Cutover

A wrong mapping in KNVV-KDGRP (Customer Group) does not just mean bad reporting. It means:
- Pricing conditions do not apply → sales orders fail → revenue stops
- Credit control group is wrong → customers get blocked or over-extended
- Statistics update to the wrong segment → management decisions based on garbage

The cost is **$50K–$500K per incident** depending on detection timing. Martenweave does not prevent wrong mappings — it documents them. The value proposition is **audit defense and faster root-cause analysis**, not error prevention. This must be clear in sales conversations.

---

## 2. Wedge Use Cases — Evaluate and Rank

### 2.1 BP/Customer/Vendor Model Documentation (the 85-object example)

**Rank: #1 — Most credible, but needs depth.**

The `examples/customer_bp_model` (`examples/customer_bp_model/model/`, 86 objects) demonstrates the full stack: Domain → Entity → Context → Attribute → FieldEndpoint → Mapping → ValueList → ValidationRule → Decision → Issue. It validates with zero errors and builds an index.

**What is credible:**
- The KNVV-KDGRP chain is a real, recognizable SAP pattern.
- The separation of `Attribute` (business meaning) from `FieldEndpoint` (physical field) is architecturally sound.
- The `Decision` object (`DEC-CH01-A17-CUSTOMER-GROUP.md`) shows intent to capture rationale.

**What is missing to make it sellable:**
- **No real decisions.** The decision body says "Accepted: map legacy customer group to KNVV-KDGRP." A real decision would cite the workshop date, attendees, the alternative considered (e.g., mapping to KNA1-KDGRP instead), and the SAP note that justified the choice.
- **No real value mappings.** `VLIST-LEGACY-CUST-GROUP.md` has placeholder values. A real migration would have 20–200 legacy values mapped to 5–20 S/4 values, with exceptions, unmapped codes, and business rules for each.
- **No wave or project scope.** Real BP→Customer migrations are phased by country, company code, or business unit. The model has no `wave`, `scope`, or `go_live_date` fields.
- **No test case linkage.** A real mapping is validated by a test case. There is no `TestCase` or `ValidationRun` object type linking mappings to actual data loads.

**Who pays:** Program director (migration budget).
**How much:** $2K–$5K pilot facilitation is plausible. $500–$2K/month subscription only if a web UI exists.
**Paid workflow credibility:** Medium. The pilot package (`docs/pilot-package.md`) is well-designed, but the deliverables (SQLite DB, Excel workbook, gap report) are not obviously better than what a competent consultant produces in Excel in 2 days.

---

### 2.2 Migration Field Mapping Control

**Rank: #2 — Strong pain, but Martenweave is only a partial solution.**

The core value is replacing the Excel mapping workbook with a validated, versioned, searchable model. The `Mapping` object (`examples/customer_bp_model/model/MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP.md`) links `source_endpoint` to `target_endpoint` with a `mapping_set` for grouping.

**What is credible:**
- `modelops validate` catches broken references (`REFERENCE_BROKEN`) and type mismatches (`REFERENCE_TYPE_MISMATCH`).
- `modelops export-model --format xlsx --business-review` produces a styled Excel workbook (`src/modelops_core/exports/export_service.py:186`) with read-only columns and reviewer notes. This is smart — it meets the buyer where they are (Excel) while keeping the canonical source in Git.

**What is missing:**
- **No multi-source mapping.** Real migrations often map 2–5 source systems to one target. A `Mapping` has one `source_endpoint` and one `target_endpoint`. There is no `MappingSet`-level orchestration showing the full source-to-target picture.
- **No transformation logic.** The `Mapping` object has no `transformation_rule`, `derivation_logic`, or `default_value` field. Real mappings are not 1:1 — they involve concatenation, lookups, date conversions, and conditional logic.
- **No load sequence awareness.** In a real cutover, KNA1 loads before KNVV. KNB1 loads after KNA1 but before KNVP. The model has no `load_sequence`, `dependency`, or `predecessor` fields.
- **No reconciliation rule.** After load, teams reconcile source count vs target count vs error count. No `ReconciliationRule` object exists.

**Who pays:** Migration workstream lead.
**How much:** This is the $20K–$100K "migration model build" professional services package (`docs/commercial-packaging.md:76`).
**Paid workflow credibility:** High for services, low for product. A team will pay a consultant to build this model once. They will not pay a subscription for the model itself.

---

### 2.3 Dataset-to-Model Gap Detection (CSV vs FieldEndpoint)

**Rank: #3 — Technically works, but the business value is weak.**

`modelops gaps` (`src/modelops_core/cli.py:473`) compares dataset columns against `FieldEndpoint` objects and reports unmatched columns.

**What is credible:**
- The `customer_sales_area_sample.csv` (`examples/customer_bp_model/data/samples/customer_sales_area_sample.csv`) has 6 columns. `modelops gaps` would flag `UNKNOWN_LEGACY_FIELD` as unmodeled.
- The gap detection supports CSV and XLSX, including multi-sheet workbooks.
- Gaps can be promoted to `Issue` objects or `PatchProposal` objects automatically.

**What is missing:**
- **The matching is trivial.** Gap detection does string normalization (`_normalize` in `src/modelops_core/gaps/gap_detection.py:50`: lowercases, replaces `_` and ` ` with `-`). It does not do fuzzy matching, semantic similarity, or SAP field name aliases (e.g., `KDGRP` is also known as `Customer Group`, `Cust. Group`, `Kundengruppe`).
- **The sample is toy-sized.** 8 rows, 6 columns. A real migration dataset has 50–500 columns and 10K–10M rows. The profiler handles large files with sampling (`src/modelops_core/cli.py:372`), but the gap detection logic does not scale in sophistication — just in volume.
- **No data quality gap detection.** It checks "is this column in the model?" not "does this column contain valid values?" A real gap is: "CUSTOMER_GROUP contains 'A17' but the target ValueList only allows '01', '02', '03'." Martenweave does not detect this.
- **False positives.** In real datasets, column names are often cryptic (`ZZFIELD1`, `TEMP_COL`, `LEGACY_XREF_7`). These will all be flagged as gaps, creating noise.

**Who pays:** Data quality workstream lead (small budget).
**How much:** $2K–$5K pilot. Hard to justify ongoing subscription.
**Paid workflow credibility:** Low. This is a nice-to-have feature, not a must-have workflow. Teams already handle this with manual inspection or Alteryx/Informatica profiling.

---

### 2.4 Validation Issue Triage

**Rank: #4 — Weak as a standalone use case.**

`modelops validate` produces a structured report with severity, code, message, and suggested fix. The `Issue` object type (`examples/customer_bp_model/model/ISS-CH01-A17-CONFIG-GAP.md`) captures problems.

**What is credible:**
- The validation pipeline (`src/modelops_core/validation/pipeline.py`) is genuinely well-designed. It catches broken references, duplicate IDs, circular references, missing owners, and SAP context violations.
- Issues can be created from gaps automatically (`--create-issues` flag).

**What is missing:**
- **No prioritization framework.** A real migration has 500–2,000 issues. They must be prioritized by: impact on go-live, effort to fix, owner availability, and dependency on other issues. The `Issue` object has `severity` and `status` but no `effort`, `priority`, `due_date`, or `blocks` fields.
- **No Jira integration.** Issue triage happens in Jira, ServiceNow, or ALM. Martenweave issues are Markdown files in Git. There is no bidirectional sync. The `issue_draft` module can generate GitHub issue drafts, but most enterprise SAP teams use Jira or ServiceNow, not GitHub.
- **No assignment workflow.** An issue is created, but who is notified? The `notifications` module (`src/modelops_core/notifications/`) exists but is basic. There is no email, Slack, or Teams integration.

**Who pays:** Project manager (if they care about structured issue tracking).
**How much:** Hard to charge for this alone.
**Paid workflow credibility:** Low. This is an enabler for other use cases, not a standalone paid workflow.

---

### 2.5 Impact Analysis for Field Changes

**Rank: #5 — Plausible, but depth is shallow.**

`modelops impact FEP-S4-KNVV-KDGRP` performs BFS traversal over `object_relationships` in the SQLite index (`src/modelops_core/impact/impact_service.py`).

**What is credible:**
- It finds upstream and downstream objects up to a configurable depth (default 2).
- It groups results by type, direction, and relationship.
- The `ImpactReport` model (`src/modelops_core/impact/impact_report.py`) is well-structured.

**What is missing:**
- **No severity weighting.** The impact report lists affected objects but does not rank them by business criticality. A `ValueMapping` affecting 2 codes vs 200 codes is the same "depth 2, downstream" entry. Real impact analysis needs: "This change affects the cutover load for 3 company codes and 50,000 customer records."
- **No change effort estimation.** Impact analysis should answer: "If we change KNVV-KDGRP, how many mappings, test cases, and load scripts must be updated?" The report lists objects but does not estimate effort or cost.
- **No what-if simulation.** The user cannot ask: "What if we split Customer Group into two fields?" The impact service only traces existing relationships.
- **Relationship graph is sparse.** The example model has relationships, but a real model would have 10x more. The BFS is O(n) and will work, but the output will be a wall of text without good filtering.

**Who pays:** Lead data architect (champion role).
**How much:** Part of the subscription or pilot package.
**Paid workflow credibility:** Medium. This is a feature, not a workflow. It supports the change request process but does not replace it.

---

### 2.6 MDM Governance Evidence Layer

**Rank: #6 — Correct vision, wrong timing.**

The governance layer (`OwnershipRole`, `Decision`, `Evidence`, `ChangeRequest`, `PatchProposal`) is architecturally sound. The `scorecard` command (`src/modelops_core/reports/scorecard_service.py`) generates metrics like `ownership_coverage`, `evidence_coverage`, and `sap_table_coverage`.

**What is credible:**
- The scorecard is a genuinely useful governance dashboard. It measures: completeness, ownership, validation rule coverage, value list coverage, traceability, and freshness.
- The `readiness_level` (seed → draft → review → ready) is a good mental model.

**What is missing:**
- **No SOX/GDPR-specific evidence types.** Auditors ask for: "Who approved this mapping? When? What was the alternative? Who tested it?" The `Decision` object has `evidence` but no `approver_signature`, `approval_date`, or `audit_trail_id` fields.
- **No retention policy.** Governance evidence must be retained for 7+ years in many industries. Martenweave files live in Git. Git history is the retention policy. This is acceptable but must be explained to auditors.
- **The scorecard metrics are naive.** `lov_coverage` expects every `FieldEndpoint` to have a `ValueList`. In SAP, many fields use check tables or domain values, not explicit value lists. `mapping_logic_coverage` expects every `Mapping` to have a `ValueMapping`. Many mappings are 1:1 with no value translation. These metrics will show "fail" for correct models, undermining trust.

**Who pays:** Data governance manager or compliance officer.
**How much:** $10K–$50K MDM foundation build.
**Paid workflow credibility:** Low for self-serve, medium for services. Governance teams already evaluate Collibra/Informatica. Martenweave is lighter but must prove it is not "just another thing to maintain."

---

### 2.7 AMS Knowledge Capture and Repeated Incident Reduction

**Rank: #7 — Real pain, but Martenweave is over-engineered for it.**

AMS teams need a field dictionary: "What does KNVV-KDGRP mean? Who owns it? What values are allowed?"

**What is credible:**
- `modelops search "customer group"` and `modelops query --type Attribute` provide fast lookup.
- The canonical files are human-readable. An AMS analyst can open `FEP-S4-KNVV-KDGRP.md` and read the business context.

**What is missing:**
- **AMS teams do not write Markdown.** They work in SAP GUI, ServiceNow, Confluence, and Excel. Asking them to maintain canonical files in Git is a non-starter.
- **No SAP GUI integration.** The ideal AMS tool is a right-click in SE16: "Show Martenweave definition for this field." That does not exist and is not on the roadmap.
- **Incident reduction is unmeasured.** There is no evidence that having a Martenweave model reduces ticket resolution time. The pilot package claims "Time to onboard a new consultant drops from 2 weeks to 2 days" (`docs/commercial-positioning.md:43`), but this is a hypothesis, not a measured outcome.

**Who pays:** AMS manager (small budget, needs MDM initiative approval).
**How much:** $500–$2K/month if part of a larger Team Workspace subscription.
**Paid workflow credibility:** Low. This is a future expansion use case, not a beachhead.

---

## 3. "Model Registry" Language

### Is "Model Registry" Clear to SAP Consultants?

**No.** An SAP consultant who has spent 15 years in SAP GUI, Excel, and ALM does not know what a "model registry" is. They would call it:
- **"Field mapping tracker"** (if they are a migration consultant)
- **"Data model wiki"** (if they are an architect)
- **"Migration knowledge base"** (if they are a program manager)
- **"Mapping documentation tool"** (if they are a tester)
- **"The thing that replaces our Excel sheets"** (if they are honest)

"Model registry" is ML/AI infrastructure language. It evokes Weights & Biases, MLflow, or Hugging Face. SAP consultants do not train models. They migrate master data. **The language is a credibility tax.**

### What Would They Call It?

The positioning docs (`docs/commercial-positioning.md`) get this partially right:
- "A searchable model that survives team turnover" — good
- "Defensible documentation and change tracking" — good
- "The field dictionary your support team actually trusts" — good

But the product name and category are wrong. Martenweave should be positioned as:
> **"A master data mapping and governance layer for SAP migrations."**

Not "model registry." Not "ModelOps." Not "canonical model knowledge layer." Those are internal architecture terms, not buyer terms.

### Is the Language Too Abstract for the Actual Buyer?

**Yes.** The program director (budget owner) does not care about "canonical files" or "deterministic validation." They care about:
- "Will this pass audit?"
- "Will my go-live be on time?"
- "Will I lose knowledge when the consultant leaves?"

The current messaging (`docs/commercial-positioning.md:87`) says:
> "Martenweave turns your spreadsheet mappings into a structured, searchable, versioned model knowledge layer."

Better:
> "Martenweave replaces your Excel mapping workbooks with a validated, audit-ready mapping system that lives in Git. Every field has an owner, a history, and a business meaning — so when your consultant leaves, the knowledge stays."

**Recommendation:** Drop "model registry" from all buyer-facing materials. Use "mapping documentation," "migration knowledge base," or "master data governance layer."

---

## 4. Credibility Gaps

### What Would Convince a Deloitte/Accenture Migration Lead to Try This?

A Big 4 migration lead has seen 20+ tools come and go. They are skeptical of:
1. **Tools that add work.** They bill by the hour. If Martenweave takes longer than Excel, they will not use it unless the client demands it.
2. **Tools with no reference.** They need a case study: "Used on a $2M S/4HANA migration for a Fortune 500 manufacturer. 150 fields modeled. 3 consultants. 0 audit findings."
3. **Tools that are not SAP-certified.** SAP certification is a long, expensive process. Martenweave does not need it, but the absence is a objection.

**What would convince them:**
- A **real reference project** with >100 fields, >2 consultants, and a post-go-live testimonial.
- An **Excel import** that converts their existing mapping workbook into canonical objects in under 10 minutes. The `import-model-sheet` command exists (`src/modelops_core/cli.py:831`), but it imports from Google Sheets, not Excel. The `model_sheet_import_service` handles XLSX (`src/modelops_core/imports/model_sheet_import_service.py`), but the CLI command is `import-sheet` (Google Sheets) not `import-excel`.
- **A pre-built SAP template** with 200+ fields for BP→Customer, not 15. The `customer_bp_model` has 86 objects but covers maybe 10–15 real SAP fields. A Deloitte lead would laugh at this.

### What Would Convince an Internal SAP MDM Manager?

An internal MDM manager cares about:
1. **Integration with existing tools.** They already have Collibra, Informatica, or SAP MDG. Martenweave must integrate, not replace.
2. **Business user adoption.** Business users will not use a CLI. They need a web UI or at least a Confluence plugin.
3. **Total cost of ownership.** Maintaining 86 Markdown files for 15 fields is not obviously cheaper than maintaining a Confluence page.

**What would convince them:**
- A **Confluence or SharePoint export** so business users can read the model without installing Python.
- A **Collibra connector** that syncs Martenweave canonical objects to Collibra assets.
- Evidence that **maintenance effort drops** after initial build. Currently, there is no evidence.

### What Is Missing to Make the Examples Feel "Real" Rather Than "Demo"?

The `customer_bp_model` is a **tutorial**, not a **reference implementation**. Here is what makes it feel like a demo:

| Aspect | Current State | What "Real" Looks Like |
|---|---|---|
| **Object count** | 86 files | 500–2,000 files for a single migration object |
| **Field coverage** | ~10–15 SAP fields | 50–200 fields per migration object |
| **Value mappings** | Placeholder values (`A17`, `B02`) | 20–200 legacy → target mappings with exceptions |
| **Decisions** | 1-line acceptance | Multi-page rationale with alternatives, risks, and sign-offs |
| **Issues** | 1 generic config gap | 50+ issues: data quality, scope conflicts, missing values, custom fields |
| **Test data** | 8 rows, 6 columns | 10K–1M rows, 50–500 columns, with real data quality problems |
| **Project context** | None | Wave plan, company codes, go-live dates, cutover sequences |
| **Ownership** | `PERSON-BUSINESS-OWNER` placeholder | Real names, email addresses, escalation paths |
| **Systems** | 3 generic systems | 5–15 systems: ECC, S/4, CRM, MDM, data lake, BI, 3rd party APIs |
| **Load dependencies** | None | Sequence: KNA1 → KNB1 → KNVV → KNVP, with reconciliation gates |

**The fix:** Create a "real-world reference model" that is 10x larger and 10x more detailed. This is a major content investment, but without it, every prospect will say "this is just a demo."

---

## 5. Workflow Fit

### Does Martenweave Fit Into Real SAP Project Workflows?

**Partially.** It fits best in the **design and documentation phase** of a migration. It fits poorly in the **execution and cutover phase**.

**Where it fits:**
- **Blueprint phase:** Architects design the target model. Martenweave enforces structure and catches broken references.
- **Realization phase:** Consultants document mappings. Martenweave provides a shared, versioned source of truth.
- **Testing phase:** Testers trace fields from source to target. `modelops trace` and `modelops impact` help.
- **Audit phase:** Auditors review decisions, evidence, and change history. The canonical files are human-readable and Git-auditable.

**Where it does not fit:**
- **Data extraction:** Martenweave does not extract data from SAP. It documents what should be extracted.
- **Transformation:** Martenweave does not run ETL. It documents the mapping logic.
- **Load:** Martenweave does not load data into SAP. It documents the target fields.
- **Reconciliation:** Martenweave does not reconcile source vs target counts. It has no `ReconciliationRun` object.
- **Cutover:** Martenweave does not manage cutover tasks, sequences, or rollback plans.

**The gap:** A migration team uses 5–10 tools: SAP GUI, Excel, Alteryx/Informatica, Jira, Confluence, Test Manager, Cutover Manager. Martenweave replaces **one** of these (Excel for mappings) and adds **another** tool to the stack. The value must be >10x better than Excel to justify the switching cost.

### When Would a Team Adopt This?

**Best timing:**
1. **Project start (blueprint phase):** The team has not yet committed to Excel. They can adopt Martenweave as the standard from day one. This is the ideal case but rare — most teams already have templates.
2. **Mid-migration, post-audit finding:** An audit finds that mappings are undocumented. The program director needs to show progress. Martenweave is a fast way to create structured documentation under pressure.
3. **Post-go-live, AMS handover:** The migration team is leaving. The AMS team needs a knowledge base. Martenweave can be the handover artifact.

**Worst timing:**
- **Mid-migration, already committed to Excel:** Switching costs are too high.
- **During cutover:** No one has time to learn a CLI tool.
- **Post-go-live, AMS team has no Git skills:** The tool is unusable.

### Who Would Maintain the Canonical Files Day-to-Day?

**This is the hardest question.** The current answer in the docs is: "The Data Steward" (`docs/commercial-positioning.md:54`).

In reality:
- **Migration consultants** will not maintain canonical files. They are billable. Documentation is overhead.
- **Data stewards** might maintain them, but only if they are technical enough to use Git and CLI.
- **Business users** will not touch Markdown files. Full stop.
- **AMS analysts** might read them, but will not write them.

**The most likely maintainer:** A **technical business analyst** or **junior data architect** who is assigned to "model governance" as a 20–50% role. They need:
- A web UI (does not exist)
- Excel import/export (partially exists)
- Clear templates and naming conventions (exists but thin)
- Management mandate ("Thou shalt document in Martenweave")

Without a web UI, the maintainer must be comfortable with:
```bash
modelops validate
modelops build-index
git add model/
git commit -m "Update KNVV-KDGRP mapping"
git push
```

This is **not** a realistic profile for the average SAP migration team member.

---

## 6. Specific Recommendations

### To Make the SAP Use Case Sellable

1. **Expand the SAP domain pack from 4 tables to 20+.** Add KNA1, KNVK, ADRC, ADR6, BUT020, BUT021, TVKOT, T077D, and common FI-CO tables (SKA1, SKB1, BSEG, BKPF). Add composite-key awareness (KNVV grain = KUNNR+VKORG+VTWEG+SPART).

2. **Create a "real-world" reference model.** 500+ objects, 50+ fields, real value mappings, real decisions, real issues, real project context. This is a content project, not a code project.

3. **Add transformation logic to Mappings.** A `transformation_rule` field, or a `TransformationLogic` object type, is essential. Real mappings are not 1:1.

4. **Add load sequence and dependency objects.** `LoadStep`, `LoadDependency`, `ReconciliationRule` would make Martenweave relevant to cutover planning.

5. **Build a web UI for read-only browsing.** Even a static HTML site generated from the index (`modelops docs generate` exists but is basic) would help business users and AMS teams. A full review UI is the Team Workspace subscription feature.

6. **Add Excel-native import/export round-trip.** The `export-model --format xlsx --business-review` is good. The missing piece is: consultant edits the Excel, imports it back, Martenweave generates a PatchProposal with diffs. This meets the team where they are.

7. **Drop "model registry" from buyer-facing language.** Use "migration mapping documentation," "master data governance layer," or "SAP field knowledge base."

8. **Get one real reference customer.** Even a small one. A $500K migration with 2 consultants and a post-go-live testimonial is worth more than 10 example models.

### What Not to Build (Yet)

1. **Do not build real-time SAP connectivity.** The local-first, read-only architecture is a strength. Do not weaken it by adding RFC connectors.
2. **Do not build a no-code ETL tool.** That is a different product. Stay in the documentation layer.
3. **Do not chase Collibra/Informatica feature parity.** You will lose. Compete on being lightweight, Git-native, and migration-specific.
4. **Do not build Team Workspace before 10+ CLI adoptions.** The docs (`docs/commercial-packaging.md:127`) already say this. Stick to it.

---

## 7. Final Verdict

| Criterion | Score | Notes |
|---|---|---|
| **SAP domain depth** | 4/10 | 4 tables, no composite keys, no S/4 vs ECC |
| **Example realism** | 3/10 | 86 objects, toy data, placeholder decisions |
| **Pain point match** | 7/10 | Excel replacement is real; other pains are partial |
| **Buyer language fit** | 4/10 | "Model registry" is wrong; positioning docs are better |
| **Workflow integration** | 5/10 | Fits design phase; does not fit execution |
| **Adoption barrier** | 3/10 | CLI-only is a massive barrier for SAP consultants |
| **Paid workflow clarity** | 6/10 | Pilot package is clear; subscription value is vague |
| **Credibility for Big 4** | 4/10 | No reference customer, no pre-built templates, no certification |
| **Credibility for internal MDM** | 5/10 | Good vision; weak integration and business user adoption |
| **Open-core strategy** | 8/10 | Correctly keeps core free; paid features are convenience |

**Overall: 5.1/10 — Promising foundation, not yet a sellable SAP product.**

The technical architecture is sound. The validation pipeline is strong. The approval-gated patch flow is safe. But the **SAP domain pack is too thin, the examples are too small, the interface is too technical, and the buyer language is too abstract**.

**Recommended next 90 days:**
1. Expand SAP domain pack to 20+ tables with composite-key rules.
2. Build one 500-object reference model with real value mappings and decisions.
3. Run 3–5 free pilots with real migration teams. Measure: time to trace a field, audit finding reduction, consultant onboarding speed.
4. Fix buyer-facing language (drop "model registry").
5. Do not build a web UI until CLI adoption is proven.

---

*Analysis based on repository inspection of `metalhatscats/martenweave-core` at commit `HEAD` (main branch, v0.4.0). Evidence cited from specific file paths where relevant.*

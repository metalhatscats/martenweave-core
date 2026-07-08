# Martenweave Commercial Due Diligence — Synthesis Report

**Synthesis Lead:** Agent 7  
**Date:** 2026-06-09  
**Sources:** Agent 1 (Product/Market), Agent 2 (SAP/MDM Buyer), Agent 3 (Competitive), Agent 4 (GTM/Pricing), Agent 5 (Technical Audit), Agent 5 (Website Audit), Agent 6 (Red Team)  
**Product Version:** 0.4.0 (`metalhatscats/martenweave-core`)  
**Status:** Zero revenue, zero public traction, core repo 404, CLI-only, AI stubbed

---

## 1. Executive Verdict

**Conditional commercial potential**

- The pain is real, quantified, and budgeted indirectly: SAP migration rework costs $250K–$750K per project, 82% of projects overrun, and 59–65% exceed schedule (Agent 1, WJAETS-2025-0374, Vaka 2024).
- The tool works: ~1,200 tests pass, 4 example models validate cleanly, deterministic validation (Layer 1–3), gap detection, impact analysis, and approval-gated patch workflow are all implemented and tested (Agent 5 Technical Audit).
- There is **zero evidence of paid adoption, community traction, or public repo access**. The core GitHub repo returns HTTP 404 (Agent 5 Website Audit, Agent 6). Web search returns zero relevant results for "Martenweave" (Agent 5 Website Audit).
- The product is **CLI-only with no UI**, which excludes ~90% of the SAP migration ICP (Agent 2, Agent 6). The `MVP_SCOPE.md` describes 8 UI screens that do not exist (Agent 5 Technical Audit).
- AI integration is **stubbed by default** (`NoProviderAdapter` does keyword matching, not LLM reasoning) (Agent 5 Technical Audit, Agent 6). The patch proposal validator — the safety gate for AI-generated changes — has only **4 tests covering 38 lines** (Agent 5 Technical Audit, Agent 6).
- The fastest path to first revenue is **services-led** (migration readiness assessment, $15K–$25K), not product-led growth or SaaS (Agent 4). SaaS is an 18–36 month horizon.
- The 2027 SAP ECC end-of-maintenance deadline creates a hard forcing function (~21,000 enterprises still on ECC), but the window is finite and shrinking (Agent 1).
- Documentation drift is significant: `AGENTS.md` has wrong version strings and wrong file paths; `SYSTEM_ARCHITECTURE.md` references a non-existent Next.js UI; `MVP_SCOPE.md` uses obsolete ID formats (Agent 5 Technical Audit, Agent 6).
- The website is polished and well-written but has **zero discoverability** — no blog, no case studies, no demo video, no email capture, no community hub (Agent 5 Website Audit).
- The most honest description is: **a consulting accelerator with product ambitions**. Do not treat it as a sellable software product today.

---

## 2. One-Sentence Commercial Thesis

> Martenweave can sell to **SAP S/4HANA migration program managers at mid-market enterprises and boutique system integrators** when **an audit finding, consultant departure, or go-live delay forces the team to document field mappings under pressure** because it reduces **the $250K–$750K cost of migration rework caused by undocumented, broken, or scattered field mappings** by providing a **validated, Git-native, searchable model knowledge layer with deterministic cross-reference checks and human-gated AI patch proposals** better than **Excel workbooks + SharePoint + tribal knowledge**.

---

## 3. Best Initial ICP

### ICP #1 — Boutique SAP System Integrator (Best near-term path)

| Dimension | Detail |
|---|---|
| **Buyer** | Delivery director or migration practice lead at a 20–200-person SAP consultancy |
| **Daily user** | Senior data architect / migration consultant |
| **Pain** | Every project rebuilds the same Excel mapping templates from scratch; knowledge walks out when consultants leave; clients demand audit-ready documentation at go-live |
| **Budget source** | Internal methodology investment + client project markup (15–25%) |
| **Why now** | 2027 ECC deadline is compressing project pipelines; SIs need differentiation from Big 4 |
| **Proof needed** | One case study showing "modeled 100+ fields, 2 consultants, 0 audit findings" |
| **Sales difficulty** | Medium. Procurement is light, but the SI must believe the tool reduces their delivery cost, not just the client's risk |

### ICP #2 — Mid-Market SAP Migration Program Director (Best direct path)

| Dimension | Detail |
|---|---|
| **Buyer** | Program director / data workstream lead on a $500K–$5M S/4HANA migration |
| **Daily user** | Lead data architect (champion, not buyer) |
| **Pain** | Audit finding on mapping documentation; go-live delay caused by data-quality surprise; consultant turnover erased tribal knowledge |
| **Budget source** | Migration program budget (reactive, often unallocated until disaster) |
| **Why now** | 2027 ECC deadline; post-audit remediation budgets are real and urgent |
| **Proof needed** | Sanitized before/after: "We found 40% of mappings had no owner and 12% had broken references" |
| **Sales difficulty** | Medium-High. Buyer is non-technical and must justify a CLI tool to a steering committee that expects SAP-certified solutions |

### ICP #3 — Data Governance Team Lead (Highest value, hardest sale)

| Dimension | Detail |
|---|---|
| **Buyer** | Head of data governance / MDM lead at a 500–5,000-employee enterprise |
| **Daily user** | Data steward (often non-technical, resistant to CLI) |
| **Pain** | Collibra/Informatica is overkill and 6–12 months to implement; team needs lightweight governance for migration only |
| **Budget source** | Data governance budget ($150K–$500K+/yr) |
| **Why now** | AI initiative requires "clean data layer"; board pressure for data governance |
| **Proof needed** | Working integration with existing catalog or at least a Confluence export; SOC 2 documentation |
| **Sales difficulty** | Very High. These buyers expect SaaS UI, SSO, RBAC, and audit certifications. Martenweave has none. |

---

## 4. Best Wedge Use Case

**Wedge name:** Migration Field Mapping Documentation & Audit Defense

| Dimension | Detail |
|---|---|
| **User** | Lead data architect on a mid-market SAP S/4HANA migration |
| **Input artifacts** | Existing Excel mapping workbook (e.g., `Mappings_v12_FINAL.xlsx`), SAP table/field list, legacy source column names, workshop decision notes |
| **Output artifact** | Validated canonical model (Markdown + YAML frontmatter) + SQLite index + gap report + styled Excel export for business review |
| **Before workflow** | Consultant maintains 50–200 Excel tabs, emails versions, renames fields manually, loses track of why KNVV-KDGRP maps to "Customer Group", has no referential integrity. When the consultant leaves, the next person starts from scratch. Audit asks for lineage; team has none. |
| **After workflow** | Team runs `modelops init`, imports the Excel workbook (via `import-model-sheet` or manual scaffold), validates with `modelops validate` (catches broken references and SAP context violations in seconds), builds index with `modelops build-index`, exports business-review Excel with `modelops export-model --format xlsx --business-review`. Every field has an owner, a decision history, and a traceable ID. When a consultant leaves, the knowledge stays in Git. |
| **Why someone pays** | Audit defense and risk reduction. The program director buys when an audit finding or go-live delay makes the cost of Excel chaos visible. The SI buys when it can package the output as a client deliverable. |
| **How to demo in 15 minutes** | 1. Show the `customer_bp_model` example (`examples/customer_bp_model/`). 2. Run `modelops validate --repo ./customer_bp_model` — zero errors, 86 objects. 3. Run `modelops impact FEP-S4-KNVV-KDGRP` — show upstream/downstream trace. 4. Run `modelops export-model --format xlsx --business-review` — open the styled Excel workbook. 5. Show `DEC-CH01-A17-CUSTOMER-GROUP.md` — a decision object with evidence link. |
| **What must exist in the repo/site to support this wedge** | A **real-world reference model** (500+ objects, 50+ fields, real value mappings, real decisions, real issues) — the current 86-object example is a tutorial, not a reference implementation (Agent 2). An **Excel-native import/export round-trip** so consultants can edit in Excel and re-import. A **2-minute demo video** on the homepage. A **sanitized case study** PDF. |

---

## 5. Pain-Budget Matrix

| # | Pain | Persona | Frequency | Cost of pain | Current workaround | Martenweave fit | Willingness to pay | Confidence | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Field mapping chaos — Excel workbooks drift, versions conflict, references break | Lead Data Architect | Daily | $50K–$500K per wrong mapping in cutover | Excel + SharePoint + email | High | Medium | High | Core value proposition; `modelops validate` catches broken references (`REFERENCE_BROKEN`) |
| 2 | Consultant turnover erases tribal knowledge | Program Director | Per event | 2–4 weeks lost per senior departure | "Ask Hans, he left in March" | High | High (reactive) | Medium | Emotional pain; `Decision` + `Evidence` objects designed for this but examples are placeholder text |
| 3 | Audit finding on data mapping or lineage documentation | Program Director / Auditor | Per audit | $100K–$250K remediation + delay | Rush-documentation sprints | High | High (panic) | High | Best trigger event; deterministic validation + Git history = audit trail |
| 4 | Late discovery of dataset-to-model gaps during UAT | Data Quality Lead | Per test cycle | Rework, retest, cutover delay | Manual inspection, Alteryx | Medium | Low-Medium | Medium | `modelops gaps` works but matching is trivial (string normalization only); no value-mismatch detection |
| 5 | Undocumented business rules (e.g., "Customer Group mandatory for CH01/01") | Data Steward | Daily | Support tickets, incorrect loads | Confluence pages, workshop minutes | Medium | Low | Medium | `Decision` object exists but no real-world depth in examples |
| 6 | Unsafe AI experimentation — teams fear uncontrolled model mutation | CIO / CDO | Per AI initiative | Governance failure, board risk | Ban AI from touching SAP | Medium | Medium | Low | AI is stubbed (`NoProviderAdapter`); safety architecture is sound but patch validator has only 4 tests |
| 7 | No single searchable field dictionary for AMS handover | AMS Manager | Per incident | 30–60 min per ticket resolution | SE16 + tribal knowledge | Medium | Low | Medium | `modelops search` works but AMS teams do not use CLI; needs read-only UI |
| 8 | Post-go-live stabilization costs exceed plan | Program Director | Per go-live | ~$157K/day during cutover (Vaka 2024) | Overtime, emergency consulting | Low | Medium | Low | Martenweave documents; it does not prevent errors. Value is pre-go-live, not cutover |
| 9 | Data governance initiative fails due to lack of business value connection | Data Governance Manager | Per initiative | $150K–$500K tool spend with no adoption | Collibra/Informatica (overkill) | Medium | Low | Low | Gartner: 80% of governance initiatives fail by 2027. Martenweave is narrow but unproven at enterprise scale |
| 10 | Multiple source systems map to one target with no orchestration view | Migration Architect | Per mapping design | Design errors, load failures | Multiple Excel tabs, LTMOM | Low | Low | Medium | `Mapping` has one source and one target; no multi-source or transformation logic fields |
| 11 | Scorecard shows "fail" for correct models due to naive metrics | Data Governance Manager | Per review | Loss of trust in tool | Manual review | Low | Low | High | `lov_coverage` and `mapping_logic_coverage` metrics are naive (Agent 2) |
| 12 | Patch proposal safety gaps — `before` field ignored, bypass flags too easy | IT Security / Compliance | Per AI proposal | Uncontrolled mutation risk | Ban AI tools | Medium | Low | High | `before` field is parsed but never used during apply; `--force` exists at multiple layers |

---

## 6. Competitive Positioning

### A. Excel / Confluence / SharePoint

| Dimension | Assessment |
|---|---|
| **Where Martenweave wins** | Deterministic validation (broken references, duplicate IDs, SAP context rules); Git-native versioning; AI patch proposals with human approval; structured audit trail via `Decision`/`Issue`/`ChangeRequest` objects |
| **Where it loses** | Adoption friction — Excel is free, universally understood, and requires zero onboarding. Martenweave requires CLI, YAML frontmatter, Git literacy. Speed of ad-hoc edits: changing a cell in Excel is faster than editing a Markdown file, running `modelops validate`, and rebuilding an index. Non-technical users (business analysts, data stewards) cannot use it. |
| **How to position without sounding fake** | *"We do not replace Excel. We replace the 17 versions of `Mappings_FINAL_v9.xlsx` that your team emails each other. Martenweave validates what Excel cannot: broken references, missing owners, and SAP context errors — before they reach UAT."* |

### B. Data Catalogs / Governance Platforms (Collibra, Alation, Informatica, Atlan, DataHub)

| Dimension | Assessment |
|---|---|
| **Where Martenweave wins** | Canonical files as source of truth (Markdown+YAML in Git, not a proprietary catalog database); deterministic offline validation (no JDBC connectors needed); SAP-native semantic layer (KNVV→`customer_sales_area` rules); local-first, zero SaaS lock-in; gap detection against CSV/XLSX samples; AI patch proposals with human approval |
| **Where it loses** | No live metadata scanning; no visual lineage graphs; no SSO/RBAC; no policy management; no data marketplace; no enterprise procurement credibility. Collibra has 10+ years of connectors and UI polish. DataHub has the largest OSS catalog community. |
| **How to position without sounding fake** | *"Collibra governs your data warehouse. Martenweave governs your migration model *before* the warehouse exists. Use us during the 12-month S/4HANA project, then feed the canonical index into Collibra post-go-live. We are 10x cheaper and deploy in hours, not months."* |

### C. SAP-Native Tooling (MDG, Datasphere, Signavio, LeanIX)

| Dimension | Assessment |
|---|---|
| **Where Martenweave wins** | Free and open source; deploys in hours; deterministic validation in seconds; no SAP certification or procurement review required; designed for pre-go-live migration projects where MDG is not yet deployed; AI patch proposals faster than MDG manual workflows |
| **Where it loses** | MDG has direct SAP table integration, real-time data quality execution, enterprise workflow engines, and SAP certification. Datasphere executes data movement; Martenweave only documents it. Signavio and LeanIX are complementary, not competitive — but SAP teams may expect an all-SAP stack. |
| **How to position without sounding fake** | *"SAP MDG governs live master data records. Martenweave documents the *design decisions* that tell MDG what to govern. Use Martenweave during migration blueprinting, then hand the canonical model to your MDG team at go-live."* |

### D. AI Document Chat / RAG (ChatGPT Enterprise, custom RAG)

| Dimension | Assessment |
|---|---|
| **Where Martenweave wins** | Deterministic truth enforcement (regex, schema, reference checks); approval state tracking (`draft` → `PatchProposal` → `ChangeRequest`); guaranteed broken reference detection; hard-coded SAP context rules; structured audit trail with object IDs; reproducible validation pipeline |
| **Where it loses** | ChatGPT Enterprise is already procured at most Fortune 500 companies. RAG retrieves by semantic similarity, not business hierarchy — but users already have it. Martenweave's default AI is keyword matching (`NoProviderAdapter`), which is weaker than ChatGPT with RAG over Excel files. |
| **How to position without sounding fake** | *"ChatGPT can read your Excel files. It cannot guarantee that a field rename in one sheet propagates to every dependent mapping. Martenweave is the governance layer *around* AI-generated changes — validators verify, humans approve, every change is traceable."* |

### E. Custom Consulting Scripts / ABAP / Python

| Dimension | Assessment |
|---|---|
| **Where Martenweave wins** | Self-documenting canonical files; shared schema and ID format across projects; `Decision`/`Issue`/`ChangeRequest` objects for audit trail; AI-assisted patch proposals; cross-project consistency; Git-native collaboration |
| **Where it loses** | ABAP runs inside SAP and processes millions of records in minutes. Python scripts are infinitely flexible. Martenweave is opinionated about object types and does not execute data loads. |
| **How to position without sounding fake** | *"Your ABAP scripts solve today's load. Martenweave solves tomorrow's audit. When the script author leaves, the script is a mystery. When a Martenweave modeler leaves, the model, decisions, and lineage stay in Git."* |

### F. dbt / SQLMesh / Data Contracts

| Dimension | Assessment |
|---|---|
| **Where Martenweave wins** | SAP-native semantic layer; design-time validation without a warehouse connection; conceptual lineage (BusinessEntity → Attribute → FieldEndpoint); AI patch proposals |
| **Where it loses** | dbt has 100,000+ community members, runs inside the warehouse, and has column-level SQL lineage. SQLMesh has virtual environments and automatic data contracts. Both are analytics engineering tools, not migration documentation tools — but the dbt analogy may confuse buyers. |
| **How to position without sounding fake** | *"dbt documents how data transforms in your warehouse. Martenweave documents what your SAP fields *mean* before they reach the warehouse. If you use dbt for your S/4HANA data lake, Martenweave feeds the semantic definitions into your dbt models."* |

---

## 7. Monetization Options

| Rank | Option | Expected buyer | Offer | Price hypothesis | Sales cycle | Build requirement | Risk | Recommendation |
|---|---|---|---|---|---|---|---|---|
| 1 | **Productized audit / service** | Migration program manager / CIO | "S/4HANA Migration Readiness Assessment": audit Excel mappings, build canonical model, deliver gap report + readiness scorecard | $15,000–$25,000 per assessment | 2–6 weeks | Sample deliverables, sales deck, repeatable methodology | Services revenue does not scale; buyer may treat as one-off | **✅ Do this now.** Fastest path to first dollar. Uses existing CLI capabilities. |
| 2 | **Consulting accelerator** | Boutique SAP consultancy | Co-branded "model-driven delivery" methodology; consultancy uses Martenweave internally, charges client markup for traceable docs | 15–25% project markup ($30K–$50K on $200K project) | 1–3 months | Training deck, case study, white-labelable reports | Consultancy may adopt free tool without paying | **✅ Pursue in parallel.** Best distribution channel. |
| 3 | **Training / workshops** | SAP consultancy or enterprise team | 1–2 day "Canonical Modeling for SAP Migrations" workshop; hands-on lab | $800–$1,500/person; $10K–$20K on-site for 12 people | 2–4 weeks | Training deck, lab exercises, trainer credibility | Lumpy revenue, scales with trainer time | **✅ Viable lead gen.** Low risk, fast to test. Validates demand. |
| 4 | **Paid domain packs** | Enterprise migration team or consultancy | Pre-built canonical models for SAP domains (FI, MM, SD, etc.) with validation rules, sample data, demo scripts | $2,000–$8,000 per pack | 2–8 weeks | 3+ comprehensive packs (currently 2 thin packs exist) | Speculative R&D without buyer commitment | **⚠️ Upsell only.** Sell assessment first, then upsell packs to accelerate model build. |
| 5 | **Open-source core + paid support** | Mid-market enterprise with internal data team | Annual support subscription: email/Slack support, bug prioritization, schema migration guidance | $5,000–$15,000/year | 3–6 months | 500+ stars, 10+ organic users, community, documented SLA | No community exists; selling support for unused tool is impossible | **❌ Not viable now.** Pre-requisite: organic adoption. Currently zero. |
| 6 | **Enterprise deployment** | Large enterprise (10,000+ employees, air-gapped) | On-premise install + annual support + custom validation rules + SLA | $30,000–$100,000/year | 6–12 months | UI, SSO, SOC 2, legal entity, insurance, reference customer | Enterprise buyers will not buy CLI-only Python package from unknown vendor | **❌ Not viable now.** Requires every enterprise prerequisite that does not exist. |
| 7 | **SaaS later** | Data governance team / migration team | Hosted team workspace with web UI, multi-tenant backend, billing | $50–$150/user/month | 3–6 months (after product exists) | Web UI, multi-tenancy, Stripe, SOC 2, SRE | 6–12 month engineering distraction from revenue; premature SaaS kills early-stage companies | **❌ Not now.** SaaS is a 2028 conversation. Fund from services revenue first. |

---

## 8. Product Gaps Blocking Commercial Use

| # | Gap | Commercial impact | Repo evidence | Fix type | Priority | Smallest next action |
|---|---|---|---|---|---|---|
| 1 | **Core repo 404 / inaccessible** | Zero adoption, zero credibility, zero stars/forks/contributors | `AGENT_5_WEBSITE_AUDIT.md` Section 16; homepage CTA links to dead URL | GTM | **P0** | Confirm repo visibility from non-authenticated session; fix permissions or update URL |
| 2 | **No real-world reference model** | Prospects see 86-object tutorial, not a credible project artifact | `examples/customer_bp_model/` — 86 objects covers ~10–15 real SAP fields (Agent 2) | Data model | **P0** | Create one 500-object reference model with real value mappings, decisions, issues, project context |
| 3 | **AI is stubbed (`NoProviderAdapter`)** | "AI-assisted" claim is marketing fiction; buyers will discover gap during pilot | `src/modelops_core/ai/provider_adapter.py` — deterministic keyword matching (Agent 6) | CLI / AI | **P0** | Integrate one real AI provider (OpenAI/Anthropic/Ollama) as default; remove "AI-assisted" from homepage until then |
| 4 | **Patch proposal validator under-tested (4 tests)** | Enterprises cannot trust AI safety gate; red team can bypass with `--force` | `tests/test_patch_proposal_validation.py` — 38 lines / 4 tests (Agent 5, Agent 6) | Validation | **P0** | Expand to 20+ tests: multi-op, broken refs, path traversal, expired proposals, long strings |
| 5 | **`before` field ignored during apply** | Hallucinated proposals misrepresent current state and still apply unconditionally | `src/modelops_core/patching/apply_service.py` lines 245–288 (Agent 5, Agent 6) | Validation | **P0** | Implement `before` field validation: reject operation if current state does not match |
| 6 | **CLI-only, no UI** | Excludes 90% of ICP; business users, data stewards, auditors cannot adopt | `README.md`: "No UI is included." `MVP_SCOPE.md` describes 8 UI screens that do not exist (Agent 5, Agent 6) | GTM / Packaging | **P0** | Build minimal read-only static HTML dashboard from SQLite index (`modelops docs-build` is basic — enhance it) |
| 7 | **SAP domain pack too thin (4 tables)** | Big 4 leads will dismiss it; no composite-key awareness | `src/modelops_core/domain_packs/sap.py` — only KNVV, KNB1, KNVP, BUT000 (Agent 2) | Data model | **P1** | Expand to 20+ tables: KNA1, KNVK, ADRC, ADR6, BUT020, BUT021, TVKOT, T077D, SKA1, SKB1, BSEG, BKPF |
| 8 | **No Excel-native import/export round-trip** | Consultants live in Excel; asking them to write Markdown is a tax on speed | `export-model --format xlsx` exists; `import-model-sheet` imports Google Sheets, not Excel (Agent 2) | CLI / Import | **P1** | Build `import-excel` command that reads styled XLSX export, generates PatchProposal with diffs |
| 9 | **No multi-source mapping or transformation logic** | Real migrations map 2–5 sources to one target with concatenation, lookups, conditionals | `examples/customer_bp_model/model/MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP.md` — single source, single target, no `transformation_rule` (Agent 2) | Data model | **P1** | Add `transformation_rule` or `TransformationLogic` object type; add `MappingSet` orchestration |
| 10 | **No load sequence / dependency / reconciliation objects** | Irrelevant to cutover planning — the most expensive phase | No `LoadStep`, `LoadDependency`, `ReconciliationRule` objects exist (Agent 2) | Data model | **P1** | Add `LoadStep`, `LoadDependency`, `ReconciliationRule` object types |
| 11 | **Documentation drift (AGENTS.md, SYSTEM_ARCHITECTURE.md, MVP_SCOPE.md)** | Signals immaturity; agents and evaluators make wrong edits | `AGENTS.md` wrong version (`0.1.0` vs `0.4.0`), wrong SAP rules path; `SYSTEM_ARCHITECTURE.md` references Next.js UI; `MVP_SCOPE.md` obsolete ID formats (Agent 5, Agent 6) | Docs | **P1** | Fix `AGENTS.md` (2-line change); remove UI fiction from `SYSTEM_ARCHITECTURE.md`; update `MVP_SCOPE.md` IDs |
| 12 | **Legacy CR service auto-applies on approval** | Importing wrong module collapses governance; hardcoded `approved_by: "system"` | `src/modelops_core/patching/change_request_service.py` (Agent 5, Agent 6) | Validation | **P1** | Add deprecation warnings; remove in 0.5.0; add test guarding against accidental import |
| 13 | **No fixture factories** | Tests are verbose; agents write repetitive boilerplate; slows contribution | `tests/conftest.py` — only 2 fixtures (`sample_repo`, `temp_model_dir`) (Agent 5) | Packaging | **P1** | Add factories for `FieldEndpoint`, `Mapping`, `PatchProposal`, `Decision`, `Issue` |
| 14 | **No blog, case studies, demo video, or email capture** | Zero content marketing; no funnel for non-developer decision-makers | Website has no `blog/`, no testimonials, no video, no newsletter form (Agent 5) | GTM | **P1** | Publish 3 blog posts (SAP migration war story, "Why we built this," AI governance opinion); add email signup |
| 15 | **Scorecard metrics are naive** | Shows "fail" for correct models; undermines trust with governance buyers | `src/modelops_core/reports/scorecard_service.py` — `lov_coverage` expects every FieldEndpoint to have ValueList; `mapping_logic_coverage` expects every Mapping to have ValueMapping (Agent 2) | Validation | **P2** | Make scorecard metrics context-aware: skip check-table fields, skip 1:1 mappings without value translation |

---

## 9. Positioning Audit

### Current Positioning Problem

The product is **too abstract, too technical, and too SAP-insider** for the actual budget holder. The homepage H1 — *"AI-assisted MDM model registry"* — contains three abstract nouns that mean nothing to a program director. The copy is witty and specific (`final_v9_really_final.xlsx`, `owner: ask Anna, unless she left`) but assumes the reader has sat in SAP migration meetings. A CIO who has never touched KNVV-KDGRP will glaze over in 10 seconds (Agent 6). The site has **zero discoverability** — no blog, no case studies, no demo video, no email capture — so the polished copy is a monologue in an empty room (Agent 5).

### Better Positioning Angle

**From:** "AI-assisted MDM model registry for migration, governance, and support teams."  
**To:** **"The field dictionary that survives when your consultant leaves."**

Lead with the **emotional pain** (knowledge loss, audit failure, go-live delay), not the category. Use business language, not architecture language. Drop "model registry" entirely — SAP consultants do not know what that means (Agent 2).

### Homepage Hero Rewrite

> **Before:** "Martenweave is the data-model brain between Excel chaos and AI help."
>
> **After:** "Your SAP migration knowledge is walking out the door. Martenweave catches it before it leaves."
>
> **Subhead:** "Replace scattered Excel mappings with a validated, audit-ready field dictionary that lives in Git. Every SAP field has an owner, a history, and a business meaning — so when your consultant leaves, the knowledge stays."
>
> **CTA:** "See a 2-minute demo" (video) + "Get the free CLI" (GitHub)

### 5 Sharper Taglines

1. "The field dictionary that survives team turnover."
2. "Audit-ready SAP mappings in Git, not email."
3. "Before you migrate to S/4HANA, know your data."
4. "Validated model truth for teams who are tired of `FINAL_v9.xlsx`."
5. "When the consultant who wrote the mapping leaves, Martenweave stays."

### 3 Bad Taglines to Avoid

1. **"AI-assisted MDM model registry"** — Three abstract nouns. Nobody knows what it means. (Agent 6)
2. **"Backend-first agentic data model registry"** — Internal architecture language, not buyer language. (Agent 5)
3. **"The data-model brain between Excel chaos and AI help"** — Metaphorical, vague, and sounds like every other AI startup. (Agent 5)

---

## 10. First Paid Offer

### Offer Name
**S/4HANA Migration Model Readiness Assessment**

### Target Buyer
Program director or CIO at a mid-market enterprise (500–5,000 employees) about to start or currently in an ECC→S/4HANA migration.

### Problem Solved
The team has field mappings scattered across Excel workbooks, SharePoint, and email. There is no single source of truth for what each SAP field means, who owns it, or why it was mapped this way. Audit risk is high, consultant turnover is imminent, and the AMS handover will be a documentation scramble.

### Inputs Required from Client
1. Existing Excel mapping workbooks (all versions, however messy)
2. SAP target table/field list for the migration scope
3. Legacy source system column names and sample data (CSV/XLSX, 100–10K rows)
4. Workshop decision notes, tickets, or validation reports (if any)
5. 2–3 hours of stakeholder interviews (migration lead, data architect, business owner)

### Deliverables
1. **Canonical Model** — Validated Martenweave repository with `Domain`, `Entity`, `Attribute`, `FieldEndpoint`, `Mapping`, `Decision`, and `Issue` objects for all in-scope fields
2. **Gap Report** — `modelops gaps` output showing unmodeled dataset columns, missing owners, and broken references
3. **Readiness Scorecard** — `modelops scorecard` output measuring ownership coverage, evidence coverage, validation rule coverage, and SAP context completeness
4. **Impact Analysis** — `modelops impact` reports for 5–10 high-risk fields (e.g., KNVV-KDGRP)
5. **Business-Review Excel Export** — Styled XLSX workbook with read-only columns and reviewer notes for non-technical stakeholders
6. **Recommendations Memo** — Prioritized list of model gaps, risks, and next steps

### Timeline
2–3 weeks (part-time engagement, remote)

### Price Hypothesis
$15,000–$25,000 fixed price. Benchmark: GSIs charge $30K–$100K for migration readiness assessments. A boutique offering at $20K is competitive.

### What Can Be Done Manually Now
A competent consultant can produce a similar output in Excel + Confluence in 3–5 days. The difference is: no validation, no referential integrity, no version control, no audit trail, no searchability, and no AI-assisted updates.

### What Martenweave Automates
- `modelops validate` catches broken references and SAP context violations in seconds instead of manual review
- `modelops gaps` compares dataset columns against the model automatically
- `modelops build-index` creates a searchable SQLite database + JSONL exports
- `modelops export-model --format xlsx --business-review` generates client-ready styled Excel
- `modelops impact` traces field dependencies up/downstream
- Git history provides automatic audit trail

### What Proof/Demo Is Needed
1. **2-minute video** showing `modelops validate`, `modelops impact FEP-S4-KNVV-KDGRP`, and `modelops export-model --format xlsx` on the `customer_bp_model` example
2. **Sanitized sample deliverables** — a gap report and scorecard from a fictional "Acme Corp" scenario
3. **One real pilot** (even at cost or free) to generate a testimonial and before/after metrics

### Why This Offer Leads Back to the Core Product
The assessment **creates** the canonical model. Once the model exists, the client has a choice: maintain it in Martenweave (free, open source) or let it rot in Excel again. The assessment demonstrates the value of the model layer. Follow-on revenue comes from:
- **Training workshops** ($10K–$20K) to teach the client's team to maintain the model
- **Domain packs** ($2K–$8K) to accelerate modeling of additional SAP modules
- **Team license** (future, $5K–$20K/yr) if a web UI is built for non-technical maintainers
- **Re-assessments** ($8K–$15K) at project milestones or post-go-live

---

## 11. 30-Day Commercial Validation Plan

### Week 1 — Sharpen Demo & Offer

- [ ] Fix core repo visibility (P0)
- [ ] Record 2-minute demo video: `modelops validate` → `modelops impact` → `modelops export-model --format xlsx`
- [ ] Write 1-page "S/4HANA Migration Model Readiness Assessment" service description with price ($15K–$25K)
- [ ] Create sanitized sample deliverables (gap report + scorecard from `customer_bp_model`)
- [ ] Update homepage hero to emotional pain angle (Section 9)
- [ ] Add email signup to website: "Get notified when the workbench launches"
- [ ] Publish first blog post: "The real cost of undocumented SAP field mappings"

### Week 2 — Build Proof Assets

- [ ] Expand `customer_bp_model` to 200+ objects (real value mappings, real decisions, real issues) OR create new "real-world reference model"
- [ ] Build Excel-native import/export round-trip prototype (even if manual)
- [ ] Create 5 demo scenarios (see below)
- [ ] Draft training deck: "Canonical Modeling for SAP Migrations" (1-day workshop)
- [ ] Post demo video to LinkedIn, Hacker News, r/SAP
- [ ] Reach out to 3 SAP consultancies for partnership conversations

### Week 3 — Interview & Outreach

- [ ] Conduct 5 customer discovery interviews with target buyers (see questions below)
- [ ] Send 10 personalized outreach emails to program directors at enterprises with known ECC→S/4HANA timelines
- [ ] Run 2 demo sessions with friendly prospects (consultancies or former colleagues)
- [ ] Document rejection signals and success signals (see below)
- [ ] Publish second blog post: "Why we built Martenweave: a migration horror story"
- [ ] Post to LinkedIn with demo video link

### Week 4 — Test Paid Pilot

- [ ] Close 1 paid pilot at $15K–$25K OR 1 free pilot with explicit agreement to publish sanitized case study
- [ ] Deliver assessment using existing CLI (no custom development)
- [ ] Measure: time to build model, number of validation errors caught, gap report findings, client satisfaction
- [ ] Write case study draft (even if internal-only for now)
- [ ] Decide: continue, pivot, or stop based on Go/No-Go criteria (Section 12)

### 20 Customer Discovery Questions

1. How do you currently document SAP field mappings during migration?
2. What happens when the consultant who wrote the mapping leaves?
3. Have you ever had an audit finding related to data mapping or lineage documentation?
4. How many versions of your mapping Excel workbook exist right now?
5. How long does it take a new consultant to understand your current mappings?
6. What tools do you use for mapping documentation? (Excel, Confluence, ALM, custom)
7. Have you ever discovered a mapping error during UAT or cutover?
8. What was the cost of that error in time, money, or delay?
9. Who owns the business meaning of a field like KNVV-KDGRP in your organization?
10. How do you track why a mapping decision was made?
11. What happens to mapping knowledge after go-live? Who maintains it?
12. Have you evaluated data catalog or governance tools (Collibra, Alation, etc.)?
13. Why did you adopt or reject them?
14. What would make you switch from Excel to another tool?
15. Who would maintain a new tool day-to-day?
16. What is your team's Git literacy?
17. How do you feel about AI-assisted documentation? What are your governance concerns?
18. What is your budget for migration documentation tools?
19. What trigger event would cause you to buy something this quarter?
20. If Martenweave were free and took 1 hour to set up, would you try it? Why or why not?

### 10 Outreach Target Profiles

1. Program director at a manufacturing company with known ECC→S/4HANA timeline (LinkedIn search: "SAP S/4HANA migration" + "program director")
2. Data workstream lead at a retail company (LinkedIn: "SAP migration" + "data lead")
3. Delivery director at a 50–200-person SAP consultancy (LinkedIn: "SAP consultancy" + "delivery director")
4. Migration architect at a pharmaceutical company (LinkedIn: "SAP S/4HANA" + "architect")
5. CIO at a mid-market enterprise with recent SAP ECC contract renewal (LinkedIn: "CIO" + "SAP ECC")
6. Data governance manager at a financial services firm (LinkedIn: "data governance" + "SAP")
7. AMS manager at a company that went live on S/4HANA in the last 12 months (LinkedIn: "SAP AMS" + "manager")
8. Independent SAP consultant with 500+ LinkedIn connections (LinkedIn: "SAP freelancer" + "migration")
9. Partner at a Big 4 firm responsible for SAP migration practice (LinkedIn: "SAP migration" + "partner" + "Deloitte/Accenture/KPMG/PwC")
10. Head of MDM at a company with recent SAP MDG implementation (LinkedIn: "MDM" + "SAP" + "head")

### 5 Demo Scenarios

1. **Audit Defense Demo** — Show `modelops validate` catching a broken reference and an SAP context violation. Emphasize: "This would have been an audit finding."
2. **Knowledge Survival Demo** — Show `modelops impact FEP-S4-KNVV-KDGRP` tracing upstream/downstream. Emphasize: "When the consultant leaves, this traceability stays."
3. **Gap Detection Demo** — Show `modelops gaps` flagging an unmodeled dataset column. Emphasize: "We caught this before UAT, not during cutover."
4. **Business Review Demo** — Show `modelops export-model --format xlsx --business-review` generating a styled Excel workbook. Emphasize: "Your business users still get Excel. The canonical source stays in Git."
5. **AI Governance Demo** — Show `modelops propose-patch --from note.md` generating a `PatchProposal`, then `modelops proposal validate` and `modelops proposal accept`. Emphasize: "AI proposes. Validators verify. Humans approve."

### 5 Rejection Signals

1. "We already pay for SAP and Excel." → Incumbent is too strong; pain is not visible.
2. "Our team doesn't use Git." → CLI/Git barrier is fatal for this prospect.
3. "This looks like a lot of manual work." → Setup burden exceeds perceived value.
4. "We already have Collibra/Informatica." → Competing against entrenched governance budget.
5. "Can you show me a customer like us?" → Zero social proof is a deal-killer.

### 5 Success Signals

1. "We just lost our lead architect and nobody knows why KNVV-KDGRP maps this way." → Trigger event is active.
2. "Our auditor asked for lineage documentation and we have none." → Panic purchase candidate.
3. "Can you do this for our Supplier/Vendor module too?" → Expansion intent.
4. "How do we get our consultants trained on this?" → Champion wants to embed in methodology.
5. "Can you deliver this as a service? We don't have time to build it ourselves." → Services-led path is open.

---

## 12. Go / No-Go Criteria

### Continue If...

- [ ] 1 paid assessment ($15K+) or 1 free pilot with signed case-study agreement is closed within 60 days
- [ ] 3+ customer discovery interviews confirm the pain is urgent and budgeted (indirectly)
- [ ] 1 SAP consultancy expresses interest in embedding Martenweave in their methodology
- [ ] Core repo is publicly accessible and receives 50+ stars within 90 days of visibility fix
- [ ] 2+ blog posts or LinkedIn posts generate 5+ inbound inquiries
- [ ] Demo video is watched 100+ times and generates 3+ "tell me more" responses

### Pivot If...

- [ ] 0 paid assessments closed after 90 days of active outreach, BUT 2+ consultancies want to use it internally for free
- [ ] All prospects say "great for technical teams, but our business users need a UI" → pivot to building minimal read-only UI before next sale
- [ ] All traction is non-SAP (e.g., Salesforce, dbt) → pivot to generic model registry positioning and deprioritize SAP domain packs
- [ ] Services revenue exceeds $50K but zero interest in self-serve CLI → embrace consulting accelerator model, defer productization
- [ ] AI integration proves to be the primary interest (not validation/governance) → pivot to "AI-ready model layer" positioning and build real provider integration

### Stop If...

- [ ] 0 paid or free pilots after 90 days of active outreach to 20+ qualified prospects
- [ ] Every prospect says "Excel is good enough" and cannot articulate a specific recent pain point
- [ ] Core repo remains 404 or inaccessible after 30 days
- [ ] 0 inbound interest after 5+ blog posts and active LinkedIn/HN presence
- [ ] Safety gaps (patch validator, `before` field, bypass flags) are not fixed after 60 days — enterprise pilots become too risky
- [ ] Team cannot commit 10+ hours/week to commercial validation alongside product development

---

## 13. Recommended GitHub Issues

**Note:** These are issue *drafts* for planning purposes. Do not create actual issues until the team agrees on prioritization.

### Repo: `metalhatscats/martenweave-core`

| # | Title | Goal | Scope | Acceptance Criteria | Validation Command |
|---|---|---|---|---|---|
| 1 | Fix core repo visibility (404 on public fetch) | Ensure prospects can evaluate, adopt, and contribute | Repository settings, homepage CTA URL | `curl -I https://github.com/metalhatscats/martenweave-core` returns 200 from non-authenticated session | `curl -I https://github.com/metalhatscats/martenweave-core` |
| 2 | Fix AGENTS.md version string and SAP rules path | Remove doc drift that causes wrong edits | `AGENTS.md` lines referencing version and `_SAP_CONTEXT_RULES` | Version reads `0.4.0`; SAP rules path points to `src/modelops_core/domain_packs/sap.py` | `grep -n "0.1.0" AGENTS.md` returns nothing; `grep -n "domain_packs/sap.py" AGENTS.md` returns match |
| 3 | Fix API hardcoded version | Align API version with package version | `src/modelops_core/api/app.py:22` | `version` uses `__version__` import instead of hardcoded `"0.1.0"` | `grep -n "version=" src/modelops_core/api/app.py` |
| 4 | Expand patch proposal validation tests from 4 to 20+ | Make the AI safety gate enterprise-trustworthy | `tests/test_patch_proposal_validation.py` | Covers: multi-op proposals, non-existent target objects, path traversal, expired proposals, extremely long strings, null bytes in IDs, SAP context violations at proposal level | `pytest tests/test_patch_proposal_validation.py --cov` shows ≥20 tests and ≥80% coverage of `patching/patch_validator.py` |
| 5 | Implement `before` field validation during apply | Prevent hallucinated proposals from applying unconditionally | `src/modelops_core/patching/apply_service.py` | Apply rejects operation if current frontmatter state does not match `op.before`; test covers mismatch case | `pytest tests/test_patch_apply.py -k before` passes |
| 6 | Deprecate legacy `patching/change_request_service.py` | Prevent accidental governance collapse | `src/modelops_core/patching/change_request_service.py` | Module emits `DeprecationWarning` on import; removed in 0.5.0 milestone; test guards against accidental import | `pytest tests/ -k legacy` passes; `python -c "import modelops_core.patching.change_request_service"` shows warning |
| 7 | Add real AI provider integration (OpenAI/Anthropic/Ollama) | Replace `NoProviderAdapter` keyword matching with LLM reasoning | `src/modelops_core/ai/` | `KimiAdapter` or new `OpenAIAdapter` is default when env var is set; produces contextual proposals from natural language notes; tests cover prompt formatting and response parsing | `pytest tests/test_ai_patch_proposal_service.py` passes |
| 8 | Build minimal read-only web UI from SQLite index | Remove biggest adoption barrier for non-technical users | New `src/modelops_core/web_ui/` or enhance `docs-build` | Static HTML dashboard shows object list, search, impact graph, gap report; generated by `modelops docs-build --serve` | `modelops docs-build --serve --repo ./customer_bp_model` serves browsable UI at `http://localhost:8000` |
| 9 | Expand SAP domain pack from 4 to 20+ tables | Make the SAP context feel authoritative | `src/modelops_core/domain_packs/sap.py` | Adds KNA1, KNVK, ADRC, ADR6, BUT020, BUT021, TVKOT, T077D, SKA1, SKB1, BSEG, BKPF; composite-key awareness for KNVV (KUNNR+VKORG+VTWEG+SPART) | `pytest tests/test_sap_context_validation.py` passes with new rules |
| 10 | Create 500-object real-world reference model | Replace tutorial with credible project artifact | New `examples/real_world_bp_model/` or expand `customer_bp_model` | 500+ objects, 50+ real SAP fields, real value mappings (20–200 legacy→target), real decisions with alternatives and risks, real issues (50+), project context (waves, company codes, go-live dates), load dependencies | `modelops validate --repo ./examples/real_world_bp_model` returns zero errors; `modelops build-index` succeeds |
| 11 | Add Excel-native import/export round-trip | Meet consultants where they are | `src/modelops_core/imports/` and `src/modelops_core/exports/` | `import-excel` command reads styled XLSX export, generates PatchProposal with diffs; business users edit Excel, technical user imports back | `modelops import-excel --from review.xlsx --repo ./my-model` generates valid PatchProposal; `pytest tests/test_import_excel.py` passes |
| 12 | Add transformation logic to Mappings | Support real-world 1:N, conditional, and lookup mappings | `src/modelops_core/schemas/` | New `transformation_rule` field on `Mapping` or new `TransformationLogic` object type; validated in Layer 1–3 | `pytest tests/test_schema_validation.py -k transformation` passes |
| 13 | Add load sequence and dependency objects | Make Martenweave relevant to cutover planning | `src/modelops_core/schemas/common.py`, `src/modelops_core/schemas/registry.py` | New `LoadStep`, `LoadDependency`, `ReconciliationRule` object types; validated in pipeline | `pytest tests/test_schema_validation.py -k load` passes |
| 14 | Add fixture factories to conftest.py | Reduce test boilerplate and agent confusion | `tests/conftest.py` | Factories for `FieldEndpoint`, `Mapping`, `PatchProposal`, `Decision`, `Issue`, `ChangeRequest`; used in 5+ existing tests | `pytest tests/ --cov` shows reduced test line count; `grep -n "def factory_" tests/conftest.py` shows ≥5 factories |
| 15 | Split CLI monolith into commands package | Reduce maintainability risk | `src/modelops_core/cli.py` → `src/modelops_core/commands/` | Pure move refactor; all 38 commands still work; no behavior changes; `pytest tests/test_cli_contracts.py` passes without modification | `pytest tests/test_cli_contracts.py` passes; `ls src/modelops_core/commands/` shows ≥5 submodules |
| 16 | Remove UI fiction from SYSTEM_ARCHITECTURE.md | Align docs with reality | `docs/architecture/SYSTEM_ARCHITECTURE.md` | No mention of Next.js UI as part of MVP; architecture diagram shows canonical file → validation → index → query flow | `grep -n "Next.js" docs/architecture/SYSTEM_ARCHITECTURE.md` returns nothing |
| 17 | Update MVP_SCOPE.md to current ID format and remove UI screens | Align scope doc with shipped product | `docs/product/MVP_SCOPE.md` | IDs use kebab-case uppercase (`ATTR-CUST-SALES-CUSTOMER-GROUP`); UI screens sections 11.1–11.8 marked as "deferred" or removed | `grep -n "attr.customer.sales_area" docs/product/MVP_SCOPE.md` returns nothing |
| 18 | Add rollback test for multi-op partial failure | Prove atomicity promise | `tests/test_patch_apply.py` | Test creates multi-op proposal where op 2 fails after op 1 writes; verify all changes are rolled back and index is consistent | `pytest tests/test_patch_apply.py -k rollback` passes |
| 19 | Add semantic validation for PatchProposal operations | Validate object existence, type registration, path traversal before apply | `src/modelops_core/validation/pipeline.py` or new proposal validator | Proposal operations are validated against Layer 1–3 rules before apply; test covers invalid type, broken ref, path traversal | `pytest tests/test_patch_proposal_validation.py -k semantic` passes |
| 20 | Add ValueList entry code-uniqueness validation | Prevent duplicate codes in value lists | `src/modelops_core/validation/pipeline.py` | Validation warns if `ValueList` contains duplicate `code` values; test covers duplicate and unique cases | `pytest tests/test_schema_validation.py -k valuelist` passes |
| 21 | Add co-occurrence rule for `sap_table` + `sap_field` | Enforce SAP field endpoint completeness | `src/modelops_core/domain_packs/sap.py` | `FieldEndpoint` with `endpoint_type: sap_table_field` must have both `sap_table` and `sap_field`; validation error if missing | `pytest tests/test_sap_context_validation.py -k cooccurrence` passes |
| 22 | Expand TESTING_STRATEGY.md from stub to ≥100 lines | Guide contributors and agents | `docs/developer/TESTING_STRATEGY.md` | Covers coverage targets, mocking policy, fixture guidelines, contract test policy, e2e test policy, CI expectations | `wc -l docs/developer/TESTING_STRATEGY.md` shows ≥100 lines |
| 23 | Add architecture diagram to SYSTEM_ARCHITECTURE.md | Help evaluators understand the system in 30 seconds | `docs/architecture/SYSTEM_ARCHITECTURE.md` | Diagram (Mermaid or embedded image) shows: canonical files → parser → validation (L1–L3) → SQLite index → query/impact/gap services | Visual inspection of rendered markdown |
| 24 | Group CLI commands with Typer `rich_help_panel` categories | Improve usability of 38-command monolith | `src/modelops_core/cli.py` | Commands grouped into: Repository, Validation, Index, Analysis, Patching, Export, Import, Admin; `--help` shows categories | `modelops --help` shows grouped panels |
| 25 | Add `--force` / `--skip-risk-check` env-var gate | Prevent accidental governance bypass | `src/modelops_core/cli.py`, `src/modelops_core/patching/` | `--force` and `--skip-risk-check` require `MARTENWEAVE_ALLOW_FORCE=1` env var; without it, flags print warning and exit | `modelops proposal apply --force` without env var exits with error; with env var succeeds |

### Repo: `Martenweave/martenweave.github.io`

| # | Title | Goal | Scope | Acceptance Criteria | Validation Command |
|---|---|---|---|---|---|
| 26 | Add 2-minute demo video to homepage | Lower barrier to "aha moment" | `index.html` hero section | Video embed (YouTube/Loom) showing `modelops validate`, `modelops impact`, `modelops export-model`; plays inline or opens modal; mobile-responsive | Visual inspection on desktop and mobile |
| 27 | Add email signup / "notify me" form | Capture interest from non-developer decision-makers | `index.html` or new page | Form captures email + role (program director, architect, consultant, etc.); data stored in simple backend (e.g., Formspree, Buttondown) or GitHub issue; privacy policy linked | Submit test email; verify receipt |
| 28 | Publish 3 blog posts | Generate inbound traffic and SEO | New `blog/` or `posts/` directory | Posts: (1) SAP migration war story, (2) "Why we built Martenweave," (3) AI governance opinion; each ≥800 words; linked from homepage and docs | `ls blog/` shows 3 `.md` files; sitemap updated |
| 29 | Add "vs." comparison page | Help evaluators understand differentiation | New `docs/vs.html` or `docs/comparisons.md` | Compares Martenweave to: Excel, Confluence, Collibra/DataHub, SAP MDG, ChatGPT; honest about where Martenweave loses | Visual inspection; copy checked by site validator |
| 30 | Add case study / pilot partner page | Provide social proof without faking testimonials | New `docs/case-studies.html` or section on homepage | One sanitized case study (even from internal pilot) with: company type, migration scope, fields modeled, time saved, quote from migration lead; explicit "pilot partner" language | Visual inspection; no fake customer names |
| 31 | Add "Get started in 5 minutes" quickstart on homepage | Reduce installation friction | `index.html` | One-liner install (`pip install martenweave-core`), 3 copy-paste commands (`modelops init`, `modelops validate`, `modelops impact`), link to `docs/first-15-minutes.md` | Copy-paste commands work in fresh venv |
| 32 | Add GitHub stars/forks badge once repo is public | Provide trust signal | `index.html` and core `README.md` | Badge shows live star count from `shields.io` or GitHub API; updates automatically | Visual inspection after repo is public |
| 33 | Fix site.webmanifest icon sizes | Remove non-standard PWA metadata | `site.webmanifest` | Icon sizes are 192x192 and 512x512; logo PNG resized or additional icons created | `cat site.webmanifest` shows standard sizes |
| 34 | Add Schema.org FAQ structured data | Improve SEO for "Why not just..." section | `index.html` | JSON-LD `FAQPage` schema with 4–6 questions (Excel, Confluence, ChatGPT, MDG) and answers; validated by Google's Rich Results Test | Copy JSON-LD into Google Rich Results Test; passes |

---

## Final Summary Block

### 1. Brutal Verdict

Martenweave is a **technically competent, commercially stranded** consulting accelerator with product ambitions. The pain it solves is real and quantified, the code works, and the website copy is excellent — but there is **zero evidence anyone is using it, zero public repo access, zero community, and no UI**. Do not treat this as a sellable software product today. Treat it as a **methodology + services business** that uses open-source code as a delivery vehicle. The window to validate is the 2027 SAP ECC deadline, which is finite and shrinking.

### 2. Best First Paid Offer

**S/4HANA Migration Model Readiness Assessment** — $15,000–$25,000 fixed-price, 2–3 week engagement. Deliverables: validated canonical model, gap report, readiness scorecard, impact analysis, business-review Excel export, and recommendations memo. This is the fastest path to first dollar because it requires no UI, no SaaS, no security certs — just the existing CLI and consultant expertise.

### 3. Best First ICP

**Boutique SAP System Integrator** (20–200 people). The delivery director buys methodology investments that differentiate their firm from Big 4 and create client deliverables. Consultants are technical enough to use a CLI, and the SI can embed Martenweave into billable projects. This is both a customer and a distribution channel.

### 4. Top 5 Repo Changes

1. **Fix core repo visibility** (P0) — A 404 repo is commercial death.
2. **Expand patch proposal validation tests** from 4 to 20+ and implement `before` field validation (P0) — Enterprises cannot trust AI safety with 4 tests.
3. **Integrate a real AI provider** (OpenAI/Anthropic/Ollama) and remove "AI-assisted" from homepage until it works (P0) — Current `NoProviderAdapter` is keyword matching, not AI.
4. **Build a 500-object real-world reference model** with real value mappings, decisions, and issues (P0) — The 86-object example is a tutorial, not a reference implementation.
5. **Build minimal read-only web UI** from SQLite index (P0) — CLI-only excludes 90% of the ICP.

### 5. Top 5 Positioning Changes

1. **Drop "model registry"** from all buyer-facing materials. Use "migration mapping documentation," "field dictionary," or "master data governance layer."
2. **Rewrite homepage hero** to emotional pain: "Your SAP migration knowledge is walking out the door. Martenweave catches it before it leaves."
3. **Add a 2-minute demo video** to the homepage — the barrier to "aha moment" is too high without it.
4. **Add an email signup** — capture interest from decision-makers who are not ready to clone a repo.
5. **Publish 3 blog posts immediately** — SAP migration war story, "Why we built this," and AI governance opinion. Zero search presence is a credibility gap.

### 6. Is This Worth Another 90 Days of Work?

**Yes — but only if the work is commercial validation, not product engineering.** The next 90 days should be spent selling the Migration Readiness Assessment, running 3–5 customer discovery interviews per week, fixing the repo visibility, and publishing content. **Do not** build a UI, do not build SaaS, do not chase enterprise features. If the team cannot commit 10+ hours/week to outreach and sales, or if 0 pilots close after 90 days, **stop** and treat Martenweave as a personal open-source project, not a business.

---

*Report synthesized from 7 agent analyses. All claims cite specific source files or agent findings. No traction, revenue, partnerships, or SAP certification has been invented.*

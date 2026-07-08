# Commercial Due Diligence — Agent Notes Summary

**Synthesis Lead:** Agent 7  
**Date:** 2026-06-09  
**Product:** martenweave-core v0.4.0  
**Purpose:** Condensed reference of key findings from all 7 source agents for quick lookup during decision-making.

---

## Agent 1 — Product/Market Analysis

**Analyst:** Product/Market Analyst  
**File:** `AGENT_1_PRODUCT_MARKET.md`

### Core Findings
- **Pain is real and quantified:** SAP migration rework costs $250K–$750K per project; 82% overrun; 59–65% exceed schedule. Data preparation causes 32% of delays.
- **Market is large:** $15–25B annual SAP S/4HANA migration services market; ~21,000 ECC customers still facing migration before 2030.
- **No existing line item** for "model registry software" in migration budgets. Martenweave must create a new category or displace Excel.
- **Best ICP ranking:** (1) System Integrator, (2) SAP Migration Team Lead, (3) SAP MDM/MDG Team Lead.
- **Not a product yet:** No UI, no SaaS, no billing, no support infrastructure. Best positioned as **consulting accelerator**.
- **Path to product:** 18–36 months. Requires organic CLI adoption → services revenue → web UI → team license → enterprise edition.
- **Verdict:** High-quality solution to validated problem, launched into large market, but **without proven product-market fit or viable distribution**.

### Key Quotes
> "The most honest description is: a consulting accelerator with product ambitions."
> "Do not invest in scaling until the first 5–10 paid pilots are complete and the repo is public."

---

## Agent 2 — SAP/MDM Domain Buyer Analysis

**Analyst:** SAP/MDM Buyer Analyst (3+ S/4HANA migrations experience)  
**File:** `AGENT_2_SAP_BUYER.md`

### Core Findings
- **SAP domain pack too thin:** Only 4 tables (KNVV, KNB1, KNVP, BUT000), no composite keys, no S/4 vs ECC distinction.
- **Examples feel like tutorials, not real projects:** 86 objects covers ~10–15 real SAP fields. A Deloitte lead would laugh at this. Needs 500+ object reference model.
- **CLI-only is a massive barrier:** SAP functional consultants do not use Git or CLI. Business users will not touch Markdown files.
- **"Model registry" is wrong language:** SAP consultants would call it "field mapping tracker," "data model wiki," or "the thing that replaces our Excel sheets."
- **Best wedge:** BP/Customer/Vendor model documentation (Rank #1). Migration field mapping control (Rank #2). Dataset gap detection (Rank #3 — weak standalone).
- **Workflow fit:** Fits design/blueprint phase; does NOT fit execution/cutover phase. No load sequence, no reconciliation, no ETL execution.
- **Maintainer problem:** Migration consultants bill by the hour — documentation is overhead. Data stewards might maintain if technical enough. Business users will not.
- **Score:** 5.1/10 — Promising foundation, not yet a sellable SAP product.

### Key Quotes
> "The abstraction is correct for governance, but it is a tax on speed during a migration sprint."
> "Drop 'model registry' from all buyer-facing materials."
> "A real-world reference model is a content project, not a code project."

---

## Agent 3 — Competitive / Alternative Analysis

**Analyst:** Competitive/Alternative Analyst  
**File:** `AGENT_3_COMPETITIVE.md`

### Core Findings
- **New sub-category:** "Agentic model knowledge registry" or "canonical data model operating system." Does not fit cleanly into data catalog, MDM, or model registry categories.
- **Excel wins on accessibility; Martenweave wins on correctness/traceability.** Switch only happens when pain from broken references, audit failures, or rework is acute.
- **SAP MDG is 10 years ahead** in direct SAP integration, real-time data quality, enterprise workflows, and certification. Martenweave is complementary (design-time docs) not competitive (runtime governance).
- **Data catalogs (Collibra, Alation, etc.) are 10+ years ahead** in connectors, UI, scale. 75%+ of organizations have NOT fully deployed a catalog. Martenweave is a **pre-catalog, migration-specific, SAP-aware semantic layer**.
- **dbt analogy partially works** — both are git-native, CLI, validation-first — but dbt transforms data; Martenweave documents meaning.
- **RAG/ChatGPT is a consumption interface, not a system of record.** Martenweave should feed RAG, not replace it. Deterministic validation is the differentiator.
- **Wedge strategy:** "Pre-go-live model documentation for SAP migrations" — mid-market S/4HANA projects (€5M–€50M) that cannot justify €200K MDG licenses.

### Key Quotes
> "Martenweave is not a data catalog replacement. It is a pre-catalog, migration-specific, SAP-aware semantic layer that can feed into a catalog later."
> "Martenweave borrows the developer experience of dbt but applies it to a completely different layer of the stack."

---

## Agent 4 — GTM / Pricing Analysis

**Analyst:** GTM/Pricing Analyst  
**File:** `AGENT_4_GTM_PRICING.md`

### Core Findings
- **10 monetization paths evaluated.** Fastest to first dollar: **Path 4 — Paid Migration Readiness Assessment** ($15K–$25K, 1–3 months).
- **Most realistic path:** Hybrid services-first: assessments + audits (months 1–3), training/workshops (months 2–6), domain packs + consulting accelerator partnerships (months 3–9), team license test (months 6–12), SaaS only if $200K+ ARR proven (months 12–24).
- **SaaS is a 2028 conversation, not 2026.** Building SaaS now would be a 6–12 month engineering distraction that kills early-stage revenue.
- **2027 ECC deadline is the single greatest commercial opportunity.** Anchor all messaging to it.
- **First dollar target:** $15,000 assessment within 60 days. 12-month target: $100K–$150K from assessments + training + domain packs.
- **Training is viable lead gen:** $800–$1,500/person, fast to test, validates demand.
- **Paid domain packs are upsell-only:** Currently 2 thin packs exist. Build comprehensive FI/MM/SD packs only after assessment revenue funds the work.
- **Open-source core + paid support is NOT viable now:** Requires 500+ stars, 10+ organic users, community. Currently zero.

### Key Quotes
> "The path to revenue is not through product-led growth or SaaS — those require a UI, community, and capital that do not exist."
> "SaaS is a 2028 conversation, not a 2026 conversation."
> "First dollar target: $15,000 assessment within 60 days."

---

## Agent 5 — Technical/Product Maturity Audit

**Analyst:** Read-only codebase exploration specialist  
**File:** `AGENT_5_TECHNICAL_AUDIT.md`

### Core Findings
- **Beta-grade, feature-rich:** ~1,200 tests, ~88% coverage, 4 example models, 30+ CLI commands, MCP server, API server, SQLite index, gap detection, impact analysis, approval-gated patches.
- **#1 maintainability risk:** `cli.py` is 5,343 lines, 38 commands + 22 subcommands. No per-command unit tests.
- **Critical safety gaps:** Patch proposal validator has only **4 tests / 38 lines**. `before` field ignored during apply. `--force` and `--skip-risk-check` exist at every layer. Legacy CR service auto-applies on approval with hardcoded `approved_by: "system"`.
- **AI is stubbed:** `NoProviderAdapter` generates deterministic scaffolds; real AI requires manual env configuration.
- **Documentation drift is real:** `AGENTS.md` wrong version (`0.1.0` vs `0.4.0`), wrong SAP rules path. `SYSTEM_ARCHITECTURE.md` references non-existent Next.js UI. `MVP_SCOPE.md` describes 8 UI screens that do not exist. `docs/change-workflow.md` references stale commands.
- **Dead files:** `schemas/mapping.py` and `schemas/validation_rule.py` (0% coverage, no imports). Legacy `patching/change_request_service.py` confuses agents.
- **API version hardcoded:** `src/modelops_core/api/app.py:22` says `version="0.1.0"` instead of using `__version__`.
- **No fixture factories:** `conftest.py` has only 2 fixtures.
- **Validation engine is strong:** Layer 1–3 + domain packs + circular reference detection. Gaps: cardinality enforcement, min-reference rules, proposal-level semantic validation.

### Key Quotes
> "Feature-rich and demo-ready, but needs cleanup before scaling to more domain packs, heavier agent workloads, or production use."
> "The patch proposal validator is the weakest safety path."
> "Documentation UI fiction misaligns team and agent expectations."

---

## Agent 5 — Website/Public Presence Audit

**Analyst:** Positioning and Public Presence Analyst  
**File:** `AGENT_5_WEBSITE_AUDIT.md`

### Core Findings
- **Overall grade: B+ for quality, F for reach.** Polished, professional, distinctive design — but zero discoverability.
- **Zero web presence:** No Google results for "Martenweave" + SAP/MDM/migration. No Reddit, HN, LinkedIn, Twitter, or SAP Community mentions.
- **Core repo 404:** `metalhatscats/martenweave-core` returns HTTP 404 via public fetch. Homepage CTA links to dead URL.
- **No demo path:** No video, no sandbox, no screenshots, no interactive demo, no "Try it online." Terminal panel on homepage is static HTML.
- **No content marketing:** No blog, no case studies, no technical deep-dives, no founder story.
- **Weak CTAs:** All CTAs are "go to GitHub" or "read more." No email capture, no "notify me when UI launches," no consulting/services CTA.
- **Exceptional copy:** Specific, witty, honest, memorable (`final_v9_really_final.xlsx`, `owner: ask Anna, unless she left`). Best open-source project copy seen.
- **AI governance leadership:** `ai.json`, `llms.txt`, and explicit safety rules are best-in-class. Site validator enforces messaging consistency — rare rigor for a static site.
- **No competitive comparisons to actual MDM/registry competitors:** Missing vs. Collibra, DataHub, SAP MDG, etc.
- **Safe content rules are admirable:** Explicitly prohibits fake testimonials, SAP certification claims, partnership claims.

### Key Quotes
> "The website is better than the product's current market position deserves."
> "The site is a beautiful monologue in an empty room."
> "A visitor who sees this polished site and then searches for 'Martenweave' will find nothing."

---

## Agent 6 — Red Team Skeptic Attack

**Analyst:** Red Team Skeptic (evidence-based attack, no praise)  
**File:** `AGENT_6_RED_TEAM.md`

### Core Findings
- **18 criticisms identified.** Severity: 7 Critical, 8 High, 2 Medium.
- **Critical severity:** Too abstract, too technical, no urgent budget, too close to consulting, existing tools good enough, no monetization path, no community/traction, core repo inaccessible, safety gaps.
- **"Model registry" is too abstract:** Requires 6 "is not" clarifications. If the product needs to disambiguate aggressively for machines, human buyers are even more lost.
- **CLI-only excludes 90% of ICP:** `MVP_SCOPE.md` describes 8 UI screens that do not exist. Product fiction is so strong that internal docs hallucinate a UI.
- **Wrong buyer:** Champion (data architect) has no budget; budget owner (program director) does not feel daily pain. Panic buyers buy SAP-certified solutions, not Python CLI tools.
- **No urgent budget:** "Scattered model knowledge" is not a budgeted problem. There is no line item for "model registry software."
- **Too close to consulting:** Services revenue does not scale. Pilot package requires a "Martenweave facilitator" — that is a consultant, not a product.
- **SAP-specific = market limit:** No second domain pack, no non-SAP example with real validation. SAP migration is a finite, time-bound market.
- **Too much manual setup:** 85 Markdown files for ~10–15 fields. Consultants bill by the hour — they have no incentive to automate themselves out of revenue.
- **AI angle is weak/overclaimed:** `NoProviderAdapter` is `if "CUSTOMER GROUP" in note.upper()`. Patch validator has 4 tests. `before` field ignored. `--force` bypasses all gates.
- **Documentation drift signals immaturity:** Wrong versions, UI fiction, stale commands, 27-line testing strategy stub.
- **Final verdict:** Technically sound, commercially doomed unless 3 things happen immediately: (1) fix repo visibility and community presence, (2) build a UI or embrace consulting, (3) prove non-SAP viability or accept the niche.

### Key Quotes
> "This is a consulting scaffold dressed as open-source infrastructure."
> "The team has built a beautiful answer to a question nobody is asking loudly enough to pay for."
> "Building is not selling, and open-sourcing is not monetizing."

---

## Cross-Agent Consensus

| Topic | Consensus |
|---|---|
| **Pain reality** | **REAL.** All 7 agents agree. SAP migration mapping chaos is extensively documented and quantified. |
| **Product maturity** | **BETA, not production.** Works in demo, has critical safety gaps, needs cleanup. |
| **Commercial readiness** | **NOT READY.** Zero traction, zero customers, zero public repo access, no UI. |
| **Best near-term path** | **SERVICES-LED.** Paid assessments ($15K–$25K) and consulting accelerator partnerships. |
| **Best ICP** | **Boutique SAP System Integrator** (distribution + customer) or **mid-market migration program director** (direct). |
| **Best wedge** | **Migration field mapping documentation & audit defense** — replacing Excel workbooks with validated canonical models. |
| **Biggest blocker** | **CLI-only + no UI** excludes 90% of buyers and users. |
| **Second biggest blocker** | **Zero public presence / repo 404** — invisible to prospects, contributors, and evaluators. |
| **AI claim** | **OVERSTATED.** Stubbed by default; safety gate under-tested. Remove "AI-assisted" from homepage until real provider is default. |
| **SaaS timeline** | **2028 at earliest.** Do not build UI/SaaS until services revenue proves demand. |
| **90-day recommendation** | **SELL, don't BUILD.** Run 3–5 customer discovery interviews per week. Close 1 paid assessment. Fix repo visibility. Publish 3 blog posts. |

---

*Condensed reference for quick lookup. For full analysis, reasoning, and evidence, see the individual agent files and the synthesis report.*

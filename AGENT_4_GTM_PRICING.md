# Agent 4 — GTM / Pricing Analysis
# Martenweave Commercial Due Diligence

**Date:** 2026-06-09
**Product Version:** 0.4.0
**Status:** MIT License, Zero Revenue, Zero Customers, No UI

---

## Executive Summary

Martenweave is a backend-first, CLI-driven agentic data model registry. It is technically solid (~1,200 tests, 88% coverage, 30+ CLI commands, MCP server, API server) but commercially nascent. There is no UI, no SaaS, no real AI provider integration (stubbed `NoProviderAdapter`), no customers, no testimonials, and no web presence.

**The fastest path to first revenue is consulting-led services sold to SAP migration teams.** The highest-value long-term path is a team license with domain packs. SaaS is not viable before a UI and multi-tenant architecture exist.

---

## Current Product State (What Actually Exists)

| Dimension | Reality |
|-----------|---------|
| License | MIT (open source, no restrictions) |
| Distribution | `pip install martenweave-core` |
| Interface | CLI only (`modelops` command) |
| Examples | 4 working models (Customer BP, Supplier/Vendor, Simple Product, Generic Product) |
| Tests | ~1,200 tests, 88% coverage |
| AI Integration | Stubbed (`NoProviderAdapter`); patch proposal framework exists but needs real provider |
| UI | None. Zero. Not even a basic web dashboard. |
| SaaS | None. Local-first architecture. |
| Customers | None. |
| Testimonials | None. |
| Website | Exists but zero content/SEO presence. |
| GitHub | Core repo may not be publicly accessible. |

**Critical Gap:** The product is a library/CLI tool, not a product a business user can adopt without a technical implementer. This shapes every commercial path.

---

## Path 1: Open-Source Core + Paid Support/Services

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | Mid-market enterprise with an internal data engineering team that adopted Martenweave but hit a wall on custom validation rules, schema migration, or MCP integration. |
| **Offer** | Annual support subscription: email/Slack support, bug prioritization, schema migration guidance, quarterly check-ins. NOT "we fix your model for you" — that's consulting. |
| **Price Hypothesis** | $5,000–$15,000/year per organization. Benchmark: small-tool OSS support (e.g., OneStop Gateway Silver tier ~$4,585/yr for 9 users). Cannot charge Red Hat prices ($500+/vCPU/yr) without enterprise credibility. |
| **Sales Motion** | Inbound via GitHub issues / docs. Requires discoverability. |
| **Proof Needed** | 1. Public GitHub repo with 500+ stars. 2. Active community asking questions. 3. Documented SLA. 4. At least 10 organic adoptions. 5. Real website with docs. |
| **Risk** | No community exists. Selling support for a tool nobody uses is impossible. Support revenue is low-margin and scales linearly with headcount. |
| **Time to First Revenue** | 12–18 months (after building community). |
| **Verdict** | ❌ **Not viable now.** Pre-requisite: organic adoption and community. Currently zero. |

---

## Path 2: Consulting Accelerator

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | SAP consultancy (boutique or mid-tier) that wants to deliver migration/MDM projects faster and with better documentation handover. |
| **Offer** | "Martenweave-enabled delivery": the consultancy uses Martenweave internally to model client data, generate gap reports, and produce AMS handover docs. Client pays for the migration project, not the tool. Tool is free (MIT). |
| **Price Hypothesis** | Project markup of 15–25% for "model-driven delivery." Example: $200K migration project → $30K–$50K premium for traceable model docs, gap analysis, and AI-assisted patch workflow. |
| **Sales Motion** | Direct outreach to SAP consultancies. Pilot with 1–2 friendly firms. Case study from pilot. |
| **Proof Needed** | 1. A consultancy actually using it on a live project. 2. A case study showing time saved or defects caught. 3. Training deck for consultants. 4. White-labelable output (client-ready reports). |
| **Risk** | Consultancies may adopt the free tool without paying for anything. Need to tie revenue to services (training, custom domain packs, priority support) that the consultancy buys from Martenweave, not the client. |
| **Time to First Revenue** | 2–4 months (if a consultancy partner is identified today). |
| **Verdict** | ⚠️ **Viable but indirect.** Revenue comes from services sold to the consultancy, not the end client. Requires a partner willing to co-sell. |

---

## Path 3: Team License (Per-Seat or Per-Project)

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | Data governance team or migration team inside a mid-market enterprise (500–5,000 employees) that wants a lightweight alternative to Collibra/Alation. |
| **Offer** | Annual license for the core + domain packs + updates. Per-seat or flat per-project. Includes support. |
| **Price Hypothesis** | $5,000–$20,000/year per team. Benchmark: Atlan starts at ~$30K/yr for mid-market. Martenweave is CLI-only, so must be 50–70% cheaper than Atlan. A 10-seat team at $150/seat/month = $18,000/yr. |
| **Sales Motion** | Outbound to data governance leaders. Content marketing ("lightweight data governance for SAP teams"). |
| **Proof Needed** | 1. A UI. CLI-only team licenses are nearly unsellable to enterprise buyers. 2. At least one reference customer. 3. Security/compliance documentation (SOC 2, GDPR). 4. Clear pricing page. |
| **Risk** | Without a UI, enterprise procurement will reject it. Buyers expect a web interface for $10K+/yr. CLI tools are sold to engineers, not governance teams. |
| **Time to First Revenue** | 6–12 months (if UI is built). Otherwise: never. |
| **Verdict** | ❌ **Not viable without UI.** The buyer persona (data governance team) will not adopt a CLI-only tool at this price point. |

---

## Path 4: Paid Migration Readiness Assessment

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | Enterprise about to start S/4HANA migration. CIO or migration program manager. |
| **Offer** | Fixed-price engagement: "We audit your Excel mappings, legacy data dictionaries, and ticket history; we build a canonical Martenweave model; we deliver a gap report and a readiness scorecard." |
| **Price Hypothesis** | $15,000–$50,000 per assessment. Benchmark: SAP migration readiness assessments from GSIs cost $30K–$100K. A boutique offering at $25K is competitive. |
| **Sales Motion** | Outbound to enterprises with known ECC→S/4HANA migration timelines. LinkedIn outreach. Partnership with SAP consultancies who refer pre-migration clients. |
| **Proof Needed** | 1. A repeatable 2–3 week assessment methodology. 2. Sample deliverables (sanitized). 3. At least one completed assessment with a testimonial. 4. Sales deck showing ROI (e.g., "we found 40% of your mappings had no owner"). |
| **Risk** | This is a services business, not a product business. Each assessment is custom labor. Hard to scale. Buyer may treat it as a one-off, not a gateway to ongoing tool adoption. |
| **Time to First Revenue** | 1–3 months (if a lead exists today). |
| **Verdict** | ✅ **Fastest path to first dollar.** High labor intensity, but directly monetizes the tool's capabilities. |

---

## Path 5: Paid Model Audit Package

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | Data governance team that already has "a data dictionary" (spreadsheets, Confluence, legacy catalog) and wants an independent validation. |
| **Offer** | "We validate your current model documentation against best practices and SAP context rules. Deliverable: audit report with severity-ranked gaps, recommended fixes, and a canonical model import plan." |
| **Price Hypothesis** | $8,000–$25,000 per audit. Benchmark: data governance consulting day rates are $1,500–$2,500/day. A 5-day audit = $7,500–$12,500. |
| **Sales Motion** | Inbound from content (blog posts on data governance gaps). Outbound to data governance leaders on LinkedIn. |
| **Proof Needed** | 1. A published audit methodology. 2. Sample audit report (sanitized). 3. Case study showing before/after. 4. Tooling to automate parts of the audit (this exists: `modelops validate`, `modelops health`, `modelops analyze`). |
| **Risk** | Similar to Path 4: services, not product. Buyers may take the report and not adopt the tool. Need to bundle audit + 1-year license to lock in recurring revenue. |
| **Time to First Revenue** | 1–3 months. |
| **Verdict** | ✅ **Viable and complementary to Path 4.** Can be sold as a lower-tier entry point. |

---

## Path 6: Paid Domain Packs

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | Enterprise migration team or consultancy that wants pre-built SAP modules (FI, MM, SD, etc.) instead of building from scratch. |
| **Offer** | Pre-built canonical models for specific SAP domains: Business Partner (exists), Supplier/Vendor (exists), Material Master, Finance (GL/AP/AR), etc. Each pack includes: canonical objects, validation rules, sample datasets, demo scripts, documentation. |
| **Price Hypothesis** | $2,000–$8,000 per domain pack. Benchmark: SAP training courses cost $500–$2,000; template libraries for data migration tools cost $1K–$5K. A full FI domain with 100+ attributes and mappings could command $5K. |
| **Sales Motion** | Marketplace listing (GitHub, website). Bundled with team license or assessment. |
| **Proof Needed** | 1. At least 3 high-quality domain packs (currently: BP/Customer, Supplier/Vendor, Product — but these are thin). 2. Documentation showing coverage. 3. Validation rules that actually catch real errors. 4. A buyer who wants them (market validation). |
| **Risk** | Currently only 2 SAP domain packs exist, and they are MVP-thin (~20–40 attributes). Building comprehensive FI/MM/SD packs is 2–3 months of SAP functional expertise each. Without a buyer commitment, this is speculative R&D. |
| **Time to First Revenue** | 3–6 months (if building packs now). |
| **Verdict** | ⚠️ **Viable as an upsell, not a lead product.** Sell the assessment first, then upsell domain packs to accelerate the model build. |

---

## Path 7: Private Enterprise Deployment

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | Large enterprise (10,000+ employees) with strict on-premise / air-gapped requirements. Financial services, defense, pharma. |
| **Offer** | On-premise install + annual support + custom validation rules + SLA. |
| **Price Hypothesis** | $30,000–$100,000/year. Benchmark: enterprise data governance platforms (Collibra, Alation) start at $170K–$200K/yr. Martenweave is lighter, so 50% discount is justified. |
| **Sales Motion** | Enterprise sales cycle: 6–12 months. Security review. Procurement. Pilot. |
| **Proof Needed** | 1. A UI. 2. SSO integration (SAML/OIDC). 3. Security documentation (SOC 2, penetration test). 4. Air-gapped installation docs. 5. Reference customer in a similar industry. 6. Legal entity, insurance, standard MSA. |
| **Risk** | Enterprise buyers will not buy a CLI-only Python package from an unknown vendor. The sales cycle is long and expensive. Martenweave lacks every enterprise prerequisite. |
| **Time to First Revenue** | 12–24 months. |
| **Verdict** | ❌ **Not viable now.** Requires UI, security certs, and enterprise credibility that do not exist. |

---

## Path 8: Training / Workshops

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | SAP consultancy training their staff. Enterprise migration team upskilling. Data governance team learning canonical modeling. |
| **Offer** | 1-day or 2-day workshop: "Canonical Data Modeling with Martenweave." Hands-on: build a model, validate it, detect gaps, review AI patches. |
| **Price Hypothesis** | $800–$1,500 per person for 2 days. Benchmark: data modeling workshops cost €1,300–€1,450 ($1,400–$1,600) for 2 days; dbt training is similar. Corporate on-site: $10,000–$20,000 for up to 12 people. |
| **Sales Motion** | Direct outreach to consultancies. Listing on training marketplaces. Content marketing. |
| **Proof Needed** | 1. A polished training deck and lab exercises. 2. Trainer with credibility (SAP + data governance background). 3. At least one pilot workshop with feedback. 4. Certification or completion badge (optional but helps). |
| **Risk** | Training revenue is lumpy and scales with trainer time. It is not recurring. It can be a good lead gen tool, but not a primary revenue engine. |
| **Time to First Revenue** | 1–2 months (if training material is created). |
| **Verdict** | ✅ **Viable as lead gen and revenue.** Low risk, fast to test. Can validate demand for the tool itself. |

---

## Path 9: "AI-Ready Model Layer" Implementation Package

| Dimension | Assessment |
|-----------|------------|
| **Buyer** | Enterprise wanting to "prep data for AI" — CIO or Chief Data Officer responding to board pressure about AI readiness. |
| **Offer** | Implement Martenweave + train team + build initial model + integrate with AI pipeline (MCP, API). Deliverable: a governed model layer with traceability, ready for LLM context injection. |
| **Price Hypothesis** | $40,000–$120,000 per engagement. Benchmark: AI readiness consulting engagements range from $50K–$200K. This is a premium positioning. |
| **Sales Motion** | Outbound to CDOs. Content marketing on "AI-ready data." Partnership with AI consultancies. |
| **Proof Needed** | 1. A real AI provider integration (not `NoProviderAdapter`). 2. A case study showing an LLM using the model layer for context. 3. MCP server demo that actually works with a popular AI tool (Claude, Cursor, etc.). 4. ROI narrative: "Your LLM hallucinates less because it has canonical definitions." |
| **Risk** | The AI integration is currently stubbed. Selling "AI-ready" without working AI is dangerous and potentially fraudulent. Buyer will discover the gap during implementation. |
| **Time to First Revenue** | 3–6 months (after real AI integration is built). |
| **Verdict** | ⚠️ **High potential, high risk.** The positioning is strong, but the product cannot deliver today. Build first, sell second. |

---

## Path 10: SaaS Later

| Dimension | Assessment |
|-----------|------------|
| **When would it make sense?** | After: (a) a UI exists, (b) 50+ paying team licenses or 5+ enterprise deployments, (c) multi-tenant architecture is built, (d) $500K+ ARR from non-SaaS revenue proves demand. |
| **What must exist first?** | 1. Web UI (React/Vue/Svelte) with auth. 2. Multi-tenant backend (API + DB per tenant or row-level security). 3. Billing/subscription infrastructure (Stripe, usage metering). 4. SOC 2 Type II. 5. At least one full-time SRE. 6. Pricing power proven from on-prem licenses. |
| **Price Hypothesis** | $50–$150/user/month. Benchmark: Atlan ~$100/user/month; Collibra ~$200+/user/month for creators. Martenweave would start at the low end. |
| **Risk** | Building SaaS is a 6–12 month engineering effort that distracts from revenue. Premature SaaS kills early-stage companies. The local-first architecture is actually a differentiator — don't abandon it too quickly. |
| **Time to Viability** | 18–36 months from today. |
| **Verdict** | ❌ **Not now.** SaaS is a Phase 3 move, not a Phase 1 move. |

---

## Cross-Cutting Analysis

### What is the FASTEST path to first paid dollar?

**Path 4: Paid Migration Readiness Assessment** (1–3 months).

Why: It is a services sale, not a product sale. It requires no UI, no SaaS, no security certs. It directly uses existing capabilities (`validate`, `health`, `analyze`, `gap-report`, `impact`). The buyer (migration program manager) has budget authority and urgency (2027 ECC deadline). The deliverable (audit report + canonical model) is tangible.

**Immediate action:** Create a 1-page "S/4HANA Migration Readiness Assessment" service description. Price it at $15K–$25K. Identify 10 target enterprises with known ECC→S/4HANA timelines. Reach out with a personalized gap-analysis offer.

### What is the HIGHEST-VALUE path long-term?

**Path 3 (Team License) + Path 6 (Domain Packs) + Path 9 (AI-Ready Package) combined.**

The vision: Martenweave becomes the "Atlan for SAP migration teams" — a lightweight, modern alternative to Collibra/Alation, purpose-built for migration and MDM governance. Recurring revenue from team licenses ($10K–$50K/yr) + high-margin domain packs ($2K–$8K each) + premium AI implementation packages ($50K–$100K).

This requires: UI, real AI integration, 5+ reference customers, and comprehensive domain packs. Timeline: 12–24 months.

### What is the most REALISTIC path given current state?

**A hybrid services-first approach:**

1. **Months 1–3:** Sell Path 4 (Assessments) and Path 5 (Audits) to generate cash and validate demand.
2. **Months 2–6:** Run Path 8 (Training/Workshops) for consultancies to build awareness and train future champions.
3. **Months 3–9:** Use services revenue to fund Path 6 (Domain Packs) and Path 2 (Consulting Accelerator partnerships).
4. **Months 6–12:** If 3+ consultancies adopt Martenweave and 2+ enterprises renew after assessment, build a minimal UI and test Path 3 (Team License).
5. **Months 12–24:** If team licenses work, build multi-tenant SaaS (Path 10).

### What trigger events cause a buyer to act?

| Trigger Event | Buyer | Path |
|---------------|-------|------|
| SAP announces ECC end-of-support deadline (2027) | CIO / Migration PM | Path 4 |
| Migration project starts; team realizes Excel mappings are ungoverned | Data Migration Lead | Path 4, Path 9 |
| Post-migration AMS handover; no documentation exists | AMS Manager | Path 5 |
| AI initiative launched; CDO needs "clean data layer" | CDO / CAO | Path 9 |
| Data governance audit finds gaps | Data Governance Manager | Path 5 |
| Consultancy wants to differentiate from competitors | Consulting Partner | Path 2, Path 8 |
| New SAP module rollout (e.g., BP in S/4HANA) | Functional Lead | Path 6 |

**The strongest trigger is the 2027 ECC deadline.** It creates urgency, budget, and a defined timeline. Martenweave should anchor all messaging to this trigger.

---

## Pricing Benchmarks (Grounded Research)

| Comparable | Price Point | Source |
|------------|-------------|--------|
| Collibra (enterprise data governance) | $170K–$510K/yr | checkthat.ai, analytica.net |
| Alation (data catalog) | $198K–$400K/yr | thedatagovernor.com |
| Atlan (modern data catalog) | $30K–$150K/yr | ovaledge.com |
| Informatica CDGC | $100K–$500K/yr | improvado.io |
| SAP S/4HANA migration (mid-market) | $1M–$8M total | tachyontech.com, softwareseni.com |
| SAP consultant (senior, US) | $120–$250/hr | abbacustechnologies.com |
| SAP consultant (UK/EU day rate) | £500–£950/day | whitehallresources.com |
| Data modeling workshop (2-day) | €1,300–€1,450/person | adeptevents.nl |
| AI data modeling masterclass (1-day) | $899/person | eacoe.org |
| Open-source support (small tool) | $4,585–$9,685/yr | onestop.biz |
| Red Hat RHEL (cloud, per vCPU/yr) | $68–$106/vCPU/yr | tencentcloud.com |

---

## What Must Exist Before Each Path is Viable

| Path | Prerequisites | Current Status |
|------|---------------|----------------|
| 1. OSS + Support | 500+ stars, 10+ organic users, community | ❌ Zero |
| 2. Consulting Accelerator | 1 consultancy partner, case study, training deck | ⚠️ Possible now |
| 3. Team License | UI, 1 reference customer, security docs | ❌ No UI |
| 4. Migration Assessment | Methodology, sample deliverables, sales deck | ✅ Mostly exists |
| 5. Model Audit | Audit methodology, sample report, automation | ✅ Mostly exists |
| 6. Domain Packs | 3+ comprehensive packs, buyer validation | ⚠️ 2 thin packs exist |
| 7. Enterprise Deployment | UI, SSO, SOC 2, legal entity, insurance | ❌ None |
| 8. Training/Workshops | Training deck, lab exercises, trainer | ⚠️ Docs exist; needs packaging |
| 9. AI-Ready Package | Real AI provider integration, MCP demo, case study | ❌ Stubbed AI |
| 10. SaaS | UI, multi-tenancy, billing, SOC 2, $500K+ ARR proof | ❌ None |

---

## Recommendations

### Immediate (Next 30 Days)
1. **Package and price Path 4:** Create a "S/4HANA Migration Readiness Assessment" service page. Price: $15,000–$25,000. Identify 10 target accounts.
2. **Create training material for Path 8:** A 1-day "Canonical Modeling for SAP Teams" workshop. Price: $1,200/person or $10,000 on-site.
3. **Do not build a UI yet.** Services revenue should fund future product development.

### Short-Term (Months 2–6)
4. **Execute 2–3 paid assessments.** Use revenue to hire SAP functional expertise for domain pack expansion.
5. **Run 2 pilot workshops** with SAP consultancies. Convert attendees into champions.
6. **Build real AI provider integration** (OpenAI, Anthropic, or Google). This unlocks Path 9 and makes the product significantly more valuable.

### Medium-Term (Months 6–12)
7. **Expand domain packs:** Build comprehensive FI, MM, and SD packs. Sell as upsells to assessment clients.
8. **Test team license pricing** with assessment clients who want ongoing access. Start at $5,000–$10,000/yr for a 5-person team.
9. **Build a minimal read-only UI** (optional but helpful for sales). Even a static HTML dashboard generated by `modelops docs-build` would help.

### Long-Term (Months 12–24)
10. **If 5+ team licenses exist and $200K+ ARR is proven**, begin SaaS architecture planning.
11. **Otherwise, double down on services + domain packs.** A profitable services business with a strong open-source core is a valid outcome.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| No buyer knows Martenweave exists | Anchor to 2027 ECC deadline. Publish LinkedIn content. Partner with SAP consultancies for distribution. |
| Product is CLI-only, limiting buyer pool | Sell to technical buyers (migration analysts, data engineers) first. Use services to bridge the gap. |
| AI integration is stubbed | Do not sell "AI-ready" until it works. Sell "governed model layer" instead. |
| Building UI/SaaS too early drains cash | Explicitly defer SaaS. Fund product development from services revenue. |
| Domain packs are thin | Charge for assessment + model build, then open-source the resulting domain pack as marketing. |
| Competitors (Collibra, Alation) have massive budgets | Compete on specificity (SAP migration) and price (10x cheaper). Do not compete on breadth. |

---

## Conclusion

Martenweave is a **strong technical product with no commercial infrastructure.** The path to revenue is not through product-led growth or SaaS — those require a UI, community, and capital that do not exist. The path is through **services-led revenue** (assessments, audits, training) that validates demand, builds case studies, and funds product expansion.

**The 2027 SAP ECC end-of-support deadline is the single greatest commercial opportunity.** Every enterprise running ECC is a potential assessment client. Martenweave should own the narrative: "Before you migrate, know your data."

**First dollar target:** $15,000 assessment within 60 days.
**12-month target:** $100,000–$150,000 from assessments + training + domain pack sales.
**24-month target:** $300,000+ ARR with a mix of team licenses, domain packs, and premium services.

SaaS is a 2028 conversation, not a 2026 conversation.

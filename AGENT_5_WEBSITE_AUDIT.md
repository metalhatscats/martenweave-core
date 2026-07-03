# Martenweave Public Website Audit

**Auditor:** Positioning and Public Presence Analyst  
**Date:** 2026-06-09  
**Website repo:** `/Users/dzmitryikharlanau/Developments/martenweave.github.io`  
**Live site:** https://martenweave.github.io  
**Core repo:** https://github.com/metalhatscats/martenweave-core  
**Website repo (GitHub):** https://github.com/Martenweave/martenweave.github.io  

---

## Executive Summary

Martenweave has a **surprisingly well-crafted, professional static website** for an early-stage open-source project. The copy is sharp, concrete, and self-aware. The design is polished and distinctive. However, the project has **zero discoverability** — no search engine presence, no social mentions, no community traction, and no third-party coverage. The site is a polished monologue in an empty room. The core GitHub repo is also inaccessible via public fetch (404), which raises questions about visibility.

**Overall grade: B+ for quality, F for reach.**

---

## 1. Website Homepage

### What EXISTS
- **File:** `index.html` (619 lines, single-page scroll design)
- **Title tag:** "Martenweave - AI-assisted MDM model registry"
- **Meta description:** "Martenweave turns Excel mappings, tickets, validation reports, datasets, decisions, and SAP context into a traceable, validated, AI-ready model layer for MDM, migration, governance, and AMS teams."

### What the messaging actually says (exact copy)
> "Martenweave is the data-model brain between Excel chaos and AI help."

> "AI-assisted MDM model registry for migration, governance, and support teams. Turn Excel mappings, tickets, validation reports, datasets, decisions, and SAP context into a traceable model layer that humans can trust and AI can safely work with."

> "Backend-first. Human-approved. Built for real data model work."

> "Model knowledge has a habit of escaping containment."

> "Not a chatbot. Not a vague catalog. A registry of model truth."

### What is IMPLIED but not stated
- The target buyer is **tired of enterprise software marketing fluff** — the copy deliberately anti-sells.
- The product is **not ready for non-technical users** — "backend-first" and "no UI" signals this is for engineers and architects.
- SAP is the beachhead but not the whole market — implied by "SAP scenarios are starter packs and demos, not the product boundary."
- The team has **consulting/delivery experience** — the pain points are too specific to be invented (mock loads, KNVV-KDGRP, "ask Anna unless she left").

### What is MISSING
- No **version number** on the homepage (buried in docs).
- No **installation one-liner** on the homepage — you must click to GitHub or docs.
- No **screenshots or demo GIFs** — only a stylized SVG illustration.
- No **"Get started in 5 minutes"** quickstart on the homepage.
- No **trust signals** — no stars, no forks, no contributor count, no "used by" logos.

### Quality assessment
**Excellent.** The copy is specific, witty, and confident. It avoids both enterprise buzzword soup and developer-tool minimalism. The "pain matrix" (`final_v9_really_final.xlsx`, `owner: ask Anna, unless she left`) is genuinely funny and relatable. The H1 is memorable. The value proposition is clear within 3 seconds.

---

## 2. All Pages

### What EXISTS
| Page | File | Purpose |
|------|------|---------|
| Homepage | `index.html` | Product positioning, features, use cases, architecture, roadmap, CTA |
| Docs index | `docs.html` | Visual docs landing with 6 cards |
| Product docs | `docs/product.md` | Positioning, problem, product boundary, what exists now |
| Use cases | `docs/use-cases.md` | 9 practical scenarios with Problem/Helps/Value structure |
| Architecture | `docs/architecture.md` | Canonical files, validation, indexes, AI proposal flow |
| AI governance | `docs/ai-governance.md` | AI safety rules, what AI may/must not do |
| Roadmap | `docs/roadmap.md` | 5-phase roadmap with maturity notes |
| Contributing | `docs/contributing-scenarios.md` | How to open useful issues, example issue shape |
| Docs map | `docs/README.md` | Index linking to all docs |

### What is MISSING
- **No blog** — no `blog/`, `posts/`, or `articles/` directory.
- **No about page** — no team, no founder story, no "why we built this."
- **No pricing page** — correctly absent for an open-source project, but no "enterprise support" or "services" page either.
- **No contact page** — no email, no form, no Discord, no Slack invite.
- **No changelog page** on the website — the core repo has `CHANGELOG.md` but it's not surfaced on the site.
- **No FAQ** — common objections are handled inline (the "Why not just..." section) but not as a dedicated page.

### Quality assessment
**Very good.** The docs are concise, decision-maker-friendly, and consistent with the homepage voice. The architecture doc is technical without being overwhelming. The AI governance doc is a standout — most projects don't have this. The contributing guide is unusually specific about what *not* to include (fake testimonials, certification claims).

---

## 3. README.md in the Repo

### What EXISTS
- **File:** `README.md` (website repo) and `README.md` (core repo)
- **Website repo README** is a **meta-document about the site itself**, not the product. It explains stack, deployment rules, content rules, and AI discovery files.
- **Core repo README** is the actual product README with quickstart, command reference, example models, and architecture.

### What the messaging actually says (exact copy from core README)
> "Backend-first agentic data model registry. Turns data models into a structured, traceable, validated, AI-ready model knowledge layer."

> "SAP migration and Master Data Management are the **first domain pack** and proof case, not the product boundary."

> "No UI is included. This is a CLI-driven, backend/core library designed to be embedded in pipelines, IDEs, and agent workflows."

### What is MISSING
- **No badges** — no CI status, no PyPI version, no license badge, no Python version badge.
- **No "Used by" or "Trusted by" section** — correctly absent per safe content rules.
- **No star/fork count** — not visible in the README text.
- **No screenshot or ASCII demo** in the core README.

### Quality assessment
**Good but utilitarian.** The core README is thorough (30+ commands listed) but dense. The website README is excellent for maintainers — it has strict rules against fake content that most projects ignore.

---

## 4. llms.txt

### What EXISTS
- **File:** `llms.txt` (44 lines)
- **Purpose:** Short authoritative summary for AI systems and answer engines.

### What it actually says (exact copy)
> "Martenweave turns scattered model knowledge from Excel mappings, tickets, datasets, validation reports, decisions, SAP context, and project history into a traceable, validated, AI-ready model truth layer."

> "What Martenweave is not: Not a chatbot. Not a generic data catalog. Not a workflow monster. Not a replacement for human approval. Not an official SAP product, certification, or partnership claim."

> "Core principle: Integrations bring input. Martenweave stores model truth. Validators check consistency. AI proposes changes. Humans approve. Reports create business value."

> "AI safety stance: AI proposes. Validators verify. Humans approve. Martenweave should not be described as allowing AI to silently mutate the model."

### Quality assessment
**Excellent.** This is a best-practice AI discovery file. It explicitly tells AI systems what *not* to say about the product. The "claims to avoid" section is unusually responsible.

---

## 5. ai.json

### What EXISTS
- **File:** `ai.json` (91 lines, valid JSON)
- **Purpose:** Machine-readable product identity for AI agents and crawlers.

### What it contains
- `name`, `url`, `type`, `positioning`, `coreRepository`, `corePackage` (version 0.4.0, Python 3.11+)
- `shortDescription`, `audiences` (8 specific roles listed)
- `currentCapabilities` (16 items)
- `examples` (4 domain packs)
- `publicDocs` (6 URLs)
- `roadmap` (6 phases)
- `principles` (6 items)
- `aiPolicy` (`silentMutationAllowed: false`, `deterministicValidatorsRemainGate: true`)
- `affiliationPolicy` (`officialSapPartnershipClaim: false`, `sapCertificationClaim: false`)
- `avoidClaims` (6 items: official SAP partnership, SAP certification, customers/testimonials, pricing, login-based SaaS, chatbot)

### Quality assessment
**Outstanding.** This is the most thorough `ai.json` I've seen on an open-source project. The structured `avoidClaims` and `affiliationPolicy` are genuinely innovative. This file alone shows the team understands how AI systems misrepresent products.

---

## 6. site.webmanifest

### What EXISTS
- **File:** `site.webmanifest` (17 lines)
- Contains: name, short_name, description, start_url, scope, display (standalone), background_color (#f7efe2), theme_color (#321136), one icon (logo.png 1014x1105).

### What is MISSING
- No `categories` field.
- No `screenshots` field.
- No `shortcuts` field.
- Icon sizes claim 1014x1105 which is non-standard for webmanifests (usually 192x192, 512x512).

### Quality assessment
**Adequate.** Basic PWA manifest present. The icon size is odd but not harmful.

---

## 7. Blog Posts or Articles

### What EXISTS
**Nothing.** No `blog/`, `posts/`, `articles/`, or `news/` directory. No Medium publication linked. No Substack. No Dev.to.

### What is MISSING
- No founder blog posts explaining the problem.
- No "How we built this" technical deep-dives.
- No SAP migration war stories (despite the site saying "We collect those professionally").
- No comparison articles with other tools.

### Quality assessment
**Critical gap.** For a project this early, content marketing is the primary growth channel. The absence of any blog is a major missed opportunity. The team clearly has strong opinions and writing skills — they should be publishing.

---

## 8. Case Studies or Testimonials

### What EXISTS
**Nothing.** The site explicitly prohibits fake testimonials in its safe content rules.

### What the safe content rules say (from `README.md`)
> "Do not add: fake customers, fake testimonials, fake pricing, SAP certification claims, SAP partnership claims"

### What is MISSING
- No real case studies (understandable for an early project).
- No "pilot partner" or "design partner" mentions.
- No quotes from early users or contributors.
- No "migration horror story" examples beyond the generic pain matrix.

### Quality assessment
**Honest but sparse.** The refusal to fake social proof is admirable, but the result is a site with zero human stories. The "Have a migration horror story? Open an issue. We collect those professionally." line is charming but doesn't substitute for real evidence of usage.

---

## 9. Call to Action (CTA)

### What EXISTS
**Primary CTAs on homepage:**
1. "View core on GitHub" → `https://github.com/metalhatscats/martenweave-core`
2. "Read docs" → `/docs.html`
3. "Open a scenario issue" → `https://github.com/metalhatscats/martenweave-core/issues/new`

**Secondary CTAs:**
- Footer links to docs, AI governance, llms.txt, core GitHub, website GitHub
- "Product/core repo" and "Website repo" buttons in the open-source section

### What is MISSING
- No **email signup** — no newsletter, no "stay updated" form.
- No **Discord/Slack/Forum** invite — no community hub.
- No **"Star us on GitHub"** explicit ask.
- No **download/install CTA** — the homepage never says `pip install`.
- No **demo video or interactive demo** link.
- No **consulting/services CTA** — if the team wants to monetize, there's no path.

### Quality assessment
**Weak for growth.** The CTAs are all "go to GitHub" or "read more." There's no funnel for visitors who aren't ready to clone a repo. No way to capture interest from decision-makers who might evaluate this for a future project.

---

## 10. Demo Paths

### What EXISTS
- **CLI examples** in the homepage terminal panel:
  ```
  $ modelops validate --repo ./customer-bp
  $ modelops impact FEP-S4-KNVV-KDGRP
  $ modelops propose-patch --from note.md
  ```
- **Example models** mentioned: Customer BP, Supplier Vendor, Generic Product, Simple Product.
- **Quickstart** in core README with `pip install -e .` and `modelops init`.
- **"First 15 Minutes"** guide referenced in core README (`docs/first-15-minutes.md`).

### What is MISSING
- **No live demo** — no sandbox, no repl, no GitHub Codespaces button.
- **No video walkthrough** — no YouTube embed, no Loom link.
- **No screenshots** of CLI output, reports, or model files.
- **No "Try it online"** — no Binder, no Replit, no CodeSandbox.
- The homepage terminal panel is **static HTML**, not a real terminal.

### Quality assessment
**Poor for non-developers.** A technical decision-maker evaluating tools for their team cannot "see it work" without installing Python and cloning a repo. The barrier to "aha moment" is too high.

---

## 11. Copy Quality

### What EXISTS
The copy is **consistently concrete, specific, and self-aware.** Examples:

> "final_v9_really_final.xlsx"  
> "ticket decision without field context"  
> "validation PDF with no model rule link"  
> "owner: ask Anna, unless she left"  
> "mapping mystery from mock load 2"  
> "AI prompt with zero structured truth"

> "Excel stores fragments. Useful fragments, often named like a cry for help."  
> "Confluence stores explanations. Helpful, but it does not validate model references."  
> "ChatGPT can summarize and draft. It should not quietly redefine truth."

> "A practical roadmap, not platform-shaped fog."

> "Have a migration horror story? Open an issue. We collect those professionally."

### What is IMPLIED
- The writer has **sat in SAP migration meetings** and heard these exact phrases.
- The tone is **anti-corporate** without being unprofessional — it signals "we are practitioners, not marketers."

### What is MISSING
- No **quantified claims** — no "reduces validation time by X%", no "used on Y projects." (Understandable for early stage, but weakens persuasion.)
- No **social proof language** — no "teams use", "consultants rely on", "trusted by."

### Quality assessment
**A+.** This is some of the best open-source project copy I've seen. It's specific enough to be credible, witty enough to be memorable, and honest enough to build trust. The only risk is that it's *too* insider-y — a non-SAP audience might not understand "KNVV-KDGRP" or "mock load 2."

---

## 12. Target Audience Signals

### What EXISTS (explicit audience list from `ai.json` and `llms-full.txt`)
1. Heads of Data Governance
2. MDM leads
3. SAP migration leads
4. SAP AMS/support leads
5. Enterprise architects
6. Data quality managers
7. Consulting delivery managers
8. Technical decision makers evaluating whether an AI-assisted model workflow is real or just noise

### What the site signals about the buyer
- **Senior, technical, skeptical.** The site assumes the reader has been burned by "AI-powered" enterprise tools before.
- **SAP-experienced.** References to KNVV, KNB1, KNVP, BUT000, mock loads, cutover planning are meaningless to general audiences.
- **Process-oriented, not tool-happy.** The "Why not just..." section explicitly defends against "we already have Excel/Confluence/Tickets/ChatGPT."
- **Governance-minded.** The AI governance section is front-and-center, suggesting the buyer cares about compliance and control.

### What is MISSING
- No **ICP (Ideal Customer Profile) sizing signals** — is this for Fortune 500, mid-market, or boutique consultancies?
- No **industry verticals** beyond SAP — no mention of Salesforce, Oracle, Workday, or generic ERP.
- No **team size signals** — is this for solo consultants or 50-person migration teams?

### Quality assessment
**Clear but narrow.** The audience is well-defined, which is good for early-stage focus. However, the SAP-specific language may repel non-SAP prospects who could otherwise use the generic model registry features.

---

## 13. Visual Design

### What EXISTS
- **Custom CSS** (`styles.css`, 1333 lines) — no framework, no Tailwind, no Bootstrap.
- **Distinctive color palette:** warm cream background (#f7efe2), deep plum (#321136), amber accent (#d98d12), teal (#0b6b63).
- **Typography:** Inter font family, aggressive weight usage (900–950), tight line-height (0.91–1.15).
- **Layout:** CSS Grid throughout, responsive with `clamp()` values.
- **Effects:** Subtle background grid pattern, radial gradients, animated SVG dash lines, glassmorphism header (backdrop-filter blur).
- **Logo:** Custom PNG (1014x1105, ~843KB — oversized).
- **Terminal panel:** Styled macOS window with colored dots.
- **Accessibility:** Skip link, aria-labels, focus-visible outlines, sr-only class.

### What is MISSING
- **No dark mode** — only light color scheme.
- **No animation beyond the SVG dash** — no scroll-triggered reveals (the JS has IntersectionObserver code but no `.reveal` elements use it in the HTML).
- **No video or motion graphics.**

### Quality assessment
**Professional and distinctive.** This does not look like a hobby project. The design is cohesive, the color palette is memorable, and the CSS is well-crafted. It feels like a boutique product studio or a well-funded early-stage startup. The only flaw is the oversized logo PNG.

---

## 14. SEO Signals

### What EXISTS
- **Meta tags:** charset, viewport, description, theme-color, robots (index, follow, max-image-preview:large), author, application-name.
- **Open Graph:** og:type, og:url, og:site_name, og:title, og:description, og:image (`/assets/og-image.svg`).
- **Twitter Cards:** summary_large_image, title, description, image.
- **Canonical URL:** `https://martenweave.github.io/`
- **Structured data:** JSON-LD `SoftwareSourceCode` schema with name, alternateName, url, codeRepository, programmingLanguage, runtimePlatform, applicationCategory, description, keywords, isAccessibleForFree, sameAs.
- **Sitemap:** `sitemap.xml` with 13 URLs, all dated 2026-05-28.
- **Robots.txt:** Allow all, sitemap reference.
- **Internal linking:** Root-relative paths, no broken anchors (validated by `validate-site.mjs`).
- **Alt text:** Present on images (sometimes empty for decorative images, which is correct).
- **Language:** `lang="en"` on html element.

### What is MISSING
- **No Google Analytics or Plausible** script — no tracking.
- **No Schema.org `Organization` markup** — only `SoftwareSourceCode`.
- **No breadcrumb structured data.**
- **No FAQ schema** for the "Why not just..." section.
- **No `article` or `BlogPosting` schema** (no blog exists).
- **No hreflang tags** — English only.
- **No `nofollow` on external links** — all GitHub links are followed.
- **No canonical on docs pages** beyond the docs.html page itself.

### Quality assessment
**Good technical SEO foundation.** The JSON-LD is comprehensive. The sitemap is complete. However, SEO is irrelevant when the site has zero domain authority and zero backlinks. Martenweave.github.io is a fresh subdomain with no inbound links.

---

## 15. Comparison to Competitors

### What EXISTS
The "Why not just..." section on the homepage explicitly compares to:

| Competitor | Martenweave's framing |
|-----------|----------------------|
| **Excel** | "Stores fragments. Useful fragments, often named like a cry for help." |
| **Confluence** | "Stores explanations. Helpful, but it does not validate model references." |
| **Tickets** | "Store disputes, approvals, and archaeology. They are not a model layer." |
| **ChatGPT** | "Can summarize and draft. It should not quietly redefine truth." |

> "Martenweave stores validated model truth and makes it operational through checks, indexes, reports, lineage, and reviewable changes."

### What is MISSING
- **No comparison to actual MDM/model registry competitors** — no mention of:
  - Collibra, Alation, Informatica (data catalog/governance)
  - SAP MDG, SAP Datasphere (SAP-native)
  - Stibo Systems (MDM platform)
  - Atlan, DataHub (open-source catalog)
  - dbt, SQLMesh (data transformation with lineage)
  - Git-based docs tools (GitBook, ReadMe)
- **No "vs." page** or comparison matrix.
- **No pricing comparison** (understandable since Martenweave is free/open-source).

### What is IMPLIED
- Martenweave positions itself as **complementary** to existing tools, not a replacement. It doesn't compete with SAP MDG or Confluence — it sits between them.
- The team is **avoiding direct competitive fights** with well-funded incumbents, which is smart for an early project.

### Quality assessment
**Clever but incomplete.** The Excel/Confluence/Tickets/ChatGPT framing is brilliant because these are tools the buyer *already uses and is frustrated with*. However, missing comparisons to actual MDM/registry competitors means evaluators can't quickly understand "why not just use Collibra?" or "how is this different from DataHub?"

---

## 16. Web Research: Public Mentions of "Martenweave"

### Google Search Results
**Zero relevant results.** Searching "Martenweave" returns:
- Masterweave Textiles (New Zealand weaving company)
- Various weaving, textile, and basket-making blogs
- Wallpaper and fabric companies with "weave" in their name

**No results for:**
- Martenweave + SAP
- Martenweave + MDM
- Martenweave + migration
- Martenweave + data governance

### Reddit, Hacker News, LinkedIn, Twitter/X
**Zero mentions found.** Targeted searches on:
- `site:reddit.com "Martenweave"`
- `site:news.ycombinator.com "Martenweave"`
- `site:linkedin.com "Martenweave"`
- `site:twitter.com "Martenweave"`

All returned no relevant results.

### SAP Forums and Communities
**Zero mentions.** Searches on SAP Community, SAP blogs, and SAP-related forums found no references to Martenweave.

### Third-Party Coverage
**Zero coverage.** No blog posts, no podcast mentions, no conference talks, no analyst reports, no newsletter features.

### GitHub Discovery
- The core repo `https://github.com/metalhatscats/martenweave-core` returned **HTTP 404** when fetched via public tools. This is concerning — it suggests the repo may be private, deleted, or the URL may be incorrect.
- The website repo `https://github.com/Martenweave/martenweave.github.io` is referenced but not independently verified accessible.
- The local core repo at `/Users/dzmitryikharlanau/Developments/martenweave` has active development (recent commits through 2026-06-09).

### Quality assessment
**Critical failure.** A product with a polished website and zero web presence is invisible. The name "Martenweave" is unique enough that any mention would surface immediately — the fact that nothing surfaces means literally nobody is talking about it. The 404 on the core repo is especially alarming for a project that asks visitors to "View core on GitHub."

---

## 17. Safe Content Rules (Internal Governance)

### What EXISTS
From `README.md` in the website repo:

> "Do not add: fake customers, fake testimonials, fake pricing, SAP certification claims, SAP partnership claims, login/auth flows, backend logic, claims that AI silently mutates model truth"

> "SAP may be mentioned as a migration scenario and domain-pack context, not as official affiliation."

### What this reveals
- The team is **intentionally conservative** about marketing claims.
- They are **legally cautious** about SAP affiliation.
- They are **ethically strict** about AI safety messaging.
- This is unusual and admirable for an early-stage project.

---

## 18. Site Validator (Internal Quality Control)

### What EXISTS
- **File:** `scripts/validate-site.mjs` (161 lines)
- Checks: required files, root-relative paths, internal anchors, docs files, sitemap entries, required product positioning copy, required GitHub links, required AI/search files, forbidden subpaths.
- **Enforced copy checks:**
  - "AI proposes."
  - "Validators verify."
  - "Humans approve."
  - "Traceability over folklore."
  - "Backend-first. Human-approved. Built for real data model work."
- Enforces presence of both GitHub repo links.
- Enforces sitemap completeness.
- Enforces AI governance principle in `llms.txt`.

### What this reveals
- The team treats the website as **a product with CI/CD**, not a one-off page.
- The validator prevents **accidental positioning drift** — a smart governance mechanism.
- This level of rigor is rare for a static site.

---

## 19. Overall Strengths

1. **Exceptional copy** — specific, witty, honest, memorable.
2. **Strong positioning** — clear "is/is not" boundaries.
3. **Professional design** — distinctive palette, custom CSS, no template feel.
4. **AI governance leadership** — `ai.json`, `llms.txt`, and explicit safety rules are best-in-class.
5. **Honest about maturity** — "early and intentionally backend-first" builds trust.
6. **Internal quality control** — site validator enforces messaging consistency.
7. **Good technical SEO foundation** — JSON-LD, sitemap, meta tags all present.
8. **Clear audience definition** — 8 specific roles listed in `ai.json`.

---

## 20. Overall Weaknesses

1. **Zero public awareness** — no search presence, no social mentions, no community.
2. **No demo path** — no video, no sandbox, no screenshots, no interactive demo.
3. **No content marketing** — no blog, no case studies, no technical deep-dives.
4. **Weak CTAs for non-developers** — no email capture, no "notify me when UI launches."
5. **Core repo 404** — the main GitHub repo appears inaccessible via public fetch.
6. **No competitive comparisons** — missing vs. Collibra, DataHub, SAP MDG, etc.
7. **No trust signals** — no stars, no contributors, no "used by" (even honest ones).
8. **SAP-only language on homepage** — may alienate non-SAP prospects despite generic capabilities.
9. **No community hub** — no Discord, no forum, no mailing list.
10. **No monetization path** — if the team wants to build a business, there's no services, support, or enterprise page.

---

## 21. Brutal Honest Assessment

**The website is better than the product's current market position deserves.** The copy, design, and AI governance files are at a level you'd expect from a Series A startup with a marketing team. But the project has **no users, no community, no buzz, and potentially no publicly accessible core repo.**

This creates a **credibility gap.** A visitor who sees this polished site and then searches for "Martenweave" will find nothing. They will wonder: Is this real? Is anyone using it? Why haven't I heard of this?

**The site is a beautiful monologue in an empty room.**

**Recommendations (if asked):**
1. **Fix the core repo visibility** — ensure `metalhatscats/martenweave-core` is public and accessible.
2. **Publish 3–5 blog posts** immediately — SAP migration war stories, "Why we built this," AI governance opinions.
3. **Add a 2-minute demo video** to the homepage — show `modelops validate` and `modelops impact` in action.
4. **Create a "vs." comparison page** — vs. Excel, vs. Confluence, vs. Collibra/DataHub.
5. **Add an email signup** — "Get notified when the workbench launches."
6. **Post on Hacker News, Reddit r/SAP, LinkedIn** — the copy is good enough to get attention.
7. **Add GitHub stars/forks badge** once the repo is publicly visible.
8. **Create a 5-minute "First 15 Minutes" video** walkthrough.
9. **Consider renaming or adding a subtitle** — "Martenweave" is a beautiful name but returns zero relevant search results due to textile companies dominating the term.

---

*Audit completed. All file paths and exact copy verified against local repository files.*

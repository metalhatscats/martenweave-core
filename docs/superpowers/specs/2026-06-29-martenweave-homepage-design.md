# Martenweave Homepage Redesign — Design Spec

**Date:** 2026-06-29  
**Project:** `Martenweave/martenweave.github.io`  
**Goal:** Redesign the homepage into a premium, minimal, search-first landing page while preserving SEO, structured data, Open Graph, `llms.txt`, `ai.json`, sitemap, and crawlability.

---

## 1. Problem / Context

The current homepage is a conventional SaaS marketing page: long hero, architecture diagram, multiple feature sections, process rail, use-case grid, and a closing CTA. The user asked for something far more restrained — a search-first landing page that feels modern, technical, high-trust, and clean, with no busy layout or AI hype.

---

## 2. Design Principles

- **Search is the hero.** The largest, most prominent element is a single search bar.
- **Radical restraint.** Only a header, headline, subhead, search bar, example queries, trust line, three quick links, and a footer.
- **High-trust, technical tone.** Neutral palette, clean typography, ample whitespace, no gradients or animation excess.
- **No AI hype.** AI is mentioned only as "human-approved AI proposals" in the trust line.
- **Preserve discoverability.** Keep canonical metadata, JSON-LD, `llms.txt`, `ai.json`, sitemap, and internal links that the validator expects.

---

## 3. Layout

```
┌─────────────────────────────────────────────┐
│ [Logo] Martenweave              GitHub  Docs │  minimal header
├─────────────────────────────────────────────┤
│                                             │
│   Open-source model registry                │
│   for SAP migration, MDM, and governance    │  short headline
│                                             │
│   Canonical files, deterministic validation,│  one-line subhead
│   gap detection, lineage, impact, and       │
│   human-approved AI proposals.              │
│                                             │
│   ┌───────────────────────────────────┐     │
│   │  🔍  Search models, fields, SAP   │     │  dominant search
│   │      tables, validation rules…    │     │
│   └───────────────────────────────────┘     │
│   Try: Customer Group · KNVV · dataset gaps │  example queries
│                                             │
│   Open source · Python 3.11+ · Local-first  │  tiny trust line
│                                             │
│   [Quickstart] [GitHub] [Docs]              │  3 quick links
│                                             │
├─────────────────────────────────────────────┤
│  Martenweave · AI proposes. Validators      │  simple footer
│  verify. Humans approve.                    │
└─────────────────────────────────────────────┘
```

---

## 4. Approaches Considered

### A. Monolithic redesign (recommended)
Replace the homepage HTML and CSS, add a generated search index, update build/validation scripts. Keeps full control and a coherent visual system.

**Pros:** Cleanest result, easiest to make responsive, no hidden legacy sections.  
**Cons:** Touches more files.

### B. Overlay on existing page
Hide the existing verbose sections and overlay a search-first hero.

**Pros:** Smaller HTML diff.  
**Cons:** Hacky, hurts performance, leaves dead markup and CSS.

### C. Separate `home.css` + shared `core.css`
Split styles into shared and homepage-specific sheets.

**Pros:** Clean separation.  
**Cons:** Larger refactor; docs pages already rely on the current single stylesheet.

**Decision:** Approach A, but pragmatically preserve docs-related CSS classes so `docs.html` and generated doc pages continue to render correctly.

---

## 5. Search Behavior

- Build step generates `docs/search-index.json` from the generated doc pages and the homepage.
- Each entry contains `url`, `title`, `category`, and `excerpt`.
- Client-side JS fetches the index, tokenizes query terms, and scores matches in title, category, and excerpt.
- Results render in a small overlay below the search bar.
- Keyboard support: focus search, arrow keys to navigate results, Enter to open, Escape to close.
- Graceful degradation: if the index is unavailable, Enter navigates to `/docs.html`.

---

## 6. Files to Change

- `index.html` — new minimal homepage; preserve all `<head>` metadata and JSON-LD.
- `styles.css` — replace old homepage section styles with minimal search-first styles; keep docs/header/footer styles.
- `script.js` — add search controller; keep existing header scroll + reveal logic.
- `scripts/build-docs.mjs` — generate `docs/search-index.json` after rendering docs.
- `scripts/validate-site.mjs` — update required copy and link checks to match new design; add `search-index.json` check.
- `sitemap.xml` — bump `lastmod` for `/` and add `/docs/search-index.json`.

---

## 7. Validation Criteria

- `npm run validate` passes.
- Homepage renders correctly at 1280×800 and 390×844.
- Search returns results for sample queries.
- No console errors; favicon loads.
- Metadata validator confirms title, description, Open Graph, Twitter, JSON-LD, and AI files are intact.

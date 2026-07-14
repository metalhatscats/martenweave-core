# Martenweave Workbench

> Official local browser UI for Martenweave Core.

This directory contains **Martenweave Workbench**, the local interactive workspace for assessment,
investigation, review, reports, and controlled changes. It runs on `localhost` and connects to
Martenweave Core through the local API. It is **not a hosted production app** and does not replace
the CLI-first, canonical-file-driven core workflow.

## What the Workbench is

- The official local browser UI for Martenweave Core.
- A browser-based **interactive workspace** that demonstrates seven model-governance screens: Home, Models (global search), Object detail, Lineage, Gaps, Proposals, and Proposal review.
- A way to review responsive navigation, model search, lineage canvas, gap workflows, and proposal approval flows connected to the local API.
- A local-first React + Vite application packaged as static assets.

## What the Workbench is not

- **Not a hosted production app.** It is built to run on `localhost` from an installed package or cloned repository.
- **Not a SaaS dashboard or generic chatbot.** The copy and interactions are specific to model governance and SAP migration workflows.
- **Not a replacement for the Martenweave CLI.** Validation, indexing, lineage, and impact analysis remain backend/core services.
- **It does not write to SAP.** All SAP context is read-only.
- **It does not mutate canonical model files without review.** Real changes still require human-reviewed `PatchProposal` → `ChangeRequest` workflows in Core.
- **AI proposals are review artifacts, not automatic changes.** Any AI-assisted suggestions must be approved before they touch canonical files.

## Prerequisites

- Node.js 20+ (LTS recommended)
- npm 10+

No runtime environment variables are required. See [`.env.example`](.env.example) for details.

## Install dependencies

```bash
cd frontend
npm install
```

## Run locally

```bash
npm run dev
```

Then open <http://127.0.0.1:5173> (or the URL shown in the terminal).

## Build

```bash
npm run build
```

The static files are written to `frontend/dist/`.

## Preview production build

```bash
npm run preview
```

Then open <http://127.0.0.1:4173> (or the URL shown in the terminal).

## Demo data

All data lives in [`src/data.js`](src/data.js). It is hand-crafted demo data that represents a small slice of a Business Partner / Customer migration model. It is not connected to a live backend or SAP system.

## Main screens

| Screen | Route | Source |
|---|---|---|
| Home | `#/home` | `App.jsx` |
| Models (global search) | `#/models` | `App.jsx` |
| Object detail | `#/object` | `App.jsx` |
| Lineage | `#/lineage` | `App.jsx` |
| Gaps | `#/gaps` | `App.jsx` |
| Proposals | `#/proposals` | `App.jsx` |
| Proposal review | `#/proposal` | `App.jsx` |

Navigation is route-based via URL hash so the prototype works from a simple static file server.

## Relationship to Martenweave Core

Martenweave Core is the Python backend in [`src/modelops_core/`](../src/modelops_core/) and the
owner of the canonical-file registry. The Workbench is an official product surface that visualizes
and interacts with Core services:

- Search results mirror what `martenweave search` and `martenweave query` return.
- Lineage reflects the edges exported by `martenweave build-index --jsonl`.
- Gaps are modeled after `martenweave gaps` and `martenweave gap-report`.
- Proposals mirror `martenweave propose-patch` and `martenweave proposal`.

The current build uses static demo data in `src/data.js` for standalone development. In a packaged
integration, the Workbench reads from the local API (`martenweave serve`) and never stores canonical
truth independently of the `model/` files.

## Known limitations

- This build uses static demo data in `src/data.js`; the live API connection is implemented in later issues.
- No client-side persistence: refreshes reset the UI state.
- No authentication or multi-tenant support.
- No direct SAP connectivity or write-back.
- AI suggestions are mocked; real proposals must be generated and reviewed through Core.
- Mobile layout is supported but not all complex lineage interactions are optimized for small viewports.

## Screenshots

Design QA screenshots are in [`qa/`](qa/):

- `qa/home-desktop.png`
- `qa/home-answered-desktop.png`
- `qa/home-mobile.png`
- `qa/models-desktop.png`
- `qa/object-desktop.png`
- `qa/lineage-desktop.png`
- `qa/gaps-desktop.png`
- `qa/proposal-desktop.png`
- `qa/comparison-home.png`
- `qa/comparison-search-gaps.png`
- `qa/source-implementation-comparison.png`

See [`design-qa.md`](design-qa.md) for the full QA report.

## How to validate changes

```bash
cd frontend
npm install
npm run build
```

If a lint script is added later, also run:

```bash
npm run lint
```

## License

Same as Martenweave Core: MIT.

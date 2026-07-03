# Martenweave UI/UX Direction

**Status:** implementation proposal  
**Date:** 2026-07-01  
**Scope:** local frontend prototype, not the backend/core product boundary

## Executive decision

Adopt **Evidence Workbench**: a compact model workbench with search as the universal entry point
and lineage/impact as contextual lenses.

The direction preserves the Martenweave logo, Inter typography, Phosphor icon language, XYFlow
lineage foundation, canonical-file terminology, and human-controlled proposal workflow. It
replaces the current chatbot-first home and generic card-dashboard composition with a denser,
traceable investigation surface.

The first implementation slice should be **Home/Search**. It is bounded, changes the product's
first impression, and establishes the shared search, evidence, status, and responsive primitives
required by every later screen.

## Scope and evidence

Reviewed:

- `frontend/src/App.jsx`, `frontend/src/data.js`, and `frontend/src/styles.css`;
- all seven documented hash routes and their source-level interactions;
- `frontend/public/martenweave-logo.png` and `assets/logo.png`;
- existing repository QA captures in `frontend/qa/` and `outputs/` as design context;
- the local API in `src/modelops_core/api/app.py`;
- product boundaries in `README.md` and `frontend/README.md`;
- the current live Vite render at 1280 × 720 and 390 × 844.

Current-run evidence:

- desktop:
  [Home](evidence/01-home-current.jpg),
  [Models](evidence/02-models-current.jpg),
  [Object detail](evidence/03-object-current.jpg),
  [Lineage](evidence/04-lineage-current.jpg),
  [Gaps](evidence/05-gaps-current.jpg),
  [Proposals](evidence/06-proposals-current.jpg), and
  [Proposal review](evidence/07-proposal-current.jpg);
- mobile:
  [Home](evidence/08-home-mobile-current.jpg),
  [Models](evidence/09-models-mobile-current.jpg),
  [Lineage](evidence/10-lineage-mobile-current.jpg), and
  [Proposal review](evidence/11-proposal-mobile-current.jpg).

The repository QA images were useful historical context, but are not treated as current-run
evidence. `evidence/01-live-prototype-render-blocker.png` records a superseded parse regression
that was fixed by a concurrent repository commit before final validation.

## Current UI diagnosis

### What is working

1. The prototype covers the right domain workflows: search, model detail, lineage, gaps, and
   proposal review.
2. The proposal diff and explicit approve/request-changes actions correctly communicate that AI
   produces review artifacts rather than silently mutating canonical truth.
3. The visual system is calm: restrained blue, thin borders, limited shadow, Inter typography,
   consistent icons, and no decorative gradients.
4. Object IDs, validation status, owners, mappings, systems, and related gaps are visible rather
   than hidden behind marketing copy.
5. The source includes visible focus treatment and a `prefers-reduced-motion` override.
6. Hash routes are compatible with a static local prototype and are moving toward ID-aware URLs.

### Structural problems

1. **The home page reads as an AI chat product.** “Ask your model layer anything,” the sparkle
   mark, prompt composer, and simulated answer dominate the first screen. This weakens the
   backend-first, deterministic-validation story.
2. **The shell is a familiar SaaS dashboard pattern.** A 228 px sidebar, top bar, large white
   cards, profile menu, notification bell, and “Production” pill make the prototype look hosted
   and multi-user even though it is a local demo.
3. **The investigation trail is fragmented.** Object facts, fields, governance, lineage, gaps,
   impact, and proposals live on separate pages with weak state continuity. Users must repeatedly
   reconstruct what object and evidence they were inspecting.
4. **Impact is not a first-class workflow.** It appears inside proposal review and as backend
   capability, but has no durable investigation surface of its own.
5. **AI and deterministic results are visually too similar.** The search “AI answer” and
   recommendation cards do not make provenance, confidence, provider state, or deterministic
   evidence boundaries explicit.
6. **The object template over-generalizes.** Different object types reuse domain-oriented facts
   and the same field/system content. An Attribute, Mapping, Dataset, Decision, or Proposal needs
   type-specific anatomy.
7. **The prototype is disconnected from the local API.** Counts and workflow states are static,
   while the backend already exposes objects, validation, trace, impact, and proposal operations.
8. **Several controls suggest behavior that is not credible yet.** Notifications, profile,
   environment, export, attach-context, and “New proposal” affordances either do not match the
   local prototype boundary or have no complete behavior.

### Visual and accessibility risks

1. The design uses many 7–10 px labels. That is too small for sustained governance work and will
   fail under zoom, lower-quality displays, and common enterprise accessibility needs.
2. Important metadata is low-contrast and visually subordinate even when it determines trust:
   object ID, validation time, source, rule status, and proposal author.
3. Mobile layouts often remove columns instead of preserving their meaning in a compact row or
   disclosure. Hidden validation or usage facts are not equivalent to responsive reflow.
4. Mobile Lineage presents a wide graph inside a narrow viewport, cropping upstream and downstream
   context to partial edges and tiny nodes. A path list should be the default mobile
   representation; the graph can be an optional landscape view.
5. Animated lineage edges create continuous motion without adding evidence. Animation should only
   identify the active trace.
6. Some icon-only controls need explicit accessible names and touch targets of at least 44 × 44 px.
7. Screenshot review cannot establish keyboard order, screen-reader names, contrast ratios,
   zoom resilience, or live-region behavior. These require implementation testing.

### Current build health

- `npm run build` passes.
- `npm test` passes: 1 test file, 5 tests.
- All seven current routes render without browser console errors at 1280 × 720.
- Home, Models, Lineage, and Proposal Review render without page-level horizontal overflow at
  390 × 844.
- The package defines no lint or typecheck scripts.
- Mobile Lineage technically fits the page but is not practically legible or navigable as a
  graph-first experience.

## Product workflow map

| User intent | Entry | Investigation | Decision/output |
|---|---|---|---|
| Find known model knowledge | Global search or command palette | Result preview with type, ID, status, owner, and source | Open object or copy stable ID |
| Understand a canonical object | Search, model browser, or relation link | Type-specific object workbench | Trace, check impact, review gaps, export |
| Trace source-to-target flow | Object action or Lineage mode | Graph plus ordered path evidence | Open node, mapping, rule, gap, or impact |
| Detect missing knowledge | Gaps queue or dataset/object context | Compare observed evidence with canonical model | Create issue or draft proposal |
| Assess a change | Object action, proposal, or Impact mode | Upstream/downstream paths with severity and reasons | Save investigation or open related proposal |
| Review AI-assisted changes | Proposal queue | Diff, source evidence, validation, risk, approvals | Request changes or approve for ChangeRequest |
| Apply approved changes | ChangeRequest workflow outside initial prototype | Deterministic dry run and approval checks | Audited canonical-file change and index rebuild |

AI may summarize evidence or draft a proposal. It must not appear as an authority, validation
engine, approver, or direct SAP writer.

## Design principles

1. **Evidence before advice.** Every recommendation links to canonical objects, source files,
   validation results, paths, gaps, or decisions.
2. **One investigation context.** Preserve repository, object, query, filters, and selected path
   while users move between detail, lineage, impact, and review.
3. **Deterministic status is visually distinct.** “Validated,” “stale index,” “broken reference,”
   and “dry run passed” use a different treatment from “AI-drafted” or “suggested.”
4. **Compact does not mean tiny.** Use dense rows, alignment, and progressive disclosure; keep
   body text at 14 px and supporting text at 12 px minimum.
5. **Canonical truth stays legible.** Stable IDs, object type, source file, status, owner, and last
   validation remain visible in the workbench header.
6. **Graph and table are peers.** Lineage and impact always offer an ordered, accessible path list.
7. **Review is a decision, not a celebration.** No confetti, glow, or “AI magic.” Approval shows
   the resulting controlled artifact and audit consequence.
8. **Local-first is visible.** Show repository path/name, index freshness, and local/demo state;
   avoid fake online presence, notification, and production-account chrome.
9. **The logo is identity, not decoration.** Preserve the existing mark and wordmark. Let its warm
   tones inform small evidence accents without redesigning it.

## Three visual concepts

### Concept 1 — Compact model workbench

**Layout model**

- 52 px mode rail;
- 48 px top utility bar with logo, repository, universal search, and index state;
- optional 288 px finder pane;
- flexible document/canvas pane;
- 320 px evidence inspector.

```text
[mode rail] [finder] [object, table, diff, or graph] [evidence inspector]
             query    selected context stays stable     sources/actions
```

**Navigation model**

- Primary modes: Search, Models, Lineage, Impact, Gaps, Proposals.
- Back/forward preserves investigation state.
- Object links open in the center pane; related evidence updates the inspector.
- `⌘/Ctrl K` opens universal search and commands.

**Key screens**

- Search result workbench;
- model browser with canonical hierarchy;
- type-specific object detail;
- lineage/impact canvas plus path table;
- gap triage queue;
- proposal diff and approval checklist.

**Interaction patterns**

- keyboard-first result navigation;
- split-pane resizing with sensible defaults;
- inline expansion for evidence and related objects;
- pinned facts and saved investigations;
- no modal for ordinary inspection.

**Motion**

- 120 ms selection and focus transitions;
- 180 ms inspector enter/exit;
- active lineage path draws once, then becomes static;
- no ambient animation.

**Strengths**

- Best fit for expert, repetitive investigation;
- keeps evidence and context visible;
- scales from search to review without changing mental model;
- visually distinctive through density and pane behavior rather than decoration.

**Risks**

- Can feel complex for first-time users;
- pane widths and type-specific detail templates need discipline;
- small screens require a different sequential pattern.

**Implementation cost:** medium-high. The shell is reusable, but `App.jsx` must be decomposed and
screen state made route-aware.

### Concept 2 — Search-first investigation surface

**Layout model**

- dominant persistent search field;
- chronological investigation stream in the center;
- faceted result rail on the left;
- evidence/source drawer on demand.

```text
[facets] [query → grouped results → opened evidence → follow-up] [source drawer]
```

**Navigation model**

- Search history is the primary navigation.
- Results group by canonical objects, physical fields, datasets, gaps, decisions, and proposals.
- Follow-up actions refine scope rather than start a separate chat.

**Key screens**

- search home;
- grouped result stream;
- saved investigations;
- evidence preview;
- compact proposal review launched from a result.

**Interaction patterns**

- query tokens such as `type:Attribute`, `table:KNVV`, `status:gap`;
- scope chips derived from selected results;
- exact-match IDs before semantic suggestions;
- evidence citations expand inline.

**Motion**

- result-group reordering uses a short cross-fade;
- source drawer slides;
- loading uses stable skeleton rows.

**Strengths**

- Lowest learning curve;
- strongest first-run experience;
- excellent for “find and explain” use cases;
- cleanest path to a small first slice.

**Risks**

- Deep model structure and bulk comparison are weaker;
- can drift back toward chatbot conventions;
- long investigations may become a feed that is hard to scan.

**Implementation cost:** medium. Search and routing can reuse current data, but evidence grouping
and query syntax need a clear backend contract.

### Concept 3 — Lineage/impact cockpit without enterprise clutter

**Layout model**

- graph or dependency table occupies the center;
- compact scenario strip across the top;
- selected-node facts on the right;
- affected-object queue below or to the left.

```text
[scenario: change X] [depth] [direction] [risk]
[affected queue] [dependency graph or ordered paths] [selected evidence]
```

**Navigation model**

- Start from an object, field, rule, mapping, or proposal.
- Toggle Trace, Impact, and Compare lenses without leaving the canvas.
- Breadcrumbs represent path and scenario, not page hierarchy.

**Key screens**

- trace explorer;
- change-impact scenario;
- field-level mapping path;
- proposal impact comparison;
- path evidence export.

**Interaction patterns**

- select a node to isolate paths;
- compare current vs proposed graph;
- show “why affected” on every node;
- table/graph parity;
- save a scenario as review evidence.

**Motion**

- path highlighting only after explicit selection;
- affected nodes enter in traversal order;
- reduced motion switches directly to final state.

**Strengths**

- Most distinctive;
- makes Martenweave's trace and impact capability tangible;
- credible for migration design reviews.

**Risks**

- Too specialized as the whole application shell;
- graphs degrade quickly with large models;
- accessibility and mobile cost are high;
- could resemble an enterprise monitoring cockpit if over-instrumented.

**Implementation cost:** high. It needs graph virtualization, path aggregation, accessible table
parity, and stronger trace/impact response contracts.

## Chosen direction: Evidence Workbench

Use Concept 1 as the product shell, take Concept 2's universal search as the entry point, and use
Concept 3 only for the Lineage and Impact lenses.

This is not a visual compromise. It is one stable interaction model:

- search finds the investigation target;
- the workbench keeps canonical facts visible;
- evidence opens beside the target;
- lineage and impact change the center lens;
- gaps and proposals remain linked review artifacts;
- approval produces a controlled next step rather than an invisible mutation.

### Information architecture

| Mode | Primary question | Default representation |
|---|---|---|
| Search | What model knowledge matches this term or question? | Grouped compact rows |
| Models | How is canonical knowledge structured? | Hierarchy + table |
| Lineage | Where did this come from and where does it go? | Graph + path list |
| Impact | What changes if this changes? | Affected list + reasons |
| Gaps | What evidence is missing or inconsistent? | Triage queue |
| Proposals | What changes need human review? | Review queue + diff |

“Home” is not a separate dashboard. Search is the default route and includes recent
investigations, review work, and repository state.

## Visual system

### Brand use

- Keep `frontend/public/martenweave-logo.png` unchanged.
- Use the full mark and wordmark in the expanded shell; use the mark alone in compact mode.
- Do not place the logo inside a generic rounded app-icon tile.
- Use warm brand-derived amber only for evidence attention and gaps, never as a broad gradient.

### Proposed tokens

| Role | Value | Use |
|---|---|---|
| Ink | `#171B22` | Primary text |
| Muted ink | `#5F6875` | Secondary text |
| Canvas | `#F4F3EF` | Workspace background |
| Surface | `#FCFBF8` | Panels and tables |
| Rule | `#DAD7CF` | Dividers and borders |
| Brand plum | `#3A1238` | Logo-adjacent identity and selected mode |
| Action blue | `#245FD6` | Links, focus, primary action |
| Evidence amber | `#A86416` | Gaps and source attention |
| Valid green | `#287A55` | Deterministic pass states |
| Risk red | `#B7473F` | Blocking errors and destructive review |

Rules:

- no generic gradients;
- use plum sparingly for identity/navigation, never as a glowing AI treatment;
- shadows only for floating palette/drawer layers;
- 1 px rules organize most surfaces;
- 6 px control radius, 10 px floating-layer radius;
- 4 px spacing base;
- 14 px body, 12 px supporting text, 11 px uppercase only for short labels;
- use system monospace for IDs, fields, paths, and YAML diffs.

### Core components

- `WorkbenchShell`: mode rail, top utility bar, repository/index state;
- `UniversalSearch`: exact IDs, text, scoped queries, and commands;
- `ResultRow`: type, name, stable ID, status, owner, source, updated time;
- `ObjectIdentity`: type-specific persistent header;
- `FactStrip`: compact canonical facts without card chrome;
- `EvidenceInspector`: sources, validation, ownership, decisions, and related artifacts;
- `StatusTag`: deterministic, draft, stale, suggested, risk, and lifecycle variants;
- `PathList`: accessible lineage/impact alternative;
- `DiffViewer`: canonical-file and field-level views;
- `ApprovalChecklist`: validation, risk, evidence, reviewers, ChangeRequest state;
- `StatePanel`: empty, loading, stale, offline/local API, not found, and blocked states.

## Concrete screen proposal

### Home / Search

**Desktop**

- Top utility bar: logo, repository switcher, index freshness, universal search shortcut.
- Main heading: “Find model knowledge” rather than an AI claim.
- Search accepts names, IDs, SAP tables/fields, source files, people, decisions, gaps, and
  proposals.
- Below the field, show three compact sections:
  - recent investigations;
  - review queue;
  - repository state and validation changes.
- When a query exists, replace these sections with grouped result rows and a right evidence
  preview. Do not append a chat transcript.
- A generated summary may appear above results only when it cites evidence and is labeled
  “Suggested summary,” never “AI answer.”

**Example result**

```text
Attribute  TAX_NUMBER                 Gap · owner Priya Nair
ATTR-BP-TAX-NUMBER                   3 endpoints · 1 open proposal
Matched: KNVV.STCD1, “tax number,” Proposal PP-27
```

### Models overview

- Finder pane offers hierarchy, type, status, owner, and domain filters.
- Center uses a compact table, not cards.
- Columns: name/ID, type, parent/context, validation, owner, updated.
- Row expansion shows definition and immediate relationships without navigation.
- “Structure” toggles between hierarchy and table; it is not a separate decorative view.
- Bulk selection is read-only initially: compare, export IDs, or open impact. No bulk mutation.

### Object detail workbench

- Persistent header: type, name, stable ID, status, source file, last validation, owner.
- Type-specific main sections:
  - Attribute: meaning, usages, endpoints, value lists, rules;
  - FieldEndpoint: system, table/field, context, physical type, mappings;
  - Mapping: source, target, transform, rules, lineage;
  - Dataset: source, profile, drift, gaps;
  - Decision: status, rationale, supersedes, affected objects;
  - Proposal: diff, evidence, impact, approvals.
- Evidence inspector always exposes provenance and related artifacts.
- Fields, relationships, lineage, gaps, and decisions use local subnavigation, but identity and
  validation facts never disappear.
- Primary actions: Trace, Impact, Review related gaps. Export is secondary.

### Lineage

- Center defaults to a bounded graph for the selected object and depth.
- Left pane lists ordered paths and supports source/target/type filtering.
- Right inspector explains the selected node and “why this edge exists.”
- Every edge exposes relationship type and source evidence.
- Toggle `Graph | Paths`; Paths is a complete accessible representation, not a fallback message.
- Animated edges are off by default. Selecting “Trace this path” animates once.
- Large graphs collapse repeated nodes into groups and disclose counts.

### Impact

- Entry requires a concrete object, field, rule, mapping, or proposal.
- Header states the scenario: “If `ATTR-BP-TAX-NUMBER` changes…”
- Center groups effects by direct, downstream, validation, and review impact.
- Each affected row includes depth, relationship, severity, and “why affected.”
- Toggle current vs proposed state for proposal impact.
- Action: attach impact snapshot to a proposal or ChangeRequest. Do not imply write-back.

### Gaps workflow

- Queue columns: severity, gap, observed evidence, expected model fact, owner, proposal state.
- Group by model object, dataset/import session, or detection rule.
- Expanding a row shows the source sample/profile, expected canonical target, validation code,
  and related decisions.
- Actions:
  - open related object;
  - assign owner;
  - create issue draft;
  - draft proposal from evidence.
- “Draft proposal” creates or opens a review artifact. It is not “Fix with AI.”
- The right inspector shows queue counts and filters, not a recommendation card.

### Proposal review

- Sticky decision header: proposal status, risk, validation, author/provider, reviewers,
  ChangeRequest state.
- Main view:
  1. reason and linked evidence;
  2. canonical-file diff;
  3. deterministic validation results;
  4. impact paths;
  5. reviewer notes and activity.
- Keep side-by-side and unified diff modes.
- Approve wording:
  - low/medium: “Approve proposal” and explain the next controlled step;
  - high risk: “Approve for ChangeRequest” until an approved ChangeRequest exists.
- Confirmation names changed files, validation state, audit event, and whether the index will
  rebuild. Never say that SAP will be updated.
- Reject/request changes requires a reason.

### Command/search palette

- Shortcut: `⌘K` on macOS, `Ctrl+K` elsewhere, `/` when focus is not in an input.
- Sections:
  - exact matches;
  - objects and fields;
  - gaps and proposals;
  - commands.
- Supported scoped syntax:
  - `id:ATTR-BP-TAX-NUMBER`;
  - `type:Mapping TAX_NUMBER`;
  - `table:KNVV`;
  - `status:gap owner:"Priya Nair"`.
- Commands are non-mutating by default: Open, Trace, Check impact, Copy ID, Review proposal.
- “Draft proposal” is allowed only when evidence is selected and opens a review form.
- Show recent queries locally; do not imply cloud history.

## Empty, loading, stale, and error states

| State | Required behavior |
|---|---|
| Empty repository | Explain canonical files are the source; link to `init`/example guidance |
| No index | State “Generated index unavailable”; show exact build command |
| Stale index | Keep canonical facts readable; mark search/lineage as stale and offer rebuild guidance |
| No search results | Preserve query; suggest removing specific filters or searching exact ID |
| No gaps | Say which dataset/model scope was checked and when |
| No proposals | Explain that proposals are review artifacts, not required noise |
| Loading | Stable row skeletons with labels; avoid spinners replacing the whole workspace |
| Object not found | Show requested ID, repository, and nearest exact matches |
| Local API unavailable | Keep static demo mode explicit; do not show “Production” |
| Validation blocked | Pin error count and codes; link to affected canonical files |
| Approval blocked | Explain missing reviewer, ChangeRequest, validation, or risk requirement |
| Provider unavailable | Disable AI drafting only; deterministic search/validation remains available |

State changes that occur after an action use a polite live region. Errors keep user input and offer
a recovery action.

## Responsive behavior

### ≥ 1280 px

- mode rail + finder + center + evidence inspector;
- center minimum width 560 px;
- inspector may be pinned;
- tables retain all critical columns.

### 900–1279 px

- finder can collapse to a filter drawer;
- inspector becomes a 360 px overlay drawer;
- identity and validation stay pinned above content.

### 680–899 px

- compact top bar and icon rail;
- one main pane at a time;
- selected context persists in a compact header;
- tables become labeled two-line rows, not truncated desktop grids.

### < 680 px

- bottom mode navigation for Search, Models, Gaps, Proposals, and More;
- search/results/detail use a sequential push navigation;
- sticky context header shows type, name, status, and back action;
- lineage defaults to Path List; graph is an explicit landscape/full-screen option;
- proposal decision bar is sticky but does not cover diff content;
- no hover-only controls;
- minimum 44 px interactive targets;
- metadata moves into labeled disclosure rows rather than disappearing.

Test at 1440 × 1000, 1024 × 768, 768 × 1024, 390 × 844, 320 × 568, 200% zoom, and with long
IDs/localized labels.

## Motion rules

| Interaction | Motion | Reduced motion |
|---|---|---|
| Row selection | 120 ms background/border | Immediate |
| Inspector open | 180 ms translate + fade | Immediate |
| Search result update | 120 ms opacity | Immediate |
| Active lineage trace | Draw once, ≤ 450 ms | Final highlighted path |
| Approval result | Inline status transition, ≤ 180 ms | Immediate text/status |
| Loading | Static skeleton with subtle pulse | Static skeleton |

No parallax, ambient glow, looping graph motion, celebratory approval animation, or animated
backgrounds.

## Implementation phases

### Phase 0 — Lock the trustworthy baseline

**Cost:** less than one day

- add `lint` and retain the lightweight test script;
- retain the current build/test gate and fresh route captures;
- remove or label inert/fake hosted-app controls;
- establish fixture states for valid, stale, empty, error, and high-risk review.

**Exit:** build and tests stay green, lint is automated, and the supported route/state matrix is
explicit.

### Phase 1 — Home/Search slice and shared tokens

**Cost:** 2–4 days

- introduce semantic tokens and minimum type sizes;
- compact the shell while preserving the logo;
- replace chatbot-first home with `UniversalSearch`;
- add grouped rows, exact-ID priority, recent investigations, review queue, and state panels;
- preserve query, filters, and selected result in the URL;
- connect objects/validation to the local API or a typed fixture adapter.

**Exit:** a user can find an object, field, gap, decision, dataset, owner, or proposal and understand
why it matched without entering a chat flow.

### Phase 2 — Object workbench

**Cost:** 4–6 days

- split `App.jsx` into routes, screen modules, and shared components;
- add type-specific object templates;
- introduce persistent identity/fact strip and evidence inspector;
- connect object, validation, trace, and impact endpoints;
- implement loading, stale, not-found, and API-unavailable states.

**Exit:** a selected result remains in context across facts, fields, relationships, governance,
lineage, gaps, and impact.

### Phase 3 — Lineage, Impact, and Gaps

**Cost:** 6–10 days

- add graph/path parity and relationship evidence;
- add a first-class impact mode;
- replace mobile graph overlay with path-first navigation;
- connect gap-report/import-session data through a defined API contract;
- add large-graph grouping and performance tests.

**Exit:** users can explain every path and every impact row from deterministic relationships.

### Phase 4 — Proposal and approval workflow

**Cost:** 4–7 days

- connect proposal detail, validate, dry-run, risk, and ChangeRequest states;
- add approval checklist and blocked reasons;
- make high-risk wording match the backend approval gate;
- confirm changed files, audit event, and index behavior;
- add keyboard and screen-reader review of diff/decision flows.

**Exit:** the UI never suggests that an AI suggestion or button click bypasses human approval,
ChangeRequest policy, validation, or audit.

## Affected files

### Existing files likely to change

| File | Planned change |
|---|---|
| `frontend/src/App.jsx` | Decompose route/screen monolith and fix route state |
| `frontend/src/styles.css` | Replace page-specific compressed CSS with semantic tokens/layout |
| `frontend/src/data.js` | Move to typed fixture adapter; retain demo states |
| `frontend/src/main.jsx` | Add providers/error boundary if needed |
| `frontend/package.json` | Add lint/test/typecheck scripts and dependencies only when justified |
| `frontend/README.md` | Update routes, demo-state contract, and validation instructions |
| `frontend/design-qa.md` | Replace historical QA with fresh evidence |
| `frontend/public/martenweave-logo.png` | Preserve unchanged |
| `src/modelops_core/api/app.py` | Add only missing read contracts/search/gaps/change-state fields |
| `tests/test_api.py` | Cover any API additions or response changes |

### Proposed frontend modules

```text
frontend/src/
  app/
    routes.jsx
    WorkbenchShell.jsx
  components/
    UniversalSearch.jsx
    ResultRow.jsx
    ObjectIdentity.jsx
    FactStrip.jsx
    EvidenceInspector.jsx
    PathList.jsx
    DiffViewer.jsx
    ApprovalChecklist.jsx
    StatePanel.jsx
  screens/
    SearchScreen.jsx
    ModelsScreen.jsx
    ObjectScreen.jsx
    LineageScreen.jsx
    ImpactScreen.jsx
    GapsScreen.jsx
    ProposalsScreen.jsx
    ProposalReviewScreen.jsx
  data/
    apiClient.js
    fixtureAdapter.js
  styles/
    tokens.css
    base.css
    workbench.css
```

Do not add a large component framework for this slice. The existing React, Phosphor, and XYFlow
stack is sufficient.

## Backend/API contract gaps to resolve before production integration

1. Add indexed search with query, type, status, owner, and pagination instead of scanning every
   canonical file on each frontend query.
2. Expose repository/index freshness and validation timestamp in one compact status response.
3. Define gap-list/gap-detail endpoints tied to import session, dataset evidence, validation code,
   owner, and proposal state.
4. Return proposal operations, evidence, risk result, reviewers, linked ChangeRequest, dry-run
   summary, and audit consequence in a review-oriented shape.
5. Preserve stable object IDs in all trace/impact nodes and include relationship/evidence reasons.
6. Keep mutations local, explicit, auditable, and subject to existing risk/ChangeRequest gates.

## Risks and mitigations

| Risk | Mitigation/validation |
|---|---|
| Workbench overwhelms new users | Default to search; progressive disclosure; five-task usability test |
| Compact UI becomes unreadable | Enforce type minimums, 44 px targets, 200% zoom test |
| Graph becomes visual noise | Path list parity, depth limits, grouping, explicit trace animation |
| AI looks authoritative | Label suggestions, cite evidence, separate deterministic status tokens |
| UI implies hosted production | Show local/demo state and repository/index status; remove fake account chrome |
| Object templates drift | Schema-driven type anatomy and contract tests |
| Static fixtures diverge from core | Adapter boundary and shared API fixtures |
| Approval wording bypasses policy | Test high-risk proposal with and without approved ChangeRequest |
| URL loses investigation context | Encode object, lens, query, filters, depth, and selected path |
| Large models hurt performance | Pagination, virtualization, bounded graph queries, performance budget |
| Existing logo loses clarity | Preserve asset and verify at 24, 32, and 40 px |

## Validation plan

### Functional

- Search exact stable IDs, names, KNVV fields, owners, decisions, gaps, and proposals.
- Open a result, trace it, inspect impact, return to unchanged search state.
- Expand a gap, inspect evidence, draft a proposal, and return to the same queue position.
- Review low-, medium-, and high-risk proposals.
- Verify high-risk approval cannot bypass an approved ChangeRequest.
- Verify AI/provider failure does not break deterministic search or validation.

### Visual/responsive

- Compare every target route at the defined desktop/tablet/mobile viewports.
- Check long object IDs, long names, empty sections, 100+ results, and 100+ graph nodes.
- Verify no horizontal page overflow; allow scoped diff/table scrolling when labeled.
- Verify logo rendering and no stretched/cropped assets.

### Accessibility

- Keyboard-only route, search, filtering, graph/path, diff, and decision flows.
- Visible focus with no obscured element.
- Semantic headings, landmarks, table/list structures, labels, and live regions.
- Automated contrast and accessible-name checks plus manual screen-reader review.
- 200% and 400% zoom/reflow checks.
- Reduced-motion check and no information communicated by color alone.

### Product truth

- Canonical files are presented as source of truth.
- Generated indexes are marked rebuildable and may be stale.
- Validation is deterministic and distinguishable from suggestions.
- AI produces proposals or summaries only.
- Human review and ChangeRequest gates remain explicit.
- No direct SAP write-back is shown or implied.

## Validation performed for this proposal

| Check | Result |
|---|---|
| Live prototype launch | Passed on Vite at `127.0.0.1:5173` |
| Frontend production build | Passed; 4,732 modules transformed |
| Frontend tests | Passed; 1 file and 5 tests |
| Frontend lint | Not available; no package script |
| Frontend typecheck | Not available; JavaScript prototype |
| Desktop visual review | All seven routes captured and inspected at 1280 × 720 |
| Responsive review | Home, Models, Lineage, and Proposal Review inspected at 390 × 844 |
| Page-level horizontal overflow | None detected on the four mobile routes checked |
| Browser console | No warnings or errors after route review |
| Accessibility review | Source/screenshot risk review only; no compliance claim |
| Backend tests | Not run; backend was not changed |
| Brand preservation | Existing logo retained; no replacement proposed |
| Governance boundary | Proposal explicitly preserves deterministic validation and human approval |

## Audit step health

1. **Open local prototype — healthy.** The app builds, launches, and exposes all documented routes.
2. **Home/Search — functional, directionally weak.** Search and suggestions work, but the
   chatbot-style composer dominates the product's first impression.
3. **Models/Object — functional, structurally sound.** Search, filters, stable IDs, validation,
   owners, and field facts are visible; the generic object template needs type-specific anatomy.
4. **Lineage/Impact — desktop usable, mobile weak.** The desktop graph is calm and readable.
   Mobile shows only a narrow crop of the graph and has no path-list equivalent. Impact remains a
   proposal tab rather than a first-class investigation mode.
5. **Gaps — functional, evidence could be stronger.** Severity, owner, proposal state, and source
   direction are scannable; observed evidence and expected canonical facts need a clearer compare
   treatment.
6. **Proposal/Approval — strongest current screen.** Diff, risk, validation, evidence, reviewers,
   and explicit human actions are visible. High-risk wording should lead to the ChangeRequest gate
   rather than imply immediate application.

No GitHub issues were created. The worktree already contains unrelated in-progress changes and the
requested deliverable is a proposal first; issue creation should follow direction approval.

## Recommended next implementation slice

Implement **Phase 1: Home/Search** only.

Slice acceptance criteria:

1. Replace the chat composer and simulated answer with a universal evidence search.
2. Keep the logo and existing brand identity.
3. Show recent investigations, review queue, and repository/index state in compact rows.
4. Group results across objects, fields, mappings, datasets, gaps, decisions, owners, and proposals.
5. Prioritize exact IDs and deterministic matches; label generated summaries as suggestions with
   evidence.
6. Preserve query/filter/selection in the URL.
7. Deliver explicit empty, stale-index, API-unavailable, loading, and error states.
8. Pass build, lint/test scripts added for the slice, keyboard review, reduced-motion review, and
   desktop/mobile visual checks.

This slice proves the product's distinctive interaction model before the more expensive object,
lineage, impact, and approval work.

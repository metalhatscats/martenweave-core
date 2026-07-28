# Martenweave Workbench — Product Redesign Brief

## Customer promise

Martenweave is the local decision workspace for migration model knowledge. It helps a migration
team move from an uncertain field, file, or rule to an evidence-backed, human-approved change
without losing traceability or control of canonical files.

The Workbench should feel like a calm mission-control surface, not a generic dashboard or a
collection of disconnected registry pages. The user must always be able to answer:

1. What needs attention now?
2. Why does it matter and what evidence supports it?
3. What safe, governed next step can I take?

## Product-owner audit

The current Workbench provides a broad and valuable feature surface: workspace, global model
search, object detail, lineage, gap triage, proposals, reports, changelog, settings, repository
switching, local imports/exports, command palette, activity, and keyboard shortcuts. It also
keeps the right local-first and approval-first boundaries.

The main experience issue is not missing capability; it is fragmentation. Users must translate
between a ledger, a separate graph, a gaps list, and a proposal review before they can understand
or act on a migration risk. Pages repeat the same header and card grammar, while the important
workflow state (source → evidence → decision → approval) is not persistent across those moves.

### High-impact findings

| Finding | Customer impact | Redesign response |
| --- | --- | --- |
| The home screen starts with a broad assistant, a ledger, and a utility rail competing for attention. | The first useful task is unclear to a migration analyst. | Start with a readiness queue and one recommended next decision. |
| Object detail, lineage, gaps, and proposals break the investigation into separate destinations. | Context and confidence are lost during a high-risk review. | Make the selected object and its evidence trail persistent across investigation views. |
| High-risk gaps expose a next action, but the evidence and downstream effect are not visible at the decision point. | Users need to route-hop before they can confidently create or review a proposal. | Put evidence, impact, owner, and proposed action in one decision briefing. |
| Proposal review has the strongest governance controls, but its relationship to the initiating gap and canonical evidence is secondary. | Approval can feel like a document review rather than an informed decision. | Make the initiating signal and the full evidence chain primary in the review screen. |
| Reports, history, settings, and imports are valuable support work but currently carry the same visual weight as the critical decision flow. | The product looks larger and less focused than its local-first MVP purpose. | Keep these as supporting surfaces reachable from the mission flow and command palette. |

## New information architecture

The new navigation uses five customer jobs rather than a feature inventory:

| Customer job | Primary surface | Existing capability retained |
| --- | --- | --- |
| Orient | **Readiness queue** | Workspace summary, validation, import status, scorecard, activity |
| Investigate | **Evidence atlas** | Search, object detail, source evidence, coverage, lineage, impact |
| Resolve | **Resolution workspace** | Gaps, issue drafting, import profiling, proposal drafting |
| Approve | **Change briefing** | Proposal validation, diff, reviewers, ChangeRequest, apply/reject controls |
| Prove | **Outputs & history** | Reports, exports, changelog, audit log, comparison, settings |

Models, lineage, gaps, and proposals remain direct deep links so current API capabilities and
existing bookmarked routes continue to work. The redesign changes how they are framed and linked,
not the Core boundary or canonical workflow.

## Core customer workflow

```text
Discover signal → understand evidence → choose resolution → validate proposal → human approval → prove outcome
```

### 1. Orient: readiness queue

The landing screen shows only work that can advance: validation blockers, unresolved gaps,
unreviewed proposals, stale index status, and import work. Each queue item shows severity, owner,
confidence, a compact evidence trail, and exactly one next action. A contextual `Today’s decision`
panel prioritizes the highest-value item instead of presenting generic KPIs.

### 2. Investigate: evidence atlas

Opening an item preserves the selected canonical object as the centre of the screen. Its upstream
source field, dataset evidence, mapping, validation coverage, downstream impact, owner, and related
gap appear in an interactive relationship map with a readable inspector. The user can move from a
source field to a proposal without re-searching or rebuilding context.

### 3. Resolve: resolution workspace

The gap view turns a finding into a decision package. It makes the source mismatch, affected model
object, suggested mapping/rule, owner, evidence freshness, and impact explicit. The primary action
creates a reviewable proposal; it never writes canonical files.

### 4. Approve: change briefing

Proposal review becomes an approval-grade brief. It keeps the initiating gap, evidence trail,
proposed canonical delta, deterministic checks, impacted objects, reviewer roles, and the reason
for the change together. `Approve with note`, `Request changes`, and `Reject` are explicit,
capability-aware decisions that retain the existing approval gates.

### 5. Prove: outputs and history

Reports and history are the evidence after a decision. They retain existing generated artifacts,
assessment comparison, export, and local audit behaviour, but are framed as the proof of model
health and applied change rather than a separate utility dashboard.

## Screen set

| Screen | Primary question | Critical interactions |
| --- | --- | --- |
| Readiness queue | What needs attention next? | Filter, open item, create proposal, resume import, inspect validation state |
| Evidence atlas | What is this object connected to and can I trust it? | Select a node, trace source/target, inspect evidence, open impact, create proposal |
| Resolution workspace | What is the smallest safe change that resolves this gap? | Review evidence, link issue, draft proposal, inspect assumptions |
| Change briefing | Is this change ready for human approval? | View diff, validate, comment, request changes, approve, apply through existing gates |
| Catalog | Can I find an object quickly? | Search, filters, open an object into the atlas |
| Outputs & history | Can I demonstrate the model state and decision record? | Generate/download reports, compare assessments, inspect audit events |
| Local workspace | Is the local repository healthy and correctly bound? | Open/create repository, validation, index/recovery guidance, local settings |

## Interaction standards

- Keep the current API capability modes visible: read-only, review, full, unavailable, stale, and
  AI-unavailable. Never render an actionable control as if it will mutate when Core will block it.
- Preserve hash routes and deep links for every current screen. Add the new mission screens as
  first-class routes rather than hiding existing features behind client-only state.
- Give each high-risk item a single next action; secondary actions live in a compact overflow or
  inspector, not a row of competing buttons.
- Keep the selected object, its route, and a concise breadcrumb of evidence as the user moves from
  gap to proposal. No copy/paste or repeated global search should be necessary.
- Use accessible native buttons, visible focus, colour-plus-text severity signals, keyboard command
  access, and responsive layouts that move inspectors below the primary decision surface on narrow
  screens.
- Use generated output only as a disposable view. The UI remains a client of the local API and
  canonical files remain the source of truth.

## Visual system direction

Three visual directions were generated from an audit of the current Workbench:

1. **Change briefing** — strong approval-grade decision page with a calm dark navigation shell.
2. **Evidence atlas** — field-journal relationship map built around a selected canonical object.
3. **Migration command centre** — a readiness queue with a clear Discover → Understand → Resolve
   → Approve journey.

The selected direction should become the source visual target for all screens. The other two are
not discarded: their workflow patterns become supporting views in the selected system so the
product stays coherent from first signal to approved change.

## Definition of a successful redesign

A first-time SAP migration analyst can open a local model repository, see the most urgent gap,
understand its source and downstream consequence, create or review a proposal, and reach the
existing human approval gate without needing to learn the underlying file structure or navigate
between unrelated screens. A data steward can still inspect evidence, ownership, history, reports,
and local repository safety at every point.

# Martenweave product audit — 2026-07-02

## Flow

1. **Home / model intelligence — Needs redesign**
   - Strength: consistent brand, clear hierarchy, useful recent objects and activity.
   - Issue: the AI prompt dominates the first screen even though the product is a model workbench.
   - Issue: import, export, reports, shortcuts, and command navigation are absent.
   - Issue: attachment, context, repository, and notification controls are visibly disabled.
   - Accessibility risk: disabled controls expose explanations only through `title`, which is weak for
     keyboard and touch users.

2. **Global model search — Functional with layout issues**
   - Strength: realistic canonical object results, type tabs, status metadata, and useful filtering.
   - Issue: the current laptop viewport clips long content and the proposal tab/result context.
   - Issue: search is duplicated between the top bar and page without a shared command model.
   - Accessibility risk: icon-only submit and clear actions need explicit accessible names.

3. **Lineage — Visually clear but underpowered**
   - Strength: source/transformation/canonical/target legend and node inspector are appropriate.
   - Issue: the graph lacks dataset, gap, decision, evidence, and proposal layers required by the brief.
   - Issue: impact scope and traversal depth are not visible.
   - Accessibility limit: graph keyboard navigation and non-visual relationship summaries require
     direct interaction testing beyond screenshots.

4. **Gaps — Actionable foundation, incomplete workflow**
   - Strength: severity, impacted object, source-to-target path, linked proposal, and timestamps are
     visible.
   - Issue: status coverage is incomplete and object/source/status filters are missing.
   - Issue: laptop-width content clips on the right, weakening the review rail and actions.
   - Issue: gaps without proposals should offer a direct “create proposal” action.

5. **Proposal review — Strongest current screen**
   - Strength: change diff, risk, validation, linked gap, reviewers, notes, and human approval are clear.
   - Issue: request-changes and approval outcomes are transient and do not update visible workflow state.
   - Issue: export and shortcut support are absent.
   - Accessibility limit: focus return and keyboard-only dialog behavior require interaction testing.

6. **Object detail — Useful but missing evidence depth**
   - Strength: ownership, lifecycle, validation health, fields, systems, and open gaps are well organized.
   - Issue: source evidence, dataset coverage, validation rule detail, downstream impact, and proposals
     are not all available in one investigation view.
   - Issue: Export is disabled, violating the no-dead-primary-actions acceptance criterion.

## Design decision

Preserve the existing logo, Inter typography, blue/navy palette, semantic status colors, compact sidebar,
and table-first visual language. Reframe the home screen as an investigation cockpit and add realistic
import/export, command palette, keyboard shortcuts, evidence, and workflow states without introducing a
generic admin dashboard or chatbot.

## Evidence limits

Screenshots establish visible hierarchy, responsive clipping, and available controls. They do not prove
screen-reader quality, complete keyboard traversal, focus restoration, or download behavior; those must
be tested after implementation.

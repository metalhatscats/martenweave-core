# Work Canvas design QA — 2026-08-24

## Findings

No actionable P0, P1, or P2 differences remain for the selected minimal Work Canvas direction.

- [P3] The implementation has four decision groups instead of the three shown in the visual reference.
  This is an intentional data-driven difference: the live customer file produces duplicate-header,
  unmodeled-column, missing-endpoint, and missing-owner evidence. Collapsing those groups would hide
  a deterministic finding.
- [P3] The implementation removes the reference's free-form command composer from the first viewport.
  Search and commands remain in the global top bar, while the evidence case keeps one primary action.
  This preserves the requested minimal product hierarchy and avoids presenting a generic chatbot.

## Verified visual contract

- 64 px icon rail, thin top bar, one continuous white decision canvas, and a contextual right drawer.
- Large outcome-led heading with the real decision count from the current evidence case.
- Actual source filename, persisted-run provenance, SHA-256 prefix, and deterministic rule codes.
- Restrained green for verified/local state and amber for unresolved evidence; no ornamental gradients.
- One governed next move; canonical mutation remains separate from assessment and proposal creation.

## Interaction and product checks

- Readiness queue selection updates the contextual evidence drawer.
- `Review proposed change` opens the persisted proposal rather than demo data.
- Proposal operations render as reviewable key/value evidence rather than raw JSON.
- The live Validation tab completes once, reports `All checks passed`, and resolves repository refs.
- The packaged Workbench establishes a local `HttpOnly`, `SameSite=Strict` mutation session; the
  standalone Local API still supports explicit token-protected mutations.
- Approval remains a named human action; this QA run did not approve or apply the inferred proposal.
- Frontend unit and interaction tests: 67 passed. Production build: passed.

## Comparison record

- Selected reference: `qa/audit-2026-08-24/selected-work-canvas-reference.png`
- Verified implementation: `qa/audit-2026-08-24/readiness-desktop.png`
- Same-input comparison: `qa/audit-2026-08-24/design-comparison.png`
- Comparison viewport: both panels normalized to 1425 x 891.
- Live state: local SAP BP Customer migration workspace generated from `customer_messy.csv`.

## Iteration history

1. Replaced the dashboard/card-heavy home with the evidence-case Work Canvas.
2. Grouped 14 live findings into four decisions and moved selected evidence into a context drawer.
3. Corrected proposal validation to use canonical repository context.
4. Added a secure local Workbench mutation session and removed an unstable mutation-hook loop.
5. Re-ran the selected-reference comparison and retained only truthful data-driven deviations.

final result: passed

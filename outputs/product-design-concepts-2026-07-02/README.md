# Martenweave redesign directions

## 1. Control Desk

Best for high-volume triage and operations. It makes imports, validation health, gaps, proposals, and
evidence immediately visible, but it risks reading like a conventional enterprise dashboard.

## 2. Evidence Canvas

Best for lineage investigation and relationship comprehension. It is the most visually distinctive
direction, but implementing its full three-pane graph workspace would consume more of the first vertical
slice and leave less room for complete import/export and review workflows.

## 3. Model Ledger — recommended

Best fit for Martenweave's canonical-files-as-truth product model. It combines a compact object ledger,
source evidence, validation, coverage, impact, gaps, proposals, shortcuts, import status, and safe human
approval in one coherent workbench. It also evolves the current table-first prototype without discarding
its strongest existing screens.

## Recommendation

Select **3. Model Ledger** for the implementation baseline, then use the Evidence Canvas relationship
model for the dedicated Lineage route. This combination best satisfies the acceptance criteria while
remaining distinctive and feasible as a complete product-quality vertical slice.

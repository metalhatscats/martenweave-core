# Public Demo Narrative

A realistic synthetic scenario that demonstrates Martenweave value end-to-end.

## Story: Customer Data Migration

Acme Corp is migrating customer master data to a new system. They have:
- A legacy CSV export (`customers_legacy.csv`) with 40 columns
- A target SAP S/4HANA system with tables KNVV, KNB1, KNVP, BUT000
- No unified data dictionary

## Demo Steps

1. **Import and profile**
   ```bash
   martenweave import-model-sheet ./customers_legacy.csv --repo ./acme-model
   ```
   → Profiles dataset, creates inferred entities and attributes.

2. **Validate gaps**
   ```bash
   martenweave validate --repo ./acme-model
   ```
   → Shows missing owners, unmapped fields, context_category errors.

3. **Build index and trace**
   ```bash
   martenweave build-index --repo ./acme-model --jsonl
   martenweave impact ATTR-CUST-SALES-CUSTOMER-GROUP --repo ./acme-model
   ```
   → BFS traversal shows affected Mappings, FieldEndpoints, ValueLists.

4. **Analyze coverage**
   ```bash
   martenweave analyze --repo ./acme-model
   ```
   → Reports orphan fields, ownership gaps, rule coverage, unresolved risks.

5. **Propose patch**
   ```bash
   martenweave propose-patch --from ./stakeholder-note.md --repo ./acme-model
   ```
   → AI-assisted PatchProposal for missing AttributeUsages and ValueLists.

6. **Review and apply**
   ```bash
   martenweave proposal show PROP-2026-001 --repo ./acme-model
   martenweave proposal apply PROP-2026-001 --repo ./acme-model --apply
   ```
   → Human review, validation, atomic apply with audit log.

7. **Export scorecard**
   ```bash
   martenweave health --repo ./acme-model --json
   ```
   → Health score, coverage metrics, readiness summary.

## Why This Matters

Martenweave is not a data dictionary. It is a **governed model knowledge layer**:
- Traceability: every attribute links to physical fields and business context
- Governance: ownership, validation, and approval gates
- Readiness: coverage analysis shows what is ready for implementation
- Safety: AI proposes, humans approve, the system records

## Screenshots / Terminal Captures Needed

- `martenweave validate` output (rich tables)
- `martenweave impact` graph (text or rendered)
- `martenweave analyze` summary
- `martenweave health --json` scorecard
- PatchProposal diff view

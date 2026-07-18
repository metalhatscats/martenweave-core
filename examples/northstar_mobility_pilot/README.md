# Northstar Mobility Group — Synthetic Pilot

A fully fictional, fully synthetic multi-domain SAP S/4HANA transformation pilot for
**Northstar Mobility Group**, an invented vehicle leasing and mobility services
company. The pilot migrates four fictional legacy systems — **Northstar CRM**,
**Voyager ERP**, **Freightlink TMS**, and **LedgerPro FI** — to **SAP S/4HANA**.

Everything in this repository is invented: all companies, people, systems,
identifiers, and data rows are synthetic, and every email address uses the reserved
`example.com` domain. No real company names, personal data, or secrets are present.

The repository intentionally contains a set of realistic pilot problems (listed
below) so that validation, gap detection, ownership/readiness reporting, and
cross-domain impact analysis have something meaningful to surface.

## Fictional participants

| ID | Name | Role | Email |
|---|---|---|---|
| `PERSON-MIGRATION-LEAD` | Alex Novak | Migration Lead | alex.novak@example.com |
| `PERSON-SOLUTION-ARCHITECT` | Priya Raman | Solution Architect | priya.raman@example.com |
| `PERSON-CUSTOMER-STEWARD` | Sam Delgado | Customer Data Steward | sam.delgado@example.com |
| `PERSON-SUPPLIER-STEWARD` | Morgan Chen | Supplier Data Steward | morgan.chen@example.com |
| `PERSON-OTC-PROCESS-OWNER` | Jordan Weiss | Order-to-Cash Process Owner | jordan.weiss@example.com |
| `PERSON-INTEGRATION-DEVELOPER` | Casey Kim | Integration Developer | casey.kim@example.com |
| `PERSON-GOVERNANCE-REVIEWER` | Robin Taylor | Governance Reviewer | robin.taylor@example.com |

## Domain map

Seven connected domains, each with its own `MigrationObject`:

| Domain | Scope | Legacy source | SAP anchors |
|---|---|---|---|
| `DOMAIN-BP-CUSTOMER` | Business Partner & Customer | Northstar CRM | BUT000, KNVV |
| `DOMAIN-SUPPLIER` | Supplier | Voyager ERP | LFA1, LFB1 |
| `DOMAIN-MATERIAL` | Material / Product | Voyager ERP | MARA |
| `DOMAIN-SALES` | Sales (Order-to-Cash) | Northstar CRM | VBAK, VBAP |
| `DOMAIN-PROCUREMENT` | Procurement (Procure-to-Pay) | Voyager ERP | EKKO, (EKPO wave 2) |
| `DOMAIN-LOGISTICS` | Logistics (Delivery & Transport) | Freightlink TMS | LIKP, LIPS |
| `DOMAIN-FINANCE` | Finance (FI Documents) | LedgerPro FI | BKPF, BSEG |

How the domains connect:

- **`ATTR-SHARED-PAYMENT-TERMS`** (home: Supplier, LFB1-ZTERM) is reused via
  `AttributeUsage` on the purchase order header (EKKO-ZTERM, Procurement) and the
  accounting document item (BSEG-ZTERM, Finance). Changing it visibly impacts all
  three domains — see `RISK-SHARED-PAYMENT-TERMS-IMPACT` and
  `BR-PAYMENT-TERMS-INHERITANCE`.
- **`ATTR-SHARED-CUSTOMER-CREDIT-LIMIT`** (home: Customer, KNVV-KLIMK) is reused via
  `AttributeUsage` in the sales order header (credit check, Sales) and the accounting
  document item (open receivables, Finance) — see `BR-CREDIT-CHECK-ORDER-BLOCK`.
- **`MAP-VOYAGER-MATERIAL-TO-VBAP-MATNR`** is an explicit cross-domain mapping: the
  material master key (Material domain) feeds the sales order item (Sales domain).

## Intentional pilot problems

All of these live in the data and metadata; canonical validation stays clean
(`is_valid: true`, zero ERRORs).

1. **Missing mapped column** — `data/samples/northstar_crm_sales_orders.csv` ships
   `order_total` instead of the model-mapped `net_value` column.
   `MAP-CRM-ORDER-NET-VALUE-TO-VBAK-NETWR` is blocked. Tracked in
   `ISS-SALES-ORDERS-MISSING-NET-VALUE`; visible as an `UNMODELED_DATASET_COLUMN`
   gap for `order_total`.
2. **Invalid codes** — `data/samples/voyager_materials.csv` ships an unmodeled
   `s4_material_type` column containing the codes `FQ`, `ZZ`, and `QQ`, which are
   not in `VLIST-S4-MATERIAL-TYPES` and have no entry in
   `VMAP-MATERIAL-TYPE-LEGACY-TO-S4`. Tracked in `ISS-MATERIAL-INVALID-TYPE-CODES`;
   the column shows as an `UNMODELED_DATASET_COLUMN` gap.
3. **Duplicate business keys** — `data/samples/northstar_crm_customers.csv` contains
   `C-10007` and `C-10015` twice (conflicting name spellings/credit limits).
   Tracked in `ISS-CUSTOMER-DUPLICATE-KEYS` and
   `DQ-CUSTOMER-DUPLICATE-BUSINESS-KEYS`.
4. **Mapping conflict** — `MAP-CRM-CREDIT-LIMIT-TO-KNVV-KLIMK` and
   `MAP-VOYAGER-CREDIT-LIMIT-TO-KNVV-KLIMK` both target KNVV-KLIMK with different
   transformation notes (direct copy vs. bucket conversion). Tracked in
   `ISS-CREDIT-LIMIT-MAPPING-CONFLICT`; resolution proposed in
   `DEC-CREDIT-LIMIT-SOURCE-PRECEDENCE`.
5. **Missing ownership (Logistics)** — `DOMAIN-LOGISTICS` deliberately has no
   `OwnershipRole`, and all 12 Logistics objects (entity, attributes, field
   endpoints, mappings, validation rules, dataset) have no owner. They surface as
   `OWNERSHIP_MISSING` validation warnings, as orphaned objects in
   `martenweave owners`, and as `active_object_missing_owner` readiness blockers.
6. **Incomplete evidence** — `EVI-CREDIT-LIMIT-SOURCE-COMPARISON` deliberately lacks
   `title`/`name` and `domain` metadata (status `draft`), producing a
   `DISPLAY_NAME_MISSING` validation warning.
7. **Open high-risk proposal** — `PP-NORTHSTAR-NET-VALUE-VALIDATION-001`
   (`pending_review`, proposes a `ValidationRule`, a high-risk object type) is
   referenced by the approved `CR-PP-NORTHSTAR-NET-VALUE-VALIDATION-001`. It
   surfaces as a `high_risk_unapproved_proposal` readiness blocker and in the
   scorecard pending/high-risk change metrics.
8. **Cross-domain blast radius** — `martenweave impact ATTR-SHARED-PAYMENT-TERMS`
   shows Supplier + Procurement + Finance objects at once;
   `martenweave impact ATTR-SHARED-CUSTOMER-CREDIT-LIMIT` shows Customer + Sales +
   Finance.

Expected validation output: `is_valid: true`, 0 ERRORs, 13 WARNINGs
(12 `OWNERSHIP_MISSING` for Logistics + 1 `DISPLAY_NAME_MISSING` for the incomplete
evidence — all intentional), 2 INFO (`SCHEMA_VERSION_MISSING` on the proposal and
change request, mirroring the upstream example structure).

## Repository layout

```
modelops.config.yaml          # Repository configuration (sap domain pack enabled)
model/                        # 187 canonical objects (Markdown + YAML frontmatter)
  patch-proposals/            # PP-NORTHSTAR-NET-VALUE-VALIDATION-001 (pending_review)
  change-requests/            # CR-PP-NORTHSTAR-NET-VALUE-VALIDATION-001 (approved)
data/
  generate_synthetic_data.py  # Seeded, deterministic generator (stdlib + openpyxl)
  samples/                    # 6 CSVs + 1 XLSX produced by the generator
  patch_notes/                # Note file for the propose-patch reproduction step
generated/                    # Disposable index, profiles, JSONL exports (rebuildable)
```

## Reproduction

All commands run from the repository root of your martenweave checkout
(`<root>`), using the repo-local CLI at `.venv/bin/martenweave`. Set
`REPO=examples/northstar_mobility_pilot` for convenience.

```bash
# 0. (Re)generate the synthetic datasets — deterministic, byte-identical output
cd examples/northstar_mobility_pilot && ../../.venv/bin/python data/generate_synthetic_data.py && cd ../..

# 1. Validate the canonical model -> is_valid: true, 0 ERRORs
.venv/bin/martenweave validate --repo $REPO --json

# 2. Build the disposable index + JSONL exports
.venv/bin/martenweave build-index --repo $REPO --jsonl

# 3. Profile every dataset (links profiles to the Dataset objects)
for f in $REPO/data/samples/*; do .venv/bin/martenweave profile-dataset "$f" --repo $REPO; done

# 4. Gap detection — the two intentional dataset problems surface here
.venv/bin/martenweave gaps $REPO/data/samples/northstar_crm_sales_orders.csv --repo $REPO
.venv/bin/martenweave gaps $REPO/data/samples/voyager_materials.csv --repo $REPO
.venv/bin/martenweave gap-report --repo $REPO

# 5. Health, scorecard, and ownership — the Logistics ownership gap is visible
.venv/bin/martenweave health --repo $REPO
.venv/bin/martenweave scorecard --repo $REPO
.venv/bin/martenweave owners --repo $REPO

# 6. Search and structured query
.venv/bin/martenweave search "payment terms" --repo $REPO
.venv/bin/martenweave query --repo $REPO --type Attribute

# 7. Cross-domain trace and impact for the two shared attributes
.venv/bin/martenweave trace ATTR-SHARED-PAYMENT-TERMS --repo $REPO
.venv/bin/martenweave impact ATTR-SHARED-PAYMENT-TERMS --repo $REPO
.venv/bin/martenweave impact ATTR-SHARED-CUSTOMER-CREDIT-LIMIT --repo $REPO

# 8. Readiness gates (dry-run: never writes into the example)
.venv/bin/martenweave readiness --repo $REPO --dry-run

# 9. Propose a patch from the committed note (dry-run first)
.venv/bin/martenweave propose-patch --from $REPO/data/patch_notes/sales_net_value_note.md --repo $REPO --dry-run
# Without an AI provider configured this answers "No proposal generated" — the
# deterministic scaffold refuses to guess, which is the no-silent-mutation gate
# working as intended. With MARTENWEAVE_AI_PROVIDER set, the same command drafts
# a real PatchProposal for human review.

# 10. Issue draft and change bundle for the pending proposal
.venv/bin/martenweave issue-draft create --proposal PP-NORTHSTAR-NET-VALUE-VALIDATION-001 --repo $REPO
.venv/bin/martenweave git-bundle PP-NORTHSTAR-NET-VALUE-VALIDATION-001 --repo $REPO

# 11. Explore the pilot in the local Workbench
.venv/bin/martenweave workbench --repo $REPO
```

Notes on the reproduction steps:

- Steps 1–8 are strictly read-only. Steps 9–10 write review artifacts (proposal,
  draft, bundle) into the repository by design; use `--dry-run` first if you only
  want to preview. Step 8 (`readiness`) must keep `--dry-run` so it never creates
  readiness Issue files inside the example.
- After re-running step 2 (`build-index`), re-run step 3 so the dataset profiles
  are linked back into the fresh index.
- The generator is deterministic: two consecutive runs of step 0 produce
  byte-identical files (fixed seed, no timestamps; XLSX metadata and zip entry
  dates are pinned).

# Product Explorer Audit — Martenweave Core v0.4.1

> Role: first-time SAP/MDM Product Owner evaluating the open-source core.
> Date: 2026-07-07
> Repository: `metalhatscats/martenweave-core`
> Version tested: `0.4.1`
> Method: fresh source install, documented onboarding, all main CLI flows, static viewer inspection, SAP Customer Group / `KNVV-KDGRP` scenario.

---

## Executive Verdict

Martenweave Core is **real and runnable**. The install works, the examples validate, the index builds, search/trace/impact return sensible results, and the static viewer is usable. For a technical evaluator, the "shape" of a model registry is convincing.

However, the **dataset-to-model and governance-reporting workflows have trust-breaking bugs and inconsistencies** that would undermine a pilot. A first-time user can get to a working index in 15 minutes, but they will hit false-positive gap reports, scorecard metrics that mark zero coverage as "pass", and a gap-to-issue path that does not exist as documented. The core engine is solid; the **edges of the user journey need hardening before a customer pilot**.

Classification of the overall first-run experience: **PARTIAL — functional but not yet trustworthy**.

---

## First Real User Value

A SAP/MDM practitioner can, in under 15 minutes:

1. Install `martenweave-core` from source.
2. Open the `examples/customer_bp_model` repository.
3. Validate, build the index, and search for `Customer Group` or `KNVV-KDGRP`.
4. Trace from the business attribute `ATTR-CUST-SALES-CUSTOMER-GROUP` to its SAP FieldEndpoint, mapping, validation rule, owners, and the `CH01-A17` decision.
5. Generate a local static viewer with object detail pages.
6. See ownership, decisions, and impact analysis in structured JSON or Rich tables.

The first real value is **traceability**: a migration team can finally answer "where does Customer Group live, who owns it, and what else breaks if it changes?" without a spreadsheet.

---

## Workflow Evaluation

For every workflow we classify:

- **PASS** — works as a first-time user would expect.
- **FRICTION** — works, but with confusing output or extra steps.
- **PARTIAL** — works for the happy path, but has gaps or misleading behavior.
- **FAIL** — does not work or produces incorrect results.
- **NOT PROVEN** — not exercised in this audit.

We also score: **functional** (F), **understandable** (U), **actionable** (A), **valuable** (V) for SAP migration / MDM / governance / AMS.

| Workflow | Classification | F | U | A | V | Notes |
|---|---|---|---|---|---|---|
| Fresh source install | PASS | ✅ | ✅ | ✅ | ✅ | `pip install -e ".[dev]"`, both `martenweave` and `modelops` commands work. |
| CLI help surface | PASS | ✅ | ✅ | ✅ | ✅ | Typer help is clear; command list is large but well organized. |
| `init` empty repository | PASS | ✅ | ✅ | ✅ | ✅ | Creates config, starter `DOMAIN-EXAMPLE.md`, `generated/`. Minor: no `data/samples/` folder created. |
| Validate simple example | PASS | ✅ | ✅ | ✅ | ✅ | 0 errors, 18 methodology warnings (expected). |
| Build index (simple) | PASS | ✅ | ✅ | ✅ | ✅ | SQLite + JSONL created, 14 objects indexed. |
| Static viewer (simple) | PASS | ✅ | ✅ | ✅ | ✅ | `index.html`, `objects.html`, object detail pages, search index generated. |
| Search / query | PASS | ✅ | ✅ | ✅ | ✅ | Keyword and typed queries return relevant objects with stable JSON. |
| Trace / impact | PASS | ✅ | ✅ | ✅ | ✅ | Shows depth, relationship type, direction, source files. Good for SAP impact analysis. |
| Profile dataset | PASS | ✅ | ✅ | ✅ | ✅ | CSV profile saved with row/column counts and column metadata. |
| Dataset gaps (simple) | **FAIL** | ⚠️ | ⚠️ | ❌ | ❌ | Reports `MODEL_ATTRIBUTE_MISSING_SOURCE` for every attribute even though dataset columns matched their FieldEndpoints. False positives break trust. |
| Health / scorecard (simple) | **PARTIAL** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | Health shows `Datasets with profile: 0/1` immediately after profiling; scorecard marks 0% `evidence_coverage` and `sap_table_coverage` as PASS. |
| Validate SAP example | PASS | ✅ | ✅ | ✅ | ✅ | 0 errors, 50 warnings. SAP context rules are enforced. |
| Build index (SAP) | PASS | ✅ | ✅ | ✅ | ✅ | 85 objects indexed; freshness check works. |
| Search / trace / impact (SAP) | PASS | ✅ | ✅ | ✅ | ✅ | `KNVV-KDGRP` trace includes Attribute, FieldEndpoint, Mapping, ValidationRule, Issue, Decision, owners. |
| Static viewer (SAP) | PASS | ✅ | ✅ | ✅ | ✅ | Object detail page for `fep-s4-knvv-kdgrp.html` exists; search index contains KNVV/KDGRP/Customer Group. |
| Dataset gaps (SAP) | PASS | ✅ | ✅ | ✅ | ✅ | Realistic 1/6 match rate; unmatched columns get clear `UNMODELED_DATASET_COLUMN` gaps promoted to a PatchProposal of `create_issue` operations for human triage. |
| Evidence-to-patch-proposal | **PARTIAL** | ✅ | ⚠️ | ⚠️ | ⚠️ | Dry-run produces a proposal with correct affected objects, but the operation is generic ("Updated description from note") and the CLI does not warn that this is a deterministic scaffold, not AI output. |
| Health / scorecard / owners / decisions (SAP) | **PARTIAL** | ✅ | ⚠️ | ⚠️ | ✅ | Owners and decisions are excellent. Scorecard again shows misleading PASS for zero-coverage metrics and prints "Untitled Repository" despite config. |
| Gap-to-GitHub-issue | **FAIL** | ❌ | ❌ | ❌ | ❌ | `martenweave issue-draft` is a command group; `issue-draft create` requires `--change-request`, `--proposal`, or `--from-validation`. There is no `--from-gaps` source. The documented gap-to-issue workflow does not exist as a single command. |
| Documentation clarity | PASS | ✅ | ✅ | ✅ | ✅ | README, first-15-minutes, demo-quickstart-flow are accurate and copy-pasteable. |
| Command output clarity | PASS | ✅ | ✅ | ✅ | ✅ | Rich tables are readable; JSON contracts are stable enough for smoke tests. |

### Summary of Classifications

- **PASS**: 18 workflows
- **FRICTION**: 0 (most frictions are captured as PARTIAL because they affect trust)
- **PARTIAL**: 3 workflows
- **FAIL**: 2 workflows
- **NOT PROVEN**: 0

---

## Five Main Problems

### 1. `gaps --check-model` reports false-positive `MODEL_ATTRIBUTE_MISSING_SOURCE`

**Evidence:**

```bash
.venv/bin/martenweave gaps examples/simple_product_model/data/samples/product_sample.csv \
  --repo examples/simple_product_model --check-model
```

Output shows:

- Coverage: 5/5 columns matched to FieldEndpoints (`FEP-PRODUCT-ID`, `FEP-PRODUCT-NAME`, etc.).
- Gaps: 5 × `MODEL_ATTRIBUTE_MISSING_SOURCE` claiming attributes have no linked FieldEndpoint.

This is incorrect: the FieldEndpoints *are* linked to the attributes through the canonical model. A first-time user sees the tool contradict itself in the same JSON object.

**Impact:** Breaks trust in the dataset-to-model workflow; users cannot rely on gap severity to prioritize work.

**Value area:** SAP migration, MDM, data governance.

---

### 2. `profile-dataset` and the index get out of sync silently

**Evidence:**

```bash
.venv/bin/martenweave profile-dataset examples/simple_product_model/data/samples/product_sample.csv \
  --repo examples/simple_product_model
.venv/bin/martenweave health --repo examples/simple_product_model
```

Health still reports `Datasets with profile: 0/1`. The profile file is written to `generated/dataset_profiles/`, but the SQLite index used by `health` and `scorecard` is not updated. The user must remember to run `build-index` again.

**Impact:** A governance report can show outdated coverage immediately after the user thinks they have progressed.

**Value area:** MDM governance, AMS.

---

### 3. Scorecard marks zero-coverage metrics as PASS and ignores repository name

**Evidence:**

For `examples/simple_product_model`:

- `evidence_coverage: 0.0` → status `pass` because no Decision objects exist.
- `sap_table_coverage: 0.0` → status `pass` because no SAP FieldEndpoints exist.

For `examples/customer_bp_model`:

- Scorecard header prints `Scorecard: Untitled Repository` even though `modelops.config.yaml` contains repository metadata.

A 0% coverage metric should not be green. A pilot stakeholder will dismiss the scorecard as unreliable.

**Impact:** Governance scorecard loses credibility; cannot be shown to a customer as-is.

**Value area:** Governance, AMS, pilot readiness.

---

### 4. Gap-to-GitHub-issue workflow does not exist as documented

**Evidence:**

```bash
.venv/bin/martenweave issue-draft --repo examples/customer_bp_model
# Error: No such option '--repo'. Did you mean '--help'?

.venv/bin/martenweave issue-draft create --help
# Requires --change-request, --proposal, or --from-validation
```

There is no `--from-gaps` or `--gap-id` source. The user cannot turn the concrete dataset gaps from `martenweave gaps` into a GitHub issue draft in one command. The closest path is `issue-draft create --from-validation`, which drafts all 50 validation warnings, not the specific gap.

**Impact:** The evidence-to-action loop is broken. Gaps are detected but cannot be tracked as issues without manual copy-paste.

**Value area:** SAP migration, MDM governance, AMS issue tracking.

---

### 5. `propose-patch` scaffold is not clearly labeled as non-AI in CLI output

**Evidence:**

```bash
.venv/bin/martenweave propose-patch --from /tmp/mw-sap-note.md \
  --repo examples/customer_bp_model --dry-run --json
```

JSON includes `assumptions: ["No AI provider is configured. This is a deterministic scaffold proposal."]`, but the default human-readable output does not surface this prominently. A user running without `--json` may think the generic `update_object description` operation came from AI analysis of the CH01-A17 decision.

**Impact:** Governance risk: AI-assisted workflows must be transparent about human-vs-machine generation.

**Value area:** Governance, AI safety, AMS.

---

## What Blocks a Pilot

A pilot with a real SAP/MDM team is blocked by **trust**, not by missing features:

1. **Dataset-to-model trust**: the false-positive gap report means a migration team cannot use `gaps` to sign off data readiness.
2. **Reporting trust**: the scorecard shows green for zero coverage and stale index data, so stakeholders cannot rely on it for go/no-go decisions.
3. **Workflow closure**: gaps cannot be promoted to trackable issues, and proposals are not clearly labeled as scaffolds, so the "detect → propose → approve → apply" loop is not credible.

The core is functional enough for a technical proof-of-concept, but not for a customer-facing pilot until these trust issues are fixed and a single end-to-end demo script passes deterministically.

---

## Static Viewer Usability

The static viewer generated by `docs-build` is a genuine asset.

**Strengths:**

- Generates quickly (`~1 s` for 85 objects).
- Includes `index.html`, `objects.html`, type indexes, object detail pages, `gaps.html`, `decisions.html`, `owners.html`, `search-index.json`, and viewer assets.
- Object detail page for `FEP-S4-KNVV-KDGRP` exists and is linked from search.
- No hosted UI, login, or editing path — consistent with the local-first boundary.

**Weaknesses:**

- The viewer is generated from the SQLite index, so if the index is stale, the viewer is stale. There is no viewer-level freshness warning.
- Object detail pages list raw frontmatter fields without a clear "business card" summary at the top.
- No visible link from an Attribute to its SAP context rule explanation (e.g., why `KNVV` requires `customer_sales_area`).

**Classification:** PASS for a read-only inspection/demo surface; FRICTION if used as the primary review artifact.

---

## Documentation and Command Output Clarity

**Documentation:**

- `README.md` is accurate and copy-pasteable.
- `docs/first-15-minutes.md` gives a clean 15-minute path.
- `docs/demo-quickstart-flow.md` correctly covers the SAP scenario.
- Command reference table in `README.md` matches `--help`.

**Command output:**

- Rich tables are readable and color-coded.
- JSON output is stable enough for `scripts/release_smoke.sh` to assert on keys.
- Validation warnings include a "Fix" column with actionable text.

**Gaps:**

- `issue-draft` is documented as a flat command in `README.md` (`issue-draft  Generate GitHub-ready issue drafts`) but is actually a command group. This mismatch matters for first-time users.
- The difference between `gaps` and `gap-report` is not explained clearly in the CLI help.

---

## Value Assessment by Use Case

| Use case | Verdict | Why |
|---|---|---|
| SAP migration | **PARTIAL** | Traceability and SAP context rules work, but gap detection and scorecard reporting are not trustworthy yet. |
| MDM governance | **PARTIAL** | Ownership, decisions, and validation coverage are visible, but scorecard logic and profile/index sync need fixing. |
| Governance / compliance | **PARTIAL** | Audit log and ChangeRequest gates exist; proposal-first mutation is sound. Reporting reliability is the blocker. |
| AMS (Application Management Services) | **PARTIAL** | Static viewer and search are useful for onboarding; issue drafting and impact analysis need tighter integration. |
| Generic data modeling | **PASS** | Simple example works end-to-end with fewer edge cases. |

---

## Evidence Log

### Environment

```text
Python 3.11.15
martenweave-core 0.4.1
Install: python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"
```

### Simple product model validation

```text
Errors: 0, Warnings: 18
Codes: FIELD_ENDPOINT_MISSING_ENRICHMENT (5), OWNERSHIP_MISSING (13)
```

### SAP Customer BP model validation

```text
Errors: 0, Warnings: 50
Codes: ATTRIBUTE_MISSING_CONTEXT (15), ATTRIBUTE_USAGE_MISSING_TYPE (13),
       FIELD_ENDPOINT_MISSING_ENRICHMENT (18), LOV_EMPTY (2), VALUE_MAPPING_EMPTY (2)
```

### SAP Customer Group trace root

```text
ATTR-CUST-SALES-CUSTOMER-GROUP
  → FEP-S4-KNVV-KDGRP
  → MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
  → VAL-CUST-GROUP-ALLOWED-VALUES
  → ISS-CH01-A17-CONFIG-GAP
  → DEC-CH01-A17-...
  → PERSON-BUSINESS-OWNER / PERSON-DATA-STEWARD
```

### SAP dataset gap sample

```text
 customer_sales_area_sample.csv
   matched: 1/6 (CUSTOMER_GROUP → FEP-MIGFILE-CUSTOMER-GROUP)
   unmatched: CUSTOMER_ID, SALES_ORG, DISTRIBUTION_CHANNEL, DIVISION, CURRENCY
```

---

## Conclusion

Martenweave Core has crossed the threshold from "prototype" to "runnable product skeleton". The canonical-file model, deterministic validation, SQLite index, trace/impact engine, and static viewer are all real and valuable. The SAP Customer Group scenario is demonstrable end-to-end.

The next phase must be **hardening the trust surface**: fix the gap-detection false positives, align profile/index state, repair scorecard metric logic, close the gap-to-issue loop, and make the non-AI proposal scaffold transparent. Once those are in place, the project is ready for a controlled pilot with a real migration team.

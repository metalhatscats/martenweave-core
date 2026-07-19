# Roadmap Recommendations — Product Explorer Audit

> Note: dated point-in-time record (2026-07-07); the audit targeted `0.4.1`, the current release is `0.6.1`.

> Source: `docs/product/PRODUCT_EXPLORER_AUDIT.md`
> Date: 2026-07-07
> Version audited: `martenweave-core 0.4.1`

This roadmap is derived from a first-time SAP/MDM Product Owner walkthrough of the CLI, examples, static viewer, and the SAP Customer Group / `KNVV-KDGRP` scenario. It is intentionally scoped to the existing local-first, CLI-driven, backend-first product boundary. It does not propose a SaaS UI, chatbot, workflow engine, direct SAP write-back, or enterprise platform.

---

## Guiding Principle

> Fix trust before adding features.

The core engine (parser, validation, index, trace, impact, viewer) works. The blockers are at the **edges of the user journey**: gap detection that contradicts itself, scorecard metrics that mark zero coverage as pass, and workflows that detect gaps but cannot turn them into trackable issues. The next milestone must harden these surfaces.

---

## P0 — Broken Core Journey

These issues produce incorrect or misleading results for a first-time user. They block any customer pilot.

### P0.1 Fix `gaps --check-model` false-positive `MODEL_ATTRIBUTE_MISSING_SOURCE`

**Problem:** When dataset columns match FieldEndpoints, `gaps --check-model` still reports every linked Attribute as missing a source.

**Why P0:** A migration team cannot use gap detection for data-readiness sign-off if the tool reports critical gaps that do not exist.

**Acceptance criteria:**
- `martenweave gaps <dataset> --repo examples/simple_product_model --check-model` returns 0 `MODEL_ATTRIBUTE_MISSING_SOURCE` gaps when all columns match endpoints that are linked to attributes.
- Add/update tests in `tests/test_gaps*.py` that assert the expected gap set for the simple product sample.
- The fix does not suppress legitimate gaps (e.g., an attribute genuinely has no linked endpoint).

**Related issue:** [#482 — Fix gaps --check-model false-positive MODEL_ATTRIBUTE_MISSING_SOURCE](https://github.com/metalhatscats/martenweave-core/issues/482)

**Suggested owner:** backend/core validation.

---

### P0.2 Repair scorecard metric logic and repository naming

**Problem:**
- Metrics with `0.0` value and non-zero target are shown as `pass` when no relevant objects exist (`evidence_coverage`, `sap_table_coverage`).
- The scorecard header prints `Untitled Repository` even when `modelops.config.yaml` contains a repository name.

**Why P0:** A governance scorecard that marks zero coverage as green is not credible to pilot stakeholders.

**Acceptance criteria:**
- Any metric below target is `warning` or `fail`, never `pass`, regardless of object count.
- `scorecard` reads `repository.name` (or equivalent config field) and prints it in the header.
- Tests assert metric status logic for zero-coverage cases.
- `ruff check .` and `pytest -q` pass.

**Related issue:** [#483 — Repair scorecard metric logic and repository naming](https://github.com/metalhatscats/martenweave-core/issues/483)

**Suggested owner:** reports/scorecard service.

---

### P0.3 Keep dataset profiles and the generated index in sync

**Problem:** `profile-dataset` writes a JSON profile, but `health` and `scorecard` read from the SQLite index and show `Datasets with profile: 0/1` until `build-index` is run again.

**Why P0:** A user who follows the documented flow expects profiling to update coverage immediately.

**Acceptance criteria:**
- After `profile-dataset`, `health` and `scorecard` reflect the profile without requiring a manual `build-index`.
- OR the CLI prints a clear "run build-index to refresh coverage" message and documentation is updated.
- Preferred fix: `profile-dataset` updates the index incrementally or triggers a lightweight refresh of dataset profile facts.

**Related issue:** [#484 — Keep dataset profiles and generated index in sync](https://github.com/metalhatscats/martenweave-core/issues/484)

**Suggested owner:** imports/profile + index builder.

---

## P1 — Onboarding and Pilot Readiness

These make the first 15 minutes and the pilot demo repeatable and trustworthy.

### P1.1 Add one deterministic golden demo journey smoke test

**Problem:** The canonical 14-step demo from `ACCEPTANCE_CRITERIA.md` is documented but not executable as a single command.

**Acceptance criteria:**
- Add `scripts/demo_customer_group_smoke.sh` (or equivalent pytest) that runs:
  - validate `--check-decisions`
  - build-index `--jsonl`
  - search `Customer Group` and `KNVV-KDGRP`
  - trace `ATTR-CUST-SALES-CUSTOMER-GROUP`
  - impact `FEP-S4-KNVV-KDGRP`
  - gaps on `customer_sales_area_sample.csv --check-model`
  - propose-patch dry-run from a CH01-A17 note
  - docs-build to a temp viewer
- Script exits non-zero on any step failure.
- Uses a temp copy of `examples/customer_bp_model` so canonical files are not mutated.

**Related existing issue:** [#471 — Add golden Customer Group demo journey smoke](https://github.com/metalhatscats/martenweave-core/issues/471)

**Suggested owner:** QA / release engineering.

---

### P1.2 Clarify `propose-patch` non-AI scaffold in CLI output

**Problem:** The deterministic scaffold from `NoProviderAdapter` is only labeled in JSON assumptions, not in default human output.

**Acceptance criteria:**
- Default `propose-patch` output prints a prominent warning when no AI provider is configured.
- Generated PatchProposal frontmatter includes `generated_by: no_provider_scaffold`.
- Tests assert the warning and marker.

**Related existing issue:** [#448 — NoProviderAdapter scaffold proposal is not clearly labeled in CLI output](https://github.com/metalhatscats/martenweave-core/issues/448)

**Suggested owner:** CLI / AI adapter.

---

### P1.3 Add scenario templates to `martenweave init`

**Problem:** `init` creates a generic empty repository. A SAP migration team must manually copy `examples/customer_bp_model` to get started.

**Acceptance criteria:**
- `martenweave init --template sap-bp-customer-migration` scaffolds a small working model with DOMAIN, EntityContext, Attribute, FieldEndpoint, Mapping, and a sample CSV.
- At least one additional template (e.g., `ams-field-dictionary`) ships in the first iteration.
- Generated repos validate cleanly and build an index.

**Related existing issue:** [#434 — Add scenario templates for SAP migration and AMS field dictionary use cases](https://github.com/metalhatscats/martenweave-core/issues/434)

**Suggested owner:** CLI / templates.

---

### P1.4 Freshen `AGENTS.md` and README command references

**Problem:** `AGENTS.md` references `0.1.0`, omits newer modules, and the README lists `issue-draft` as a flat command when it is a command group.

**Acceptance criteria:**
- `AGENTS.md` version and module list match `0.4.x`.
- README command reference distinguishes flat commands vs command groups where it matters (`issue-draft`, `proposal`, `decisions`, `change-request`).

**Related existing issue:** [#449 — Update AGENTS.md to reflect v0.4.0 module and command surface](https://github.com/metalhatscats/martenweave-core/issues/449)

**Suggested owner:** docs.

---

## P2 — Stronger Gaps, Impact, Evidence and Proposal Workflows

These close the loop between detection, tracking, review, and approval.

### P2.1 Add `--from-gaps` source to `issue-draft create`

**Problem:** `issue-draft create` only supports `--change-request`, `--proposal`, or `--from-validation`. There is no direct path from `martenweave gaps` output to a GitHub issue draft.

**Acceptance criteria:**
- `martenweave issue-draft create --from-gaps <gap-id-or-file> --repo ...` generates a focused issue draft linked to the affected Attribute, FieldEndpoint, Dataset, and evidence.
- If no gap ID is provided, drafts one issue per high/critical gap.
- Draft includes gap code, severity, affected object IDs, dataset metadata, and recommended proposal op.

**Related existing issue:** none found (complements [#473 — Add stable gap IDs and evidence links](https://github.com/metalhatscats/martenweave-core/issues/473)).

**Suggested owner:** issue_draft / gaps.

---

### P2.2 Add stable gap IDs and evidence links

**Problem:** Gap detection results are not traceable across runs or datasets, making issue/proposal workflows noisy.

**Acceptance criteria:**
- Each gap in `martenweave gaps --json` has a deterministic `gap_id`.
- `--create-issues` and `--promote-to-proposal` persist the gap ID and evidence metadata.
- Repeated runs on the same state do not produce duplicate issue references.

**Related existing issue:** [#473 — Add stable gap IDs and evidence links](https://github.com/metalhatscats/martenweave-core/issues/473)

**Suggested owner:** gaps / issue_draft.

---

### P2.3 Add proposal reviewer summary

**Problem:** Reviewing a PatchProposal requires reading raw operations; there is no compact reviewer checklist.

**Acceptance criteria:**
- `martenweave proposal show <id> --repo ...` prints operation count by type, affected objects, files touched, validation status, risk level, assumptions, and a recommended action.
- `--json` output has a stable `reviewer_summary` field.

**Related existing issue:** [#476 — Add proposal reviewer summary](https://github.com/metalhatscats/martenweave-core/issues/476)

**Suggested owner:** patching / approval.

---

### P2.4 Add pilot readiness gates command

**Problem:** There is no single pass/fail command for "is this repository ready for demo/pilot?".

**Acceptance criteria:**
- `martenweave readiness --repo ... --profile demo|pilot|release` returns non-zero when required gates fail.
- Gates include validation errors, stale index, missing owners, unresolved high-severity gaps, and invalid open proposals.

**Related existing issue:** [#474 — Add pilot readiness gates command](https://github.com/metalhatscats/martenweave-core/issues/474)

**Suggested owner:** reports / CLI.

---

## P3 — Later Ideas

These are valuable but should not block v0.1 or the first pilot.

- **Model summary report command** — compact Markdown export for one domain/entity ([#477](https://github.com/metalhatscats/martenweave-core/issues/477)).
- **Diagnostics bundle export** — safe repository-state export for support/agent handoff ([#475](https://github.com/metalhatscats/martenweave-core/issues/475)).
- **Object card command** — compact single-object view for CLI and viewers ([#472](https://github.com/metalhatscats/martenweave-core/issues/472)).
- **Business review pack** — Excel + Markdown pack for non-technical sign-off ([#431](https://github.com/metalhatscats/martenweave-core/issues/431)).
- **Incremental indexing** — avoid dropping the whole SQLite database on every `build-index` ([#456](https://github.com/metalhatscats/martenweave-core/issues/456)).
- **Type-specific search fields** — improve search relevance for SAP table/field lookups ([#455](https://github.com/metalhatscats/martenweave-core/issues/455)).
- **Messier example datasets** — demonstrate credible gap detection with renamed/missing/extra columns ([#453](https://github.com/metalhatscats/martenweave-core/issues/453)).
- **CLI monolith split** — refactor `cli.py` into `commands/` package for maintainability ([#416](https://github.com/metalhatscats/martenweave-core/issues/416)).

---

## Recommended Next Milestone

**Milestone: "Trustworthy Customer Group Pilot"**

Goal: the SAP Customer Group / `KNVV-KDGRP` demo can be run by a first-time user with one command, and every output in the chain is trustworthy.

### Milestone acceptance criteria

1. `bash scripts/demo_customer_group_smoke.sh` passes from a fresh checkout (or equivalent pytest).
2. `martenweave gaps examples/customer_bp_model/data/samples/customer_sales_area_sample.csv --repo examples/customer_bp_model --check-model` reports no false-positive `MODEL_ATTRIBUTE_MISSING_SOURCE` gaps.
3. `martenweave scorecard --repo examples/customer_bp_model` shows correct repository name and no `pass` status for zero-coverage metrics.
4. After `profile-dataset`, `health` and `scorecard` reflect the profile without a manual `build-index` (or the CLI/docs clearly instruct the user to rebuild).
5. `martenweave propose-patch --dry-run ...` clearly labels the output as a deterministic scaffold when no AI provider is configured.
6. All existing tests, ruff, and `scripts/release_smoke.sh` pass.

### Suggested issue set for the milestone

- New: [#482](https://github.com/metalhatscats/martenweave-core/issues/482) Fix `gaps --check-model` false-positive `MODEL_ATTRIBUTE_MISSING_SOURCE`
- New: [#483](https://github.com/metalhatscats/martenweave-core/issues/483) Repair scorecard metric logic and repository naming
- New: [#484](https://github.com/metalhatscats/martenweave-core/issues/484) Keep dataset profiles and generated index in sync
- Reuse: [#448](https://github.com/metalhatscats/martenweave-core/issues/448) Clarify NoProviderAdapter scaffold in CLI output
- Reuse: [#471](https://github.com/metalhatscats/martenweave-core/issues/471) Add golden Customer Group demo journey smoke

---

## One Concrete Next Action

**Create and prioritize a single issue to fix the `gaps --check-model` false-positive `MODEL_ATTRIBUTE_MISSING_SOURCE`.**

This is the highest-leverage fix because:
- It is a clear bug with a reproducible test case.
- It blocks trust in the dataset-to-model workflow, which is the core differentiator for SAP migration.
- It is small and deterministic (no AI, no UI, no external dependencies).
- Fixing it unblocks the rest of the milestone.

---

## Alignment with `ROADMAP_V0_1.md`

`ROADMAP_V0_1.md` already calls for:
- acceptance demo script (v0.2 candidates)
- stronger CLI JSON contract tests
- privacy/sanitization hardening

This audit confirms those priorities and adds specific P0 bugs that must be fixed before the demo script is meaningful. The P2 items above (gap IDs, reviewer summary, readiness gates) are natural extensions of the v0.1 core and should be sequenced after the P0 trust fixes.

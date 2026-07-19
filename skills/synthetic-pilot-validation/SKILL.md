# Skill: Synthetic Pilot Validation — Martenweave

## When to use
You need to prove a product change keeps the Northstar Mobility Group pilot green — the product regression and user-journey benchmark (gate G8) — or you suspect pilot drift.

## Inputs
- Repository root with `.venv` built (`pip install -e '.[dev]'`) and `jq` on PATH
- The change under test (diff or branch)
- Expected numbers from `docs/factory/memory/VALIDATION_COMMANDS.md`

## Read first
1. `docs/factory/memory/VALIDATION_COMMANDS.md` — the verified expected outputs; drift in these numbers is itself a finding.
2. `scripts/demo_northstar_pilot.sh` — the 11 self-verifying steps and their jq assertions.
3. `docs/factory/NORTH_STAR.md` — "Current proof benchmark" section.
4. `docs/factory/policies/AGENT_PREVENTIONS.md` (P6) — canonical data is read-only for agents.

## Do not do
- Do not edit anything under `examples/northstar_mobility_pilot/model/` or `data/` — canonical data changes only via the product PatchProposal path, and fixture changes are L3 (P6).
- Do not "fix" intentional fixture problems: the 61 gaps, 13 warnings, and readiness blockers must keep surfacing.
- Do not edit `generated/` artifacts; rebuild them.
- Do not update expected numbers in docs to match a changed run — a changed number is a finding to report, not to edit away.

## Procedure
1. Run the full benchmark:
   ```bash
   bash scripts/demo_northstar_pilot.sh
   ```
   Expect the final line: `Northstar synthetic pilot reproduction passed (11/11 steps).`
2. Interpret each step against the verified counts (VALIDATION_COMMANDS.md):
   - **1 validate** — `is_valid: true`, 0 errors, 13 warnings (intentional).
   - **2 build-index** — 187 objects indexed (assertion floor is 150; 187 is the verified count).
   - **3 profile-dataset** — all seven extracts in `data/samples/` profile with rows ≥ 1.
   - **4 gaps** — `UNMODELED_DATASET_COLUMN` surfaces on sales orders and materials; gap report total 61.
   - **5 health + scorecard** — 187 objects; readiness review status not ready.
   - **6 search + query** — cross-domain hits (≥3 for "payment terms"; ≥10 Attributes).
   - **7 trace + impact** — payment terms impact 71 objects, credit limit impact 55 objects.
   - **8 readiness** — must FAIL (exit non-zero) with blockers `active_object_missing_owner` and `high_risk_unapproved_proposal`. A passing readiness is a regression.
   - **9 propose-patch** — without an AI provider: exit non-zero, `proposal == null`, assumptions listed (no silent mutation).
   - **10 issue draft + git bundle** — artifacts created for `PP-NORTHSTAR-NET-VALUE-VALIDATION-001`.
   - **11 workbench** — prints launch instructions only.
3. Byte-determinism check — regenerated datasets must be byte-identical:
   ```bash
   cd examples/northstar_mobility_pilot && ../../.venv/bin/python data/generate_synthetic_data.py && cd ../..
   git status --short    # must be empty
   ```
4. Workbench smoke against the pilot:
   ```bash
   .venv/bin/martenweave workbench --repo examples/northstar_mobility_pilot --no-open
   ```
   Open `http://127.0.0.1:8000`; wait for "Local workspace" before asserting anything (probe race, see `docs/factory/memory/LESSONS_LEARNED.md` 2026-07-19).
5. Any mismatch in the expected numbers: stop, capture command + actual vs expected, and report it as a finding in the issue. Do not patch fixtures or docs to hide it.

## Validation
- Demo script reports 11/11 steps passed.
- Observed counts match VALIDATION_COMMANDS.md exactly (187 / 13 / 61 / 71 / 55; readiness blockers named above).
- `git status --short` is empty after dataset regeneration.
- Workbench loads the pilot workspace without console errors.

## Output format
Return:
- Steps passed (`11/11`) and the final script output line
- Table of observed vs expected numbers for steps 1, 2, 4, 7, 8
- Determinism result (`git status` empty or the diff that appeared)
- Workbench smoke result
- Drift findings, if any (command, actual, expected) — reported, never edited away

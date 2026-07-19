# Skill: Repository and Product Audit — Martenweave

## When to use
You are starting a factory session (or suspect drift) and need a verified picture of
repository health and product truth before any work is selected. This is the L0
inspect stage of the factory loop (`docs/factory/WORKFLOWS.md` stage 1). It produces
findings, not fixes.

## Inputs
- A checkout of `metalhatscats/martenweave-core` with the repo-local venv (`.venv/bin/...`)
- Optional: `jq` and Node/npm when the audit covers the Northstar demo or Workbench
- The open issue list (`gh issue list`)

## Read first
1. `docs/factory/memory/PROJECT_MEMORY.md` — current state index; read first every session.
2. `docs/factory/NORTH_STAR.md` — the product scope findings are judged against.
3. `docs/factory/memory/VALIDATION_COMMANDS.md` — canonical commands with expected outputs.
4. `docs/factory/policies/QUALITY_GATES.md` — G1–G11 gate definitions and commands.
5. `docs/factory/memory/KNOWN_LIMITATIONS.md` and `docs/factory/memory/REJECTED_IDEAS.md`.

## Do not do
- Do not fix anything during the audit; findings become issues (P10).
- Do not mark a finding `verified` without a command you actually ran this session (P9).
- Do not report known limitations or rejected ideas as new gaps.
- Do not edit `generated/`, `model/`, tests, or fixtures to make a check pass (P1, P6).
- Do not file GitHub issues here; filing is the `issue-triage` skill after verification.

## Procedure
1. **Freshness.** Confirm the checkout state:
   ```bash
   git status --short
   git log --oneline -5
   git fetch origin && git status -sb
   ```
   Uncommitted changes or a stale `main` are themselves findings.
2. **Lint and test collection:**
   ```bash
   .venv/bin/ruff check .
   .venv/bin/python -m pytest --collect-only -q | tail -1
   ```
   Compare the collected count with `VALIDATION_COMMANDS.md` (full run: 1805 passed,
   3 skipped). Run `.venv/bin/python -m pytest -q` in full when correctness is in question.
3. **Validate all 8 bundled examples** (gate G4):
   ```bash
   for ex in customer_bp_model supplier_vendor_model generic_product_model \
     simple_product_model sap_bp_customer_vendor_reference \
     synthetic_customer_migration_demo synthetic_enterprise_portfolio_demo \
     northstar_mobility_pilot; do
     .venv/bin/martenweave validate --repo examples/$ex | tail -2
   done
   ```
   Expect `is_valid: true` and 0 errors for each.
4. **Doc and skill structure** (gate G10):
   ```bash
   .venv/bin/python scripts/validate_doc_commands.py
   .venv/bin/python scripts/validate_skills.py
   ```
5. **Product behavior.** When behavior or a docs/website claim is in question, run the
   regression benchmark (gate G8):
   ```bash
   bash scripts/demo_northstar_pilot.sh
   ```
   Expect 11/11 steps: 187 indexed objects, 13 warnings, 61 gaps, impact 71/55,
   readiness not ready.
6. **Compare** each deviation against `docs/factory/NORTH_STAR.md` scope,
   `KNOWN_LIMITATIONS.md`, and `REJECTED_IDEAS.md`. Drop out-of-scope findings; record
   non-obvious decisions in memory.
7. **Classify** each surviving finding `verified` (reproduced by a command this
   session) or `suspected` (inferred, not yet reproduced).
8. **Map to issues.** Search before concluding a finding is unfiled:
   ```bash
   gh issue list --search "<distinctive terms>" --state all
   ```
   Record the existing issue number or a proposed new title.

## Validation
- Every command above was actually executed; outputs are quoted with exact counts (P9).
- Each finding carries a `verified`/`suspected` class and a north-star or memory link.
- The working tree is unchanged (`git status --short` matches step 1); the audit is L0.
- Every verified finding maps to an issue number or a proposed issue title.

## Output format
One findings table, one row per finding:

| Area | Evidence (command → result) | Verified? | North-star link | Proposed issue title |
|---|---|---|---|---|

Then list: commands run, environment gaps (e.g. missing `jq` or Node), and the
recommended next step — `gap-regression-detection` for verified rows, then
`issue-triage` for filing.

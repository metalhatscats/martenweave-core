# Skill: Website Claim Verification — Martenweave

## When to use
Use before any public website change, and whenever Core behavior changes. Every public statement must match verified Core behavior — a north-star success measure.

## Inputs
- The claim(s) to add or change.
- Core evidence (commands run this session, with exact outputs) backing each claim.

## Read first
1. `docs/factory/NORTH_STAR.md` — non-goals; "public website claims match verified Core behavior exactly".
2. `docs/factory/policies/AGENT_PREVENTIONS.md` — P9 (no fabricated evidence), P3 (no invented capabilities).
3. `docs/factory/policies/AUTONOMY_LEVELS.md` — website capability claims are L3.
4. `docs/factory/policies/QUALITY_GATES.md` — G10 website checks.

## Do not do
- Do not edit generated `.html` files — edit the `.md` source and regenerate.
- Do not publish capability claims without maintainer approval (L3).
- Do not quote numbers from memory or older sessions; re-run the command now (P9).
- Do not claim non-goals: SaaS, hosted UI, auth, SAP write-back, chatbots.
- Do not push website changes while the Core evidence is unverified.

## Procedure
1. Website repo: sibling checkout `../martenweave.github.io` (clone `https://github.com/Martenweave/martenweave.github.io`).
2. Inventory the claims: `docs/*.md` sources, `llms.txt`, `llms-full.txt`, `ai.txt`, `ai.json`, `sitemap.xml`, and structured data embedded by the page templates.
3. Re-verify every quantitative claim (object counts, gap counts, test counts, demo steps) against CLI output in this session, e.g. from the Core repo root:
   ```bash
   .venv/bin/martenweave health --repo examples/northstar_mobility_pilot --json
   .venv/bin/python -m pytest -q
   bash scripts/demo_northstar_pilot.sh
   ```
4. Edit the `.md` source (or `llms*.txt` / `ai.*` files) so each statement matches the evidence exactly; drop or qualify anything unverifiable.
5. Keep version copy in sync with Core `pyproject.toml`: `ai.json` and `docs/release-proof.md` — website CI enforces it via `scripts/check-core-version-copy.py`.
6. Regenerate and validate in the website repo:
   ```bash
   npm ci
   npm run build
   npm run test:render
   ```
7. After push, once GitHub Pages deploys:
   ```bash
   npm run test:production
   ```
8. Capability claims: open the PR, comment requesting maintainer approval, stop (L3).

## Validation
- `npm run build` and `npm run test:render` pass in the website repo.
- `npm run test:production` passes after the Pages deploy.
- Every quantitative claim traces to a command run in this session, quoted with exact counts.

## Output format
Return:
- claims changed, each with its evidence command and exact output;
- files edited (sources only — never generated `.html`);
- gate results: build / render / production;
- L3 approval status when capability claims are involved.

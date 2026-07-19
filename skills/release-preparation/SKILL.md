# Skill: Release Preparation — Martenweave

## When to use
Use when a maintainer asks for release readiness evidence. The agent assembles evidence; the maintainer decides and executes the release (P7).

## Inputs
- Candidate version (given by the maintainer, never chosen by the agent).
- The state of `main` to evaluate.

## Read first
1. `docs/factory/policies/AGENT_PREVENTIONS.md` — P7: no tags, no PyPI upload, no version bumps.
2. `docs/factory/policies/QUALITY_GATES.md` — G11 release readiness.
3. `docs/factory/policies/AUTONOMY_LEVELS.md` — releases are always L3.
4. `.github/workflows/release.yml` — what the tag-triggered workflow does.

## Do not do
- Do not run `git tag`, bump versions, or publish anything (P7, L3).
- Do not edit `pyproject.toml` version or `src/modelops_core/__version__.py` — that is the maintainer's release commit (P8).
- Do not report readiness from stale runs; every count comes from this session (P9).
- Do not weaken or skip a failing gate to reach "ready" (P1).

## Procedure
1. Run the G11 release gates from the repo root:
   ```bash
   bash scripts/release_smoke.sh
   .venv/bin/python scripts/release_preflight.py --tag v<CANDIDATE>
   ```
   `release_smoke.sh` exercises the CLI against all 8 bundled examples (validate, build-index, index-fresh, health, scorecard, search, trace, impact, gaps, reports, proposal, viewer) plus the Northstar demo and frontend tests. `release_preflight.py` guards that the tag matches the `pyproject.toml` version — pass `--tag` explicitly outside CI.
2. Run the standard gates for full evidence:
   ```bash
   .venv/bin/python -m pytest -q
   .venv/bin/ruff check .
   .venv/bin/ruff format --check src tests
   .venv/bin/python -m build
   ```
3. Check version consistency across:
   - `pyproject.toml` (`project.version`);
   - `src/modelops_core/__version__.py`;
   - `README.md` Status section (current source version, latest published release);
   - website `docs/release-proof.md` and `ai.json` (website CI: `scripts/check-core-version-copy.py`).
   Report drift as a blocker; do not fix it yourself when fixing means a version bump.
4. Summarize what `release.yml` does once the maintainer pushes a `v*` tag: re-run ruff, format check, pytest, and release smoke → preflight version guard → build packaged Workbench assets → `python -m build` → PyPI trusted publishing → GitHub Release with `dist/*` attached.
5. Collect open L3 items and known risks from `docs/factory/memory/KNOWN_LIMITATIONS.md` and open issues.
6. Assemble the readiness report (format below) and hand it to the maintainer. Stop.

## Validation
- Every command above passes, with exact counts captured (e.g. `pytest: N passed`).
- Version strings agree across all four locations, or drift is reported as a blocker.
- Proof of restraint: no tag created, no version commit, no publish — evidence only.

## Output format
Release readiness report containing:
- candidate version;
- gate evidence: each command → pass/fail → exact counts;
- version consistency results;
- what `release.yml` will do on tag push;
- open L3 items and risks;
- recommendation (ready / not ready) — the maintainer decides.

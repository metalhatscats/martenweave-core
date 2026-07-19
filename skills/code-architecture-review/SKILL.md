# Skill: Code and Architecture Review — Martenweave

## When to use
A patch is finished and gated, and you must review it critically before merge — your own work (every agent, every patch) or another agent's work as the Security & Critical Review role (L0 with veto power: it can block any patch).

## Inputs
- The diff against `main` (`git diff main...HEAD`)
- The issue the patch claims to satisfy
- Commit messages and gate evidence already posted on the issue

## Read first
1. The issue: goal, scope, acceptance criteria. Review the patch against these, not against your taste.
2. `docs/factory/policies/AGENT_PREVENTIONS.md` — P1–P10; each one is a reject condition.
3. `docs/factory/policies/QUALITY_GATES.md` — G1–G3 checklist gates and the evidence rule.
4. `docs/architecture/ARCHITECTURE_DECISIONS.md` and the boundary docs: `docs/architecture/CANONICAL_MODEL_BOUNDARY.md`, `WORKBENCH_BOUNDARY.md`, `GENERATED_INDEX_BOUNDARY.md`, `INTEGRATION_BOUNDARIES.md`.
5. The changed files in full, not just the hunks — context reveals what the diff hides.

## Do not do
- Do not approve your own patch without re-reading it as a hostile reviewer.
- Do not review style the linter already owns; review correctness, scope, and evidence.
- Do not fix findings inside someone else's patch; report them in the verdict.
- Do not waive a prevention violation; only the maintainer can (AGENT_PREVENTIONS.md, violation handling).
- Do not approve while any claim in the commit or issue is unverified (P9).

## Procedure
1. **Diff hygiene.** `git diff main...HEAD --stat` shows only in-scope files. Hard reject if it touches protected paths: `.github/workflows/`, `LICENSE`, `NOTICE`, `pyproject.toml` metadata, `.env*`, `generated/`, or canonical `model/` data (P6, P8). No unrelated churn or reformat noise (P10).
2. **P1–P10 checklist.** Walk every prevention and answer pass/fail with one line of evidence: tests not weakened (P1), no duplicated service (P2), traceable to an issue and the north star (P3), no policy/scope edits (P4), no forbidden product shapes (P5), no canonical data edits (P6), no release actions (P7), no protected paths (P8), no fabricated evidence (P9), no scope expansion (P10).
3. **G1–G3 checklist gates.**
   - G1: change traces to the issue and `docs/factory/NORTH_STAR.md`; adds no non-goal.
   - G2: consistent with ARCHITECTURE_DECISIONS.md and the boundary docs; no new component duplicating an existing service. Record which ADRs/boundaries you checked.
   - G3: no secrets committed, no new network calls, no PII in fixtures, guardrails unchanged or strengthened.
4. **Architecture consistency.** New logic lands in the layer the boundary docs assign it to: canonical logic and validators in Core, HTTP adapters in the Local API, visualization in the Workbench. Canonical truth stays in `model/` files; `generated/` stays disposable; Workbench mutations go through Core services and approval gates.
5. **Test quality.** For each new or changed test ask: would this fail if the bug came back? Reject tautologies — asserting what a mock returns, re-implementing the code under test, or asserting only "no exception". A regression test must reproduce the reported bug.
6. **Evidence check.** Every claim in the commit message or issue (tests passed, counts, gates run) matches a command actually run in the session, with counts quoted exactly. Unverified claims must be labeled unverified.
7. **Verdict.** Approve only when steps 1–6 are clean. Otherwise block with numbered reasons, each citing file:line and the rule it violates.

## Validation
- Written pass/fail answers for every one of P1–P10 and G1–G3, each with evidence.
- Every blocking finding names file, line, and the violated rule (P#, G#, or boundary doc).
- The verdict is explicit: `approve` or `block` — never "looks fine".

## Output format
Return:
- Verdict: `approve` or `block`
- P1–P10 results: pass/fail + one-line evidence each
- G1–G3 answers, including which ADRs/boundary docs were checked
- Test-quality findings (if any)
- Evidence-check findings: claims vs. commands actually run
- For `block`: numbered reasons with file:line, the violated rule, and the minimal change that would clear each

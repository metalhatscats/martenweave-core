# Skill: Gap and Regression Detection — Martenweave

## When to use
You have audit output (skill: `repository-product-audit`) and need to turn findings
into precise, verified gaps, or you suspect a previously-passing gate now fails. This
is stages 2–3 of the factory loop (`docs/factory/WORKFLOWS.md`).

## Inputs
- Findings list from an audit, each with evidence (command → result)
- `docs/factory/memory/VALIDATION_COMMANDS.md` expected outputs
- Open issue list (`gh issue list`)

## Read first
1. `docs/factory/NORTH_STAR.md` — what the product must do and must not do.
2. `docs/factory/memory/VALIDATION_COMMANDS.md` — the numbers that define "passing".
3. `docs/factory/memory/KNOWN_LIMITATIONS.md` — verified limitations, not bugs.
4. `docs/factory/memory/REJECTED_IDEAS.md` — ideas already decided against.
5. `docs/factory/WORKFLOWS.md` §1 stages 2–5 — gap definition and ranking order.

## Do not do
- Do not promote a `suspected` finding to a gap without reproducing it (P9).
- Do not report a known limitation or rejected idea as a gap; link the memory doc instead.
- Do not treat intentional pilot problems (61 gaps, 13 warnings, readiness not ready)
  as regressions — they are the benchmark working.
- Do not bundle unrelated gaps into one report entry; one gap = one issue later.
- Do not fix the gap here; this skill ends at a ranked, deduplicated gap list.

## Procedure
1. **Classify the finding type:**
   - *Regression*: a gate or behavior that previously passed now fails. Compare current
     output against `VALIDATION_COMMANDS.md` expectations — e.g. `pytest` 1805 passed /
     3 skipped, Northstar 187 objects / 13 warnings / 61 gaps / impact 71 / 55,
     `scripts/demo_northstar_pilot.sh` 11/11 steps, website "170 HTML files".
   - *Product gap*: north-star behavior missing, or docs/website claims that verified
     behavior does not support.
2. **Reproduce** every suspected finding with an exact command; capture output
   verbatim. If you cannot reproduce it, keep it `suspected` and state what is missing.
3. **Apply the gap test.** A real gap states all three:
   - (a) what is true now — command plus observed output;
   - (b) what should be true — `NORTH_STAR.md` section or docs path reference;
   - (c) user impact — which primary user (`NORTH_STAR.md` "Primary users") is hurt
     and how.
   If any leg is missing, it is not yet a gap.
4. **Dedupe** against memory docs and the backlog:
   ```bash
   gh issue list --search "<key terms>" --state all
   ```
   Re-check `KNOWN_LIMITATIONS.md` and `REJECTED_IDEAS.md`. Link duplicates instead of
   re-filing; plan an update when an open issue already covers the gap.
5. **Rank severity** in factory order (`WORKFLOWS.md` stage 5):
   1. Correctness/trust bugs in shipped behavior
   2. Documentation or website claim drift
   3. Test/CI health
   4. Small UX clarity wins
   5. Everything else
   A regression takes the class of the gate it broke; within a class, smallest fix first.
6. **Hand off.** Verified, deduplicated, ranked gaps go to the `issue-triage` skill
   for filing or updating.

## Validation
- Every gap has (a) evidence, (b) a north-star/docs reference, (c) user impact.
- Every regression names the `VALIDATION_COMMANDS.md` expectation it violates.
- Dedupe search results are recorded (issue numbers checked).
- No gap duplicates `KNOWN_LIMITATIONS.md`, `REJECTED_IDEAS.md`, or an open issue.

## Output format
Ranked gap list. Per gap:
- Title (one line, actionable)
- Type: `regression` or `product-gap`
- Now: command → observed result
- Should: reference (`NORTH_STAR.md` section, doc path, or expected count)
- User impact (one sentence)
- Severity class (1–5) and dedupe note (`new` / `extends #<n>` / `known limitation`)

# Skill: AI Evaluation — Martenweave

## When to use
You are changing or reviewing AI-adjacent behavior — prompts, context building, provider adapters, agent loop, telemetry — and must evaluate it deterministically instead of by vibes.

## Inputs
- The `src/modelops_core/ai/` change under test (diff or branch)
- A model repository path and fixture notes for proposal scenarios
- Optional: a configured provider for manual runs (never required for gates)

## Read first
1. `src/modelops_core/ai/provider_adapter.py` — `NoProviderAdapter`, `AIContextBundle.scrub()`, `ProviderOutputValidator`.
2. `src/modelops_core/ai/patch_proposal_service.py`, `context_builder.py`, `prompt_registry.py`, and `prompts/*.yaml`.
3. `docs/ai/ai-permission-policy.md` — risk tiers 0–4 and channel ceilings.
4. `docs/ai/ai-evaluation-strategy.md` — eval cases and metrics (strategy reference).
5. `docs/factory/policies/AGENT_PREVENTIONS.md` (P9) — never fabricate evidence.

## Do not do
- Do not claim AI accuracy or quality numbers without an evaluation run behind them (P9); "looks reasonable" is not evidence.
- Do not let a no-provider run produce a real proposal: the contract is refuse-to-guess — non-zero exit, `proposal == null`, explicit assumptions.
- Do not weaken guardrail or telemetry assertions to make an AI change pass (P1).
- Do not cite `modelops eval ai` as existing — it is a planned command in the strategy doc, not implemented.
- Do not include raw dataset rows in AI context unless `--include-raw-samples` was explicitly passed; `scrub()` must strip them by default.

## Procedure
1. **Verify the no-silent-mutation contract** (also demo step 9, gate G8):
   ```bash
   .venv/bin/martenweave propose-patch --from <note.md> --repo <path> --dry-run --json
   ```
   With no provider configured this must exit non-zero with `proposal == null` and non-empty `assumptions`. `NoProviderAdapter` output is always marked `created_by=no_provider_scaffold` and carries a "deterministic scaffold" assumption — never presented as model truth.
2. **Run the deterministic test surfaces**:
   ```bash
   .venv/bin/python -m pytest tests/test_ai_patch_proposal_service.py tests/test_agent_loop.py \
       tests/test_ai_usage_telemetry.py tests/test_guardrails.py -q
   ```
   Add `tests/test_ai_context_builder.py` and `tests/test_context_builder.py` for prompt/context changes.
3. **Prompt/context changes**: edit `prompts/*.yaml` through `prompt_registry.py` conventions; re-run the context-builder tests; confirm `AIContextBundle.scrub()` still removes raw samples and telemetry event shapes still pass `test_ai_usage_telemetry.py`.
4. **Evaluate against the strategy metrics** (`docs/ai/ai-evaluation-strategy.md`): structure (valid JSON / schema match), reference validity (every cited object ID exists — enforced by `ProviderOutputValidator` against the ID pattern and registered types), safety (no destructive ops, no PII), completeness, assumption quality (assumptions explicit). Run provider-agnostic: `NoProviderAdapter` and mock providers for gates; a real provider is optional and manual.
5. **Check permission tiers**: the change must respect channel ceilings from `ai-permission-policy.md` — CLI max Tier 3 (with `--yes`), API max Tier 2, MCP max Tier 2 (propose, not apply). Tier 4 behavior (direct canonical mutation, auto-apply without approval, exfiltration) is forbidden in every channel.
6. **Record evidence**: fixture used, commands, exact counts. Unverified behavior is reported as unverified (P9).

## Validation
- The four test surfaces above pass; guardrails tests unchanged or strengthened.
- No-provider contract reproduced by the command in step 1 (non-zero exit, `proposal == null`).
- Every AI-behavior claim in the closeout cites a command and output actually run this session.
- Channel ceilings hold for any new AI surface (API/MCP contract changes are L3 — stop and request approval).

## Output format
Return:
- Test surfaces run with pass/fail counts
- Contract check result (command, exit code, `proposal` value)
- Metrics observed per strategy (structure, reference validity, safety, completeness, assumptions)
- Claims made, each with its evidence command
- Limitations: what was not evaluated (e.g. no real-provider run)

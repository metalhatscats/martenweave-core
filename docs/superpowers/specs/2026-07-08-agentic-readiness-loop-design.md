# Design: Agentic Readiness Loop

> Date: 2026-07-08
> Author: Product Owner / Agent
> Scope: martenweave-core
> Status: Draft

## Problem

The `PRODUCT_EXPLORER_AUDIT.md` (v0.4.1) identifies trust-breaking gaps at the edges of the user journey:

1. `gaps --check-model` reports false-positive `MODEL_ATTRIBUTE_MISSING_SOURCE` gaps.
2. `profile-dataset` updates the JSON profile but not the SQLite index used by `health`/`scorecard`.
3. `scorecard` marks zero-coverage metrics as `pass` and prints `Untitled Repository`.
4. There is no single command that answers "is this repository ready for a pilot demo?".
5. Detected gaps cannot be promoted to trackable `Issue` objects or GitHub issue drafts in one step.

These are P0/P1 blockers for a customer pilot. The core engine works; the trust surface does not.

## Goal

Add an `agent readiness` command that runs a deterministic gate suite and, for every failing gate, creates human-reviewable artifacts (`Issue`, `PatchProposal`, notification event, GitHub issue draft) instead of silently printing misleading output.

The agent never edits canonical model objects directly. All mutations flow through the existing proposal-first pipeline.

## In-scope

- New `ReadinessAgent` service in `src/modelops_core/agents/readiness.py`.
- New CLI command `martenweave agent readiness --repo <path> --profile demo|pilot|release --dry-run --json`.
- Deterministic gates backed by existing services:
  - `validate_objects` — validation errors/warnings.
  - `check_index_freshness` — stale generated index.
  - `generate_repository_health` — dataset profile/index sync.
  - `generate_scorecard` — zero-coverage-as-pass and repository naming.
  - `validate_patch_proposal` on open proposals — invalid open proposals.
  - `compute_proposal_risk` on open proposals — high-risk unapproved proposals.
  - ownership coverage on active objects.
- Artifact generation:
  - One `Issue` canonical file per readiness blocker (in `model/issues/`).
  - One aggregated `PatchProposal` when a blocker has a clear deterministic fix (e.g., scorecard metric rule fix, repository name read fix).
  - Notification events for affected object owners.
  - GitHub issue draft in `generated/issues/`.
- Dry-run support that reports intended artifacts without writing files.

## Out-of-scope

- Automatic application of fixes to canonical files.
- External system write-back (SAP, Jira, etc.).
- Chatbot or interactive workflow engine.
- New AI provider or non-deterministic inference.

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│ CLI: martenweave agent readiness --profile pilot            │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ ReadinessAgent.run(profile)                                  │
│  1. Run gates using existing report/validation services      │
│  2. De-duplicate findings by (code, object_id)               │
│  3. For each blocker:                                        │
│     - create Issue object (dry-run aware)                    │
│     - if fixable deterministically, add PatchProposal op     │
│  4. Write aggregated PatchProposal if ops exist              │
│  5. Emit notification events                                 │
│  6. Generate GitHub issue draft                              │
│  7. Return ReadinessResult                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ Outputs: Issue files, PatchProposal, draft issue, events,   │
│          readiness report                                    │
└─────────────────────────────────────────────────────────────┘
```

## Gate definitions

### Gate: validation_errors
- **Trigger:** any `ERROR` severity validation result.
- **Issue type:** `validation_error`.
- **Proposal op:** none (human must decide).

### Gate: validation_warnings_high_volume
- **Trigger:** >20 warnings of the same code (methodology noise threshold).
- **Issue type:** `methodology_noise`.
- **Proposal op:** none.

### Gate: stale_index
- **Trigger:** `check_index_freshness().fresh is False`.
- **Issue type:** `stale_index`.
- **Proposal op:** none; report suggests `build-index`.

### Gate: profile_index_mismatch
- **Trigger:** `health` reports datasets with profile count < registered dataset sources.
- **Issue type:** `profile_index_mismatch`.
- **Proposal op:** trigger lightweight `build-index` is out of scope; proposal op is `update_object` on a generated README note (none).

### Gate: scorecard_zero_coverage_pass
- **Trigger:** scorecard metric value is 0.0 and status is `pass`.
- **Issue type:** `scorecard_metric_logic`.
- **Proposal op:** `update_object` on the metric definition or scorecard service fix is out of artifact scope; create Issue only.

### Gate: scorecard_untitled_repository
- **Trigger:** scorecard uses fallback "Untitled Repository" while config has a name.
- **Issue type:** `scorecard_repository_name`.
- **Proposal op:** none (fix is in code, not model).

### Gate: gaps_check_model_false_positive
- **Trigger:** `gaps --check-model` reports `MODEL_ATTRIBUTE_MISSING_SOURCE` for attributes that have linked FieldEndpoints.
- **Issue type:** `gap_false_positive`.
- **Proposal op:** none (fix is in gap detection service).

### Gate: invalid_open_proposal
- **Trigger:** open PatchProposal with `validation_status == "invalid"`.
- **Issue type:** `invalid_open_proposal`.
- **Proposal op:** none (human must reject or fix).

### Gate: high_risk_unapproved_proposal
- **Trigger:** open PatchProposal with risk level `high` and no approved ChangeRequest.
- **Issue type:** `high_risk_unapproved_proposal`.
- **Proposal op:** none.

### Gate: active_object_missing_owner
- **Trigger:** object status is `active` and no `business_owner`, `technical_owner`, `data_steward`, or `owner` field is set.
- **Issue type:** `missing_owner`.
- **Proposal op:** none (human must assign).

## CLI contract

```bash
martenweave agent readiness --repo ./my-model --profile pilot
martenweave agent readiness --repo ./my-model --profile demo --dry-run
martenweave agent readiness --repo ./my-model --profile release --json
```

### JSON output

```json
{
  "profile": "pilot",
  "ready": false,
  "gate_count": 9,
  "failed_gates": ["scorecard_zero_coverage_pass", "gaps_check_model_false_positive"],
  "issues_created": ["ISS-READINESS-001"],
  "proposal_created": null,
  "draft_issue_path": ".../generated/issues/readiness-2026-07-08.md",
  "notification_event_ids": ["NE-..."],
  "blockers": [
    {
      "gate": "scorecard_zero_coverage_pass",
      "severity": "high",
      "message": "Scorecard marks evidence_coverage 0.0 as pass",
      "object_id": null,
      "issue_id": "ISS-READINESS-001"
    }
  ]
}
```

## Files to create / modify

1. `src/modelops_core/agents/readiness.py` — `ReadinessAgent`, `ReadinessInput`, `ReadinessResult`, gate functions.
2. `src/modelops_core/agents/__init__.py` — export `ReadinessAgent`, `ReadinessInput`, `ReadinessResult`.
3. `src/modelops_core/cli.py` — add `agent readiness` subcommand.
4. `tests/test_readiness_agent.py` — unit and CLI tests.
5. `docs/agent-modeling-guide.md` — document `agent readiness`.
6. `tests/test_cli_structure.py` — add `readiness` to expected `agent` subcommands.

## Acceptance criteria

- `pytest tests/test_readiness_agent.py -v` passes.
- `ruff check src/modelops_core/agents tests/test_readiness_agent.py src/modelops_core/cli.py` is clean.
- `martenweave agent readiness --repo examples/simple_product_model --dry-run` runs without errors.
- The command correctly identifies the scorecard zero-coverage-pass issue on `examples/simple_product_model`.
- Dry-run mode does not write canonical files.
- Full test suite passes.

## Dependencies

Reuses existing services; no new external dependencies.

# Agent-Loop Command Design

> **Goal:** Add a closed-loop `agent-loop` CLI command and MCP prompt that turns a free-text modeling goal into a validated, impact-assessed PatchProposal through iterative propose → validate → refine cycles, without ever applying changes automatically.

## Motivation

Current AI-assisted workflows require the user to run `propose-patch`, read validation errors, manually rewrite the note, and try again. The agent loop automates that cycle: it proposes a change, checks validation and impact, feeds findings back into the next proposal, and stops when the proposal is valid or when it cannot make progress.

## Scope

In scope:
- A new `martenweave agent-loop` CLI command.
- A new MCP prompt `run_agent_loop`.
- A deterministic state machine with hard-coded tool selection.
- Integration with existing services: validation, search, trace, propose, impact, dry-run.
- Telemetry and audit events for every iteration.

Out of scope:
- Fully autonomous application of proposals (still requires human approval).
- Natural-language planning beyond the provided goal.
- Multi-goal orchestration.

## User Interface

### CLI

```bash
martenweave agent-loop \
  --goal "Add a new Attribute for Customer Credit Group mapped to KNVV-KDGRP" \
  --repo examples/customer_bp_model \
  --max-iterations 5 \
  --json
```

Output with `--json`:

```json
{
  "goal": "Add a new Attribute for Customer Credit Group mapped to KNVV-KDGRP",
  "iterations": 3,
  "final_status": "valid_proposal",
  "proposal_id": "PP-AGENT-20260708-001",
  "proposal_path": "examples/customer_bp_model/model/patch-proposals/PP-AGENT-20260708-001.md",
  "validation_status": "valid",
  "impact": {
    "high_risk": false,
    "requires_approval": false,
    "affected_objects_count": 4
  },
  "assumptions": [...],
  "human_checks": [...],
  "log": [
    {"iteration": 1, "action": "propose", "proposal_id": "PP-AGENT-20260708-001", "validation_status": "invalid", "errors": [...]},
    {"iteration": 2, "action": "refine", "proposal_id": "PP-AGENT-20260708-001", "validation_status": "invalid", "errors": [...]},
    {"iteration": 3, "action": "refine", "proposal_id": "PP-AGENT-20260708-001", "validation_status": "valid"}
  ]
}
```

Final statuses:
- `valid_proposal` — proposal passed deterministic validation.
- `invalid_proposal` — max iterations reached without a valid proposal.
- `no_progress` — validation errors did not change between iterations.
- `high_risk` — proposal is valid but requires approval via ChangeRequest.
- `failed` — proposal generation failed entirely.

### MCP Prompt

A new prompt `run_agent_loop` guides an MCP client to execute the same loop using the available tools.

## State Machine

```
INIT
  │
  ▼
PROPOSE ──(proposal generated)──▶ VALIDATE
  │                                  │
  │(no proposal)                     │(valid)
  ▼                                  ▼
FAILED                          IMPACT
                                     │
                                     │(high risk)
                                     ▼
                                HIGH_RISK
                                     │
                                     │(low risk)
                                     ▼
                                    DONE
  │                                  │
  │(invalid)                         │
  ▼                                  │
REFINE ──(no progress)───────────────┘
  │
  ▼
NO_PROGRESS
```

States:
1. **INIT** — parse goal, record audit event, set iteration counter to 0.
2. **PROPOSE** — call `build_patch_proposal_from_note` with the current note.
   - If no proposal generated, transition to FAILED.
3. **VALIDATE** — inspect `proposal["validation_status"]` and `proposal["validation_results"]`.
   - If valid, transition to IMPACT.
   - If invalid, transition to REFINE.
4. **IMPACT** — call `generate_proposal_impact_report` and `compute_proposal_risk`.
   - If `requires_approval`, transition to HIGH_RISK.
   - Otherwise, transition to DONE.
5. **HIGH_RISK** — final state. Proposal is valid but needs governance.
6. **REFINE** — build a refined note that includes the original goal plus the validation errors from the previous iteration. Increment iteration counter.
   - If iteration counter > max_iterations, transition to INVALID_PROPOSAL.
   - If validation errors are identical to previous iteration, transition to NO_PROGRESS.
   - Otherwise, transition to PROPOSE.
7. **DONE**, **FAILED**, **INVALID_PROPOSAL**, **NO_PROGRESS** — terminal states.

## Tool Selection

The loop uses these existing services directly (not via MCP tool calls in CLI mode):

| Tool | Purpose |
|---|---|
| `validate_objects` / `validate_model` | Baseline repo validity before first propose. |
| `search_objects` | Discover existing objects related to the goal (optional pre-step). |
| `build_patch_proposal_from_note` | Generate/refine the proposal. |
| `generate_proposal_impact_report` | Assess downstream impact. |
| `compute_proposal_risk` | Determine if approval is required. |
| `dry_run_patch_proposal` | Preview what applying would do. |

## Note Refinement Prompt

When validation fails, the loop constructs a refined note:

```text
Original goal: <goal>

Previous proposal <proposal_id> had these validation errors:
- <error message> (object: <object_id>, code: <code>)
- ...

Please fix these errors and regenerate the proposal. Do not change the intent.
```

If impact is high-risk, the loop adds:

```text
The proposal affects <N> downstream objects. Ensure all affected object IDs are listed and the change is minimal.
```

## Safety Boundaries

- The loop never calls `apply_patch_proposal` or writes to canonical files outside `model/patch-proposals/`.
- Each iteration is logged as an audit event with actor `agent-loop`.
- The loop stops at `max_iterations` to avoid runaway proposals.
- The loop stops if validation errors do not change between iterations (no progress).

## Files

- `src/modelops_core/ai/agent_loop.py` — core state machine and loop logic.
- `src/modelops_core/cli.py` — `agent-loop` CLI command.
- `src/modelops_core/mcp_server.py` — `run_agent_loop` prompt.
- `tests/test_agent_loop.py` — unit tests for the state machine.
- `tests/test_cli.py` — CLI invocation tests.

## Acceptance Criteria

- [ ] `martenweave agent-loop --goal "..." --repo PATH` produces a PatchProposal for valid goals.
- [ ] Invalid goals are refined up to `max_iterations` and then report failure with reasons.
- [ ] Valid but high-risk proposals are flagged and require ChangeRequest creation.
- [ ] No canonical files are mutated automatically.
- [ ] Every iteration writes an audit event.
- [ ] `pytest -q && ruff check .` passes.

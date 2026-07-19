# Rejected Ideas

> Ideas already evaluated and decided **against**, with the deciding source. Agents
> must not re-propose these as new work. If new evidence genuinely changes the
> trade-off, open an `[ADR]` issue instead of implementing.

## Product-shape rejections

- **Generic chatbot / broad chat mode** — rejected; the Workbench "model assistant"
  is deterministic search over the index, not an LLM chat.
  Source: `docs/architecture/AI_PATCH_WORKFLOW.md` ("Do not build autonomous agents,
  broad chat mode, direct canonical writes").
- **Workflow engine as primary architecture** — rejected; approval gates and
  statuses only. Source: `docs/architecture/MODEL_REPOSITORY_SPEC.md` §37.
- **SaaS / hosted multi-tenant platform** — rejected; local-first is a core
  principle. Source: `README.md`, `docs/product/MVP_SCOPE.md` §3.2 (9).
- **Autonomous AI apply / auto-approving agents** — rejected; fully autonomous apply
  is excluded. Source: `docs/superpowers/specs/2026-07-08-agent-loop-design.md`,
  `docs/ai/ai-permission-policy.md`.
- **Master-data record storage / raw data lake** — rejected; Martenweave governs
  model knowledge, not business records. Source: MODEL_REPOSITORY_SPEC §37.
- **Direct SAP write-back / transport management** — rejected permanently.
  Source: `README.md`, MVP_SCOPE §3.2.
- **Neo4j / Kafka / event streaming / enterprise graph infrastructure** — rejected
  for MVP and current roadmap. Source: MVP_SCOPE §3.2 (8).
- **Unreviewed AI memory** — AI-generated content enters the model only through
  reviewed proposals. Source: MODEL_REPOSITORY_SPEC §37.
- **Jira / Confluence / SolMan / Cloud ALM direct integrations** — rejected for
  current scope; integrations are I/O channels (issue drafts, bundles), not live
  sync. Source: MVP_SCOPE §3.2 (4), `docs/architecture/INTEGRATION_BOUNDARIES.md`.
- **Full SAP customizing extraction / all BP roles / all domains at once** —
  rejected as scope creep; narrow slices prove the model.
  Source: MVP_SCOPE §3.2 (13–15), §7.1.

## Factory-scope rejections

- **Separate orchestration platform for the AI factory** — rejected by the factory
  charter itself: the factory is versioned docs + skills + one stdlib harness +
  GitHub issues. No daemons, no databases, no job servers.
- **Website as a marketing-first surface with aspirational claims** — rejected;
  every public claim must match verified Core behavior (website-claim-verification
  skill; production parity tests).

## Commercial-direction notes (context, not commitments)

The 2026-06 due-diligence reports (`AGENT_1..4_*.md`,
`COMMERCIAL_DUE_DILIGENCE_MARTENWEAVE.md`) judged the commercial model unvalidated
and suggested consulting-led adoption. These are historical analysis artifacts,
not product direction; agents must not treat them as scope.

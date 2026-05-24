# AI Runtime Architecture

## Runtime Flow

```
User Intent
    |
    v
Workflow Router  ←--- maps intent to workflow type
    |
    v
Context Builder  ←--- selects, compacts, redacts evidence
    |
    v
Retrieval / Index Lookup  ←--- SQLite, JSONL, optional vector
    |
    v
Prompt Template  ←--- versioned, workflow-specific
    |
    v
Provider Adapter  ←--- OpenAI, Anthropic, local, stub
    |
    v
Structured Output Parser  ←--- validates against schema
    |
    v
PatchProposal / Report  ←--- deterministic validation
    |
    v
Telemetry / Cache / Audit  ←--- records interaction
```

## Workflow Types

| Workflow | Router Key | Context Builder | Prompt |
|---|---|---|---|
| file-to-model | `file_upload` | Dataset profile + schema hints | `prompts/file_to_model_v1.yaml` |
| chat-to-model | `chat_message` | User query + relevant objects | `prompts/chat_to_model_v1.yaml` |
| explain trace | `trace_request` | Object + BFS lineage | `prompts/explain_trace_v1.yaml` |
| explain impact | `impact_request` | Object + impact report | `prompts/explain_impact_v1.yaml` |
| suggest metadata | `gap_request` | Gap analysis results | `prompts/suggest_metadata_v1.yaml` |
| suggest LoV/rules | `lov_request` | FieldEndpoint + sample values | `prompts/suggest_lov_v1.yaml` |
| summarize review | `review_request` | PatchProposal + affected objects | `prompts/summarize_review_v1.yaml` |
| create issue draft | `issue_request` | Validation errors + gaps | `prompts/create_issue_v1.yaml` |

## Boundaries

- **Deterministic services** (left of Prompt Template): no AI, no non-determinism
- **AI services** (right of Prompt Template): provider-dependent, validated output
- **Validation** (after parser): deterministic, blocks invalid proposals

## v0.1 Scope

- Workflow router: CLI command mapping
- Context builder: SQLite index queries + compaction
- Retrieval: exact ID lookup + structured query + relationship expansion
- Prompt templates: YAML files in `src/modelops_core/ai/prompts/`
- Provider adapter: `NoProviderAdapter` stub + OpenAI adapter skeleton
- Structured output: Pydantic models (PatchProposal, Report)
- Telemetry: audit_events.jsonl entries

## Later

- Vector retrieval over search_documents.jsonl
- Prompt evaluation framework
- Multi-provider routing
- Streaming responses

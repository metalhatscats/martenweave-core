<!-- modelops-freshness-ignore: all -->

# AI Usage Telemetry and Token Accounting Design

## Goal

Track AI provider usage, token consumption, request counts, latency, errors, and estimated cost so Martenweave users can understand and control agentic workflows.

## Scope

This document covers:

- Telemetry event schema for every AI call
- Provider-specific token accounting strategies
- Cost estimation without hardcoded secrets
- Storage strategy (append-only JSONL + optional SQLite)
- Privacy boundaries (no raw prompts or responses by default)
- Integration with existing audit and usage-report infrastructure
- CLI reporting and future dashboard design

## Telemetry Event Schema

Every AI call — whether from `propose-patch`, `infer-model`, or future AI-assisted analysis — emits a single `ai_call` telemetry event.

```json
{
  "event_id": "ai-abc123def456",
  "event_type": "ai_call",
  "timestamp": "2026-05-25T12:34:56Z",
  "workflow": "patch_proposal",
  "command": "propose-patch",
  "actor": "system",
  "provider": "kimi",
  "model": "kimi-latest",
  "input_tokens": 1240,
  "output_tokens": 380,
  "total_tokens": 1620,
  "token_source": "exact",
  "estimated_cost_usd": 0.00486,
  "cost_confidence": "high",
  "latency_ms": 3420,
  "status": "success",
  "error_type": null,
  "proposal_id": "PP-2026-001",
  "change_request_id": null,
  "source_id": null,
  "request_id": "req-kimi-xyz789",
  "session_id": "sess-uuid-123",
  "metadata": {
    "context_length": 1240,
    "output_length": 380,
    "temperature": 0.2,
    "max_tokens": 4096,
    "note_truncated": false
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|---|---|---|---|
| `event_id` | string | Yes | Unique telemetry event ID (`ai-{hex}`) |
| `event_type` | string | Yes | Always `ai_call` |
| `timestamp` | ISO-8601 | Yes | UTC timestamp of response completion |
| `workflow` | string | Yes | High-level workflow: `patch_proposal`, `gap_analysis`, `model_inference`, `mcp_tool` |
| `command` | string | Yes | CLI command or tool name that triggered the call |
| `actor` | string | Yes | `system`, `user`, or `mcp_agent` |
| `provider` | string | Yes | Provider identifier: `kimi`, `google`, `openai`, `local`, `none` |
| `model` | string | Yes | Model identifier used for the call |
| `input_tokens` | int | Yes | Tokens in the prompt/context |
| `output_tokens` | int | Yes | Tokens in the model response |
| `total_tokens` | int | Yes | `input_tokens + output_tokens` |
| `token_source` | string | Yes | `exact` (provider reported), `estimated` (heuristic), `unknown` |
| `estimated_cost_usd` | float | No | Estimated cost in USD |
| `cost_confidence` | string | No | `high`, `medium`, `low` based on token_source and price freshness |
| `latency_ms` | int | Yes | Round-trip latency in milliseconds |
| `status` | string | Yes | `success`, `error`, `timeout`, `rate_limited`, `cancelled` |
| `error_type` | string | No | `validation_error`, `provider_error`, `timeout`, `rate_limit`, `content_filter` |
| `proposal_id` | string | No | Linked PatchProposal ID |
| `change_request_id` | string | No | Linked ChangeRequest ID |
| `source_id` | string | No | Linked import source or dataset ID |
| `request_id` | string | No | Provider-specific request ID for debugging |
| `session_id` | string | No | Session grouping ID for multi-call workflows |
| `metadata` | object | No | Provider-specific params (temperature, max_tokens, truncation flags) |

## Provider-Specific Token Accounting

Different providers report token usage with different fidelity. The telemetry layer normalizes all providers into the common schema.

### Exact Token Reporting

Providers that return token counts in their API response:

| Provider | API Field | Notes |
|---|---|---|
| **Kimi / Moonshot** | `usage.prompt_tokens`, `usage.completion_tokens` | Exact counts returned in response body |
| **OpenAI** | `usage.prompt_tokens`, `usage.completion_tokens` | Exact counts |
| **Google Gemini** | `usageMetadata.promptTokenCount`, `usageMetadata.candidatesTokenCount` | Exact counts |
| **Anthropic Claude** | `usage.input_tokens`, `usage.output_tokens` | Exact counts |

### Estimated Token Reporting

Providers or deployment modes where exact tokens are unavailable:

| Scenario | Estimation Method | Accuracy |
|---|---|---|
| **Local / self-hosted models** (Ollama, vLLM, llama.cpp) | Character-count heuristic: `tokens ≈ chars / 4` | Medium (`±20%`) |
| **Streaming responses without usage headers** | Accumulate streamed chunks; estimate if no final usage | Low (`±30%`) |
| **NoProviderAdapter** | Always `0` tokens; `token_source: unknown` | N/A |
| **Cached / replayed responses** | Use original token count if available; else `0` | Varies |

### Estimation Heuristic

```python
def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0
    # Conservative estimate: 1 token per 3.5 characters for multilingual text
    return max(1, int(len(text) / 3.5))
```

When `token_source` is `estimated`, `cost_confidence` is downgraded to `medium` or `low`.

## Cost Estimation

Cost is calculated per call using a provider-model price table loaded from configuration. No prices are hardcoded in source code.

### Price Configuration

```yaml
# modelops.config.yaml
ai:
  provider: kimi
  model: kimi-latest
  telemetry:
    enabled: true
    store_in_index: true
  pricing:
    kimi:
      kimi-latest:
        input_per_1m: 1.0
        output_per_1m: 3.0
      kimi-k1:
        input_per_1m: 2.0
        output_per_1m: 8.0
    google:
      gemini-2.5-pro:
        input_per_1m: 1.25
        output_per_1m: 10.0
    openai:
      gpt-4o:
        input_per_1m: 2.50
        output_per_1m: 10.0
    local:
      default:
        input_per_1m: 0.0
        output_per_1m: 0.0
```

### Cost Calculation

```python
def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    provider: str,
    model: str,
    pricing_config: dict,
) -> tuple[float, str]:
    provider_pricing = pricing_config.get(provider, {})
    model_pricing = provider_pricing.get(model, provider_pricing.get("default", {}))
    input_price = model_pricing.get("input_per_1m", 0.0)
    output_price = model_pricing.get("output_per_1m", 0.0)
    cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    confidence = "high" if input_price > 0 else "low"
    return cost, confidence
```

### Cost Confidence Rules

| Condition | `cost_confidence` |
|---|---|
| Exact tokens + known price | `high` |
| Estimated tokens + known price | `medium` |
| Exact tokens + unknown/default price | `medium` |
| Estimated tokens + unknown price | `low` |
| Local provider (no cloud cost) | `high` (cost is $0.00) |

## Storage Strategy

### Primary: Append-Only JSONL

AI telemetry events are written to `generated/ai_telemetry.jsonl` as an append-only log, separate from the general audit log to keep query patterns distinct.

```python
from pathlib import Path
import json

class AITelemetryService:
    def __init__(self, repo_root: Path) -> None:
        self.log_path = repo_root / "generated" / "ai_telemetry.jsonl"

    def emit(self, event: dict) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a") as fh:
            fh.write(json.dumps(event, default=str) + "\n")
```

### Secondary: SQLite Index (Optional)

When `telemetry.store_in_index: true` is set in config, telemetry events are also written to the generated SQLite index in a new `ai_telemetry` table. This enables fast aggregation queries for dashboards.

```sql
CREATE TABLE ai_telemetry (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT,
    workflow TEXT,
    command TEXT,
    provider TEXT,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    token_source TEXT,
    estimated_cost_usd REAL,
    cost_confidence TEXT,
    latency_ms INTEGER,
    status TEXT,
    error_type TEXT,
    proposal_id TEXT,
    session_id TEXT
);

CREATE INDEX idx_ai_telemetry_session ON ai_telemetry(session_id);
CREATE INDEX idx_ai_telemetry_provider ON ai_telemetry(provider, model);
CREATE INDEX idx_ai_telemetry_time ON ai_telemetry(timestamp);
```

### Retention

- JSONL logs are never truncated by default (append-only).
- A future `modelops telemetry compact` command may archive old events to monthly JSONL files.
- No PII or raw content is stored, so retention policy is driven by disk usage, not privacy.

## Privacy and Safety

### Default: No Raw Content

By default, telemetry events **do not** include:
- Raw prompt text
- Raw model response text
- User notes or dataset samples
- Any data that could reconstruct the input or output

### Opt-In Content Logging

For debugging, a `telemetry.log_content_hashes: true` option may store SHA-256 hashes of prompts and responses for correlation without exposing content.

```yaml
ai:
  telemetry:
    enabled: true
    store_in_index: true
    log_content_hashes: false
```

### Redaction Rules

| Field | Default | Redaction |
|---|---|---|
| `note` (from context) | Never stored | Truncated to 0 chars |
| `prompt` | Never stored | Truncated to 0 chars |
| `response` | Never stored | Truncated to 0 chars |
| `metadata.context_length` | Stored | Token count only |
| `metadata.output_length` | Stored | Token count only |

## Integration with Existing Infrastructure

### Audit Event Bridge

AI telemetry events are related to but separate from audit events. For high-level workflow tracking, the existing audit event can reference the telemetry event ID:

```json
{
  "event_id": "audit-def789",
  "event_type": "proposal_created",
  "actor": "system",
  "status": "success",
  "command": "propose-patch",
  "proposal_id": "PP-2026-001",
  "metadata": {
    "ai_telemetry_event_id": "ai-abc123def456",
    "ai_provider": "kimi",
    "ai_model": "kimi-latest",
    "ai_tokens": 1620
  }
}
```

### Usage Report Extension

The existing `UsageReport` aggregates AI telemetry directly instead of scraping audit metadata.

```python
@dataclass
class AIUsageSummary:
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_estimated_cost_usd: float = 0.0
    calls_by_provider: dict[str, int] = field(default_factory=dict)
    calls_by_model: dict[str, int] = field(default_factory=dict)
    calls_by_status: dict[str, int] = field(default_factory=dict)
    avg_latency_ms: float = 0.0
    error_rate_percent: float = 0.0
```

### Provider Adapter Integration

Every `AIProviderAdapter` implementation is responsible for emitting telemetry before returning candidates.

```python
class KimiProviderAdapter:
    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        start = time.perf_counter()
        try:
            response = self._call_api(context)
            latency_ms = int((time.perf_counter() - start) * 1000)
            tokens = response.usage
            telemetry.emit({
                "provider": "kimi",
                "model": self.model,
                "input_tokens": tokens.prompt_tokens,
                "output_tokens": tokens.completion_tokens,
                "token_source": "exact",
                "latency_ms": latency_ms,
                "status": "success",
                ...
            })
            return self._parse_candidates(response)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            telemetry.emit({
                "status": "error",
                "error_type": self._classify_error(exc),
                "latency_ms": latency_ms,
                ...
            })
            raise
```

The `NoProviderAdapter` emits a telemetry event with `provider: none`, `token_source: unknown`, and `status: success` so that usage reports can distinguish between "no AI configured" and "AI not called."

## CLI Reporting

### `modelops telemetry` Command Design

```bash
# Show summary
modelops telemetry --repo ./my-model

# Show last N calls
modelops telemetry --last 20 --repo ./my-model

# Filter by provider
modelops telemetry --provider kimi --repo ./my-model

# Filter by workflow
modelops telemetry --workflow patch_proposal --repo ./my-model

# JSON output
modelops telemetry --json --repo ./my-model

# Export to CSV
modelops telemetry --export-csv ./telemetry.csv --repo ./my-model
```

### Example Output

```
AI Telemetry Summary
  Total calls:        42
  Total input tokens: 52,340
  Total output tokens: 14,280
  Estimated cost:     $0.12
  Avg latency:        3.2s
  Error rate:         2.4%

By Provider
  kimi:    38 calls ($0.11)
  google:   4 calls ($0.01)

By Status
  success:        41
  error:           1 (timeout)
```

## Dashboard and Future UI

The SQLite `ai_telemetry` table is designed to power future dashboards:

| Metric | SQL |
|---|---|
| Daily cost | `SELECT date(timestamp), sum(estimated_cost_usd) FROM ai_telemetry GROUP BY date(timestamp)` |
| Token burn rate | `SELECT sum(total_tokens) / sum(latency_ms) * 1000 FROM ai_telemetry` |
| Error rate by provider | `SELECT provider, 100.0 * sum(status='error') / count(*) FROM ai_telemetry GROUP BY provider` |
| Most expensive workflows | `SELECT workflow, sum(estimated_cost_usd) FROM ai_telemetry GROUP BY workflow ORDER BY 2 DESC` |

## Multi-Provider Support Matrix

| Provider | Exact Tokens | Cost Config | Status |
|---|---|---|---|
| Kimi / Moonshot | Yes | `kimi.*` | Supported |
| Google Gemini | Yes | `google.*` | Supported |
| OpenAI | Yes | `openai.*` | Supported |
| Anthropic Claude | Yes | `anthropic.*` | Supported |
| Local (Ollama, vLLM) | Estimated | `local.*` | Supported |
| NoProviderAdapter | Unknown | `none` | Supported |
| Future providers | Varies | User-configurable | Extensible |

## Implementation Path

### Phase 1 — Design (this document)

- Schema, storage, privacy, and CLI design
- No runtime dependencies added

### Phase 2 — Core Telemetry Service

- `modelops_core.telemetry` module:
  - `AITelemetryEvent` dataclass
  - `AITelemetryService` (JSONL writer)
  - `TelemetryCostCalculator` (pricing config loader)
  - `TokenEstimator` (heuristic for local providers)
- Integrate into `AIProviderAdapter` protocol
- Update `NoProviderAdapter` to emit telemetry
- Update `usage_report_service` to read from telemetry JSONL

### Phase 3 — Index Integration

- Extend `build_index` to optionally create `ai_telemetry` SQLite table
- Add telemetry fields to `modelops.config.yaml` schema

### Phase 4 — CLI Command

- Implement `modelops telemetry` command with filtering and export

### Phase 5 — Dashboard

- Future web UI consuming SQLite aggregates

## Dependency Strategy

| Dependency | Scope | Notes |
|---|---|---|
| `modelops_core` | Required | Telemetry module added to core |
| No new external packages | — | Uses existing `json`, `sqlite3`, `pathlib` |

Telemetry is a core concern because it tracks usage of core AI features. Unlike MCP (external integration), telemetry lives inside `modelops_core`.

## Acceptance Criteria

- [ ] The telemetry design covers token usage, cost estimation, latency, errors, and workflow attribution.
- [ ] It is privacy-safe by default and avoids raw content capture.
- [ ] It supports Kimi/Moonshot, Google ADK/Gemini path, no-provider scaffold, and future local providers.
- [ ] It can power CLI reports and future UI dashboards.
- [ ] Cost configuration is externalized (config file) without hardcoded secrets or prices.
- [ ] Token estimation heuristics are documented with confidence levels.

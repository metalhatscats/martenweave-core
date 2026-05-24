# AI Provider Architecture

> Martenweave can operate without any AI provider. When configured, AI providers augment deterministic workflows rather than replace them.

---

## Design Goals

1. **Deterministic-first**: All core workflows run without external AI dependencies.
2. **No committed secrets**: API keys are never stored in the repository, logs, or generated artifacts.
3. **Validator-gated**: AI output is always validated before creating PatchProposals or mutating canonical files.
4. **Privacy-scrubbed**: Context sent to providers excludes raw samples by default and minimizes sensitive data.
5. **Swappable**: New providers can be added by implementing a single protocol.

---

## Provider Abstraction

The core interface is `AIProviderAdapter`, a Python Protocol:

```python
class AIProviderAdapter(Protocol):
    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        ...
```

### Context Bundle

`AIContextBundle` carries privacy-scrubbed context to the provider:

| Field | Purpose | Default |
|---|---|---|
| `note` | User-supplied free-text note or prompt | required |
| `dataset_columns` | Column names for dataset-aware proposals | `[]` |
| `dataset_row_count` | Row count hint | `None` |
| `affected_object_ids` | Known affected object IDs | `[]` |
| `domain` | Target domain filter | `None` |
| `include_raw_samples` | Whether raw values may be included | `False` |
| `max_context_length` | Soft cap for context size | `4000` |

The `.scrub()` method returns a copy with `include_raw_samples=False`.

### Candidate Output

`AICandidateOutput` is the structured return type before PatchProposal creation:

| Field | Purpose |
|---|---|
| `proposal_id` | Stable proposal ID |
| `title` | Human-readable title |
| `operations` | List of patch operations |
| `affected_objects` | Object IDs the proposal touches |
| `assumptions` | Assumptions the AI made |
| `human_checks` | Items a human should verify |
| `source_evidence` | Evidence snippet |

---

## Supported Provider Slots (v1)

### 1. No-Provider Deterministic Scaffold

**Module**: `modelops_core.ai.provider_adapter.NoProviderAdapter`

The default when no provider is configured. Uses keyword matching and deterministic rules to generate scaffold proposals. Safe, predictable, and requires no network calls.

**When to use**: Local development, CI, air-gapped environments, or when AI augmentation is not needed.

### 2. Kimi / Moonshot API

**Planned module**: `modelops_core.ai.kimi_adapter.KimiAdapter`

OpenAI-compatible chat completion adapter for Kimi/Moonshot.

**Configuration**:
```bash
MARTENWEAVE_AI_PROVIDER=kimi
MOONSHOT_API_KEY=<your-key>
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1  # optional
MOONSHOT_MODEL=kimi-latest                      # optional
```

**Behavior**:
- Requests structured JSON output for PatchProposal candidates.
- Validates JSON schema before conversion.
- Falls back to `NoProviderAdapter` on timeout, rate limit, or invalid JSON.

### 3. Google ADK / Gemini Path

**Planned module**: `modelops_core.ai.google_adk_adapter.GoogleADKAdapter`

Optional agent-runtime adapter for Google ADK or direct Gemini API.

**Configuration**:
```bash
MARTENWEAVE_AI_PROVIDER=google_adk
GOOGLE_API_KEY=<your-key>
GOOGLE_ADK_MODEL=gemini-2.5-flash             # optional
```

**Behavior**:
- ADK agents call Martenweave services but cannot bypass validators.
- Agent outputs are converted to `AICandidateOutput` and validated.
- See `docs/google-adk-integration.md` for agent-level design.

### 4. Local / Ollama Provider (future)

**Planned module**: `modelops_core.ai.ollama_adapter.OllamaAdapter`

For on-premise or local inference.

**Configuration**:
```bash
MARTENWEAVE_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

---

## Secret Handling Rules

1. **No API keys in repository**: `.env` and `.env.example` contain placeholder names only.
2. **No keys in logs**: All log and audit event paths redact secret-like values.
3. **No keys in generated files**: `generated/` artifacts never include provider credentials.
4. **No keys in examples**: Example configs use `<YOUR_KEY_HERE>` placeholders.
5. **No keys in error messages**: Provider errors surface generic messages ("provider unavailable").

### Redaction Helper

```python
from modelops_core.ai.secrets import redact_secrets

redacted = redact_secrets(text)
```

Known secret patterns:
- `api_key`, `apikey`, `secret`, `token`, `password`
- Values matching `[a-zA-Z0-9_-]{20,}` adjacent to these keys

---

## Environment Variables

| Variable | Purpose | Example |
|---|---|---|
| `MARTENWEAVE_AI_PROVIDER` | Select provider slot | `no_provider`, `kimi`, `google_adk`, `ollama` |
| `MOONSHOT_API_KEY` | Kimi/Moonshot API key | *(redacted in logs)* |
| `MOONSHOT_BASE_URL` | Kimi base URL | `https://api.moonshot.cn/v1` |
| `MOONSHOT_MODEL` | Kimi model name | `kimi-latest` |
| `GOOGLE_API_KEY` | Google/Gemini API key | *(redacted in logs)* |
| `GOOGLE_ADK_MODEL` | Gemini model name | `gemini-2.5-flash` |
| `OLLAMA_BASE_URL` | Ollama endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llama3.1` |
| `MARTENWEAVE_AI_TIMEOUT` | Request timeout (seconds) | `30` |
| `MARTENWEAVE_AI_MAX_RETRIES` | Retry count | `3` |
| `MARTENWEAVE_AI_CONTEXT_LIMIT` | Max context tokens | `4000` |

### `.env.example` (checked in)

```bash
MODELOPS_ENVIRONMENT=development
MODELOPS_LOG_LEVEL=INFO

# AI Provider (optional)
# MARTENWEAVE_AI_PROVIDER=no_provider
# MOONSHOT_API_KEY=<your-key>
# GOOGLE_API_KEY=<your-key>
```

---

## Timeout, Retry, and Rate-Limit Behavior

| Scenario | Behavior |
|---|---|
| Timeout | Raise `AITimeoutError`; fallback to `NoProviderAdapter` if configured |
| Rate limit | Raise `AIRateLimitError`; retry with exponential backoff (1s, 2s, 4s) |
| Invalid JSON | Raise `AIOutputValidationError`; do not create PatchProposal |
| Unsafe operations | Reject candidate if operation type is not in allow-list |
| Structured output failure | Retry once; then fallback to scaffold |

---

## Structured Output Requirements

AI providers must return JSON that can be unmarshalled into `AICandidateOutput`.

Required schema:
```json
{
  "proposal_id": "string",
  "title": "string",
  "operations": [
    {
      "op": "update_object|create_object|add_relationship",
      "object_id": "string",
      "object_type": "string",
      "target_path": "string",
      "after": "any"
    }
  ],
  "affected_objects": ["string"],
  "assumptions": ["string"],
  "human_checks": ["string"],
  "source_evidence": "string"
}
```

The `ProviderOutputValidator` checks:
1. `proposal_id` and `title` are present
2. Operations are in the allow-list
3. No `delete_object` or destructive ops are present
4. Result is passed through `validate_patch_proposal()` before canonical creation

---

## Provider Fallback

The resolution order at runtime:

1. Read `MARTENWEAVE_AI_PROVIDER`.
2. If unset or `no_provider`, use `NoProviderAdapter`.
3. If provider is configured but credentials are missing, log a clear config error and use `NoProviderAdapter`.
4. If provider call fails (timeout, rate limit, invalid output), raise the specific error for the caller; the CLI may choose to fallback.

```python
def get_provider_adapter() -> AIProviderAdapter:
    provider = os.getenv("MARTENWEAVE_AI_PROVIDER", "no_provider")
    if provider == "kimi":
        return KimiAdapter()
    if provider == "google_adk":
        return GoogleADKAdapter()
    return NoProviderAdapter()
```

---

## Integration with Existing Services

### Patch Proposal Flow

```
User note
    → AIContextBundle
        → AIProviderAdapter.generate_candidates()
            → AICandidateOutput
                → ProviderOutputValidator.validate()
                    → PatchProposal (if valid)
                        → validate_patch_proposal()
                            → Canonical file (after human approval)
```

### Validation Gate

AI-generated proposals are never exempt from:
- `validate_patch_proposal()` (deterministic)
- `compute_proposal_risk()` (approval gates)
- `build_index()` (post-apply validation)

---

## Testing Strategy

- All AI provider adapters are tested with **mocked HTTP clients**.
- No tests make real API calls.
- No API keys are present in test fixtures.
- `NoProviderAdapter` is the default in CI and all test runs.

Example test pattern:
```python
def test_kimi_adapter_timeout_fallback(monkeypatch):
    monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "kimi")
    monkeypatch.setenv("MOONSHOT_API_KEY", "fake-key")
    adapter = get_provider_adapter()
    with mock.patch.object(adapter.client, "chat.completions.create", side_effect=TimeoutError):
        with pytest.raises(AITimeoutError):
            adapter.generate_candidates(AIContextBundle(note="test"))
```

---

## Security Checklist

- [ ] No real API keys in `.env.example`
- [ ] No keys in `generated/` artifacts
- [ ] No keys in audit or notification events
- [ ] Provider errors do not leak keys in tracebacks
- [ ] Raw samples excluded from context by default
- [ ] `include_raw_samples=True` requires explicit opt-in
- [ ] All AI-generated changes pass deterministic validation
- [ ] All AI-generated changes pass approval gates if high-risk

---

## Future Work

- Implement `KimiAdapter` (issue #35)
- Implement `GoogleADKAdapter` (issue #37)
- Add `OllamaAdapter` for local inference
- Add provider health-check command: `modelops ai-provider health`
- Add provider-switch CLI flag: `modelops propose-patch --provider kimi`

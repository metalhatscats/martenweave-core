# Google ADK Integration Design

> Optional agent runtime path for Martenweave. Core deterministic workflows remain independent.

---

## Overview

Google ADK (Agent Development Kit) can orchestrate agent workflows around Martenweave services. ADK agents do not replace validators, canonical model files, or approval gates. They are an optional augmentation layer.

---

## Where ADK Fits

```
┌─────────────────────────────────────────┐
│           Agent Orchestration            │
│         (Google ADK / Gemini)           │
├─────────────────────────────────────────┤
│  Martenweave Services (validate, index, │
│  trace, impact, propose, change-request) │
├─────────────────────────────────────────┤
│      Canonical Model Files (model/)      │
│      Deterministic Validation            │
│      Approval Gates                      │
└─────────────────────────────────────────┘
```

ADK agents call downward into Martenweave services. They cannot bypass validation or approval.

---

## Supported ADK Use Cases

### 1. File-to-Model Agent

- **Input**: Dataset file (CSV, XLSX)
- **Output**: `PatchProposal` with inferred model objects
- **Tool calls**:
  - `profile_dataset`
  - `infer_model_from_profile`
  - `validate_patch_proposal`

### 2. Chat-to-Model Proposal Agent

- **Input**: Natural language change request
- **Output**: `PatchProposal` with structured operations
- **Tool calls**:
  - `build_patch_proposal_from_note`
  - `validate_patch_proposal`
  - `compute_proposal_risk`

### 3. Model Gap Analysis Agent

- **Input**: Repository path
- **Output**: Analysis report with suggested issues/decisions
- **Tool calls**:
  - `validate_objects`
  - `generate_analysis_report`
  - `generate_repository_health`

### 4. Change Impact Explanation Agent

- **Input**: Object ID and proposed change
- **Output**: Human-readable impact summary
- **Tool calls**:
  - `generate_impact_report`
  - `trace_object`
  - `generate_proposal_impact_report`

### 5. Documentation / Report Generation Agent

- **Input**: Repository path and report type
- **Output**: Markdown report
- **Tool calls**:
  - `generate_analysis_report`
  - `create_draft_from_validation`
  - `export_model_csv`

---

## Configuration

Environment variables:

```bash
MARTENWEAVE_AI_PROVIDER=google_adk
GOOGLE_API_KEY=<your-key>
GOOGLE_ADK_MODEL=gemini-2.5-flash
```

Optional extra dependency:

```toml
[project.optional-dependencies]
google_adk = ["google-adk>=0.1.0", "google-generativeai>=0.8.0"]
```

The core package does not depend on ADK. Users install it explicitly:

```bash
pip install modelops_core[google_adk]
```

---

## Agent Tool Interface

ADK agents expose tools that wrap Martenweave services. Each tool returns structured JSON, not direct file mutations.

Example tool definition:

```python
def validate_model(repo_path: str) -> dict:
    """Run deterministic validation on a model repository."""
    from modelops_core.validation import validate_objects
    from modelops_core.repository import scan_repository, parse_file

    model_path = Path(repo_path) / "model"
    files = scan_repository(model_path)
    parsed = [parse_file(f) for f in files]
    summary = validate_objects(parsed)

    return {
        "is_valid": summary.is_valid,
        "error_count": summary.error_count,
        "warning_count": summary.warning_count,
        "results": [r.model_dump() for r in summary.results[:20]],
    }
```

---

## Safety Model

1. **Agents cannot bypass validators**: All AI output is validated before PatchProposal creation.
2. **Agents cannot bypass approval gates**: High-risk proposals still require approved ChangeRequests.
3. **Agents cannot mutate canonical files directly**: They create proposals and reports, not direct edits.
4. **Agents work with scrubbed context**: Raw dataset samples are excluded by default.
5. **Missing configuration produces clear errors**:
   ```
   Google ADK is not installed. Install with: pip install modelops_core[google_adk]
   ```

---

## How ADK Differs from a Simple Provider Adapter

| Aspect | Simple Provider Adapter | ADK Agent Path |
|---|---|---|
| **Interface** | Protocol method (`generate_candidates`) | Agent tools + orchestration |
| **State** | Stateless per call | Can maintain session state |
| **Multi-step** | Single request/response | Multi-turn reasoning |
| **Tool use** | Direct API call | LLM chooses tools dynamically |
| **Deployment** | Backend service | Can run as agent runtime |
| **Dependencies** | `httpx` or `openai` | `google-adk` optional extra |

The simple adapter is for direct API calls. ADK is for complex agent workflows that require planning, tool selection, and multi-turn interaction.

---

## Test Strategy

- All ADK-related code is tested with **mocked ADK interfaces**.
- No tests call external Google services.
- Tests verify that:
  - Agent tools return structured JSON
  - Agent outputs pass `ProviderOutputValidator`
  - Agent tools cannot bypass validation or approval gates
  - Missing optional dependencies raise clear errors

Example test:

```python
def test_adk_agent_tool_returns_structured_json(tmp_path: Path):
    result = validate_model(str(tmp_path))
    assert "is_valid" in result
    assert "error_count" in result
```

---

## Implementation Plan

1. **Design document** (this file) — completed
2. **Optional dependency group** — add `[google_adk]` extra in `pyproject.toml`
3. **Agent scaffold module** — `src/modelops_core/ai/google_adk_adapter.py` with conditional import
4. **Tool wrappers** — wrap existing services as ADK-compatible functions
5. **Mocked tests** — verify tool outputs and safety invariants
6. **CLI integration** — `modelops propose-patch --provider google_adk` (future)

---

## Security Checklist

- [ ] `google-adk` is an optional extra, not a base dependency
- [ ] No `GOOGLE_API_KEY` in repository or examples
- [ ] Agent outputs are validated before PatchProposal creation
- [ ] Agent tools cannot bypass approval gates
- [ ] Raw samples are excluded from ADK context by default
- [ ] Missing dependencies produce actionable setup errors

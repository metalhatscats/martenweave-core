# AI Prompt Registry

Prompt templates are versioned, structured, and stored as YAML files so AI behavior is reproducible and testable.

## Location

`src/modelops_core/ai/prompts/*.yaml`

## Template Structure

```yaml
prompt_id: string
version: semantic_version
workflow: workflow_type
system_instructions: >
  Multi-line system prompt.
input_schema:
  type: object
  required: [field1]
  properties: {}
output_schema:
  type: object
  required: [field1]
  properties: {}
safety_rules:
  - "Rule 1"
context_requirements:
  max_objects: integer
  max_tokens: integer
examples:
  - input: {}
    output: {}
```

## Registered Prompts

| Prompt ID | Workflow | Version |
|---|---|---|
| `file_to_model` | file-to-model | 1.0.0 |
| `chat_to_model` | chat-to-model | 1.0.0 |
| `explain_trace` | trace-explanation | 1.0.0 |
| `explain_impact` | impact-explanation | 1.0.0 |
| `suggest_metadata` | metadata-gap-suggestion | 1.0.0 |
| `suggest_lov` | lov-rule-suggestion | 1.0.0 |

## Usage

```python
from modelops_core.ai.prompt_registry import PromptRegistry

registry = PromptRegistry()
template = registry.get("file_to_model")
system = template.render_system_prompt()
user = template.render_user_prompt({"dataset_profile": ...})
metadata = template.to_metadata()
```

## Versioning Rules

- Patch version: wording tweaks, examples added
- Minor version: new fields in input/output schema
- Major version: workflow behavior change

## Telemetry

Every AI usage records `prompt_id` and `version` in:
- Audit events (`audit_events.jsonl`)
- PatchProposal metadata

# Martenweave AI-Ready Data Model Layer

Version: 0.2
Status: Aligned with v0.5.0 implementation
Scope: Why Martenweave creates an AI-ready model layer without becoming a generic AI chatbot

---

## Implementation Status

| Capability | Status | Notes |
|---|---|---|
| AI proposes / validators verify / humans approve | Implemented | Core principle enforced by CLI workflow: `propose-patch` → `proposal validate` → `proposal impact` → human review → `change-request approve` → `proposal apply` |
| Bounded context bundles | Implemented | `AIContextBundle` limits max primary objects (10), related objects (50), source text length, validation results (50), open issues (20) |
| Schema-known objects | Implemented | All canonical objects have registered types with known fields, reference fields, and relationship types in `schemas/registry.py` |
| Deterministic validation as guardrail | Implemented | Every proposal runs through `validate_patch_proposal()` using the same pipeline as human edits |
| Patch proposal workflow | Implemented | `propose-patch`, `proposal validate`, `proposal impact`, `proposal diff`, `proposal apply`, `proposal report`, `proposal review-bundle` |
| No direct write guardrail | Implemented | AI cannot modify canonical files directly; `apply` only accepts PatchProposal or ChangeRequest |
| Privacy scrubbing | Implemented | `AIContextBundle.scrub()` removes raw samples by default; `include_raw_samples=True` requires explicit opt-in |
| Provider output validation | Implemented | `ProviderOutputValidator` checks proposal_id, title, operations allow-list; no `delete_object` or destructive ops |
| NoProviderAdapter | Implemented | Deterministic scaffold adapter when no AI provider is configured |
| KimiAdapter | Implemented | OpenAI-compatible chat completions with JSON response format, structured output validation, retry-ready error handling |
| GoogleADKAdapter | Target state | Google ADK tools exist but no full adapter yet |
| OllamaAdapter | Target state | Not implemented |
| Confidence scoring | Partial | Low/medium/high levels in scaffold; numeric calibration is target state |
| Semantic search | Target state | Keyword + exact match only; ranked relevance is planned |
| Cross-proposal conflict detection | Target state | Manual review only; automated detection is planned |
| AMS handover generation | Target state | Manual or template-based; AI-generated from domain objects is planned |

---

## Core Principle

```text
AI proposes.
Validators verify.
Humans approve.
Canonical files change only after approval.
```

Martenweave is not an AI chatbot. It is a **controlled model change workflow** that uses AI as an assistant, not an authority. The AI-ready model layer means:

1. **Structured context:** AI receives bounded, validated, schema-known context bundles instead of raw repository dumps.
2. **Deterministic guardrails:** Every AI proposal is validated by the same deterministic rules that govern human edits.
3. **Traceable decisions:** AI-generated proposals are linked to `Evidence`, `Issue`, `Decision`, and `ChangeRequest` objects.
4. **Human approval gates:** No canonical file is mutated by AI without human review and approval.

---

## Why Canonical Model Truth Matters for AI

AI assistants are only as good as the context they receive. In SAP migration and MDM work, context is usually scattered across:

- Excel spreadsheets with inconsistent naming
- Email threads with partial information
- Ticket systems with fragmented history
- Confluence pages that are out of date
- Human experts who are unavailable

Martenweave solves this by creating a **single, structured, validated source of model truth** that AI can reason about safely:

| Scattered Context | Martenweave Canonical Truth |
|---|---|
| "Customer Group field in KNVV" | `ATTR-CUST-SALES-CUSTOMER-GROUP` with business definition, `FEP-S4-KNVV-KDGRP` with SAP context, `EntityContext` with grain |
| "Mapping spreadsheet row 47" | `MAP-CUST-GROUP-LEGACY-TO-KNVV` with source_endpoint, target_endpoint, and linked ValueMapping |
| "Email from Sarah about CH01" | `EV-EMAIL-20260426-CH01-A17` with source_date, related_objects, and linked Issue |
| "We decided to use 01 for A17" | `DEC-CH01-A17-CUSTOMER-GROUP` with decision_category, affected_objects, and evidence |

**Why this matters for AI:**

1. **Bounded context bundles:** Instead of dumping the entire repository to the AI, Martenweave retrieves only the relevant objects (exact ID match, SAP technical name match, attribute name match, open issues, recent decisions, owners). This reduces hallucination and cost.
2. **Schema-known objects:** Every object has a registered type with known fields, reference fields, and relationship types. AI outputs can be validated against this schema.
3. **Relationship graph:** AI can traverse `Attribute` → `FieldEndpoint` → `Mapping` → `ValueMapping` → `ValidationRule` to understand full context without guessing.
4. **Validation as feedback loop:** Invalid AI proposals are caught before they reach humans. The AI learns from validation errors (via human correction) to improve future proposals.

---

## Patch Proposal Workflow

The AI patch workflow is the primary interface between unstructured knowledge and structured model updates.

### Flow

```
User note / ticket / email / dataset profile
    → Evidence summary (optional)
    → Bounded context bundle retrieval
    → AI extraction of model-relevant facts
    → AI structured patch proposal
    → ProviderOutputValidator.validate()
    → validate_patch_proposal() (deterministic)
    → compute_proposal_risk() (approval gates)
    → PatchProposal file created
    → Human review (diff, impact, assumptions, required checks)
    → Human approve / reject / request revision
    → ChangeRequest created
    → Apply to canonical files
    → Post-apply validation
    → Index rebuild
    → Audit event
```

### Context Bundle Limits

To prevent hallucination and control cost, context bundles are bounded:

| Limit | Value | Purpose |
|---|---|---|
| Max primary objects | 10 | Focus AI on the most relevant objects |
| Max related objects | 50 | Include context without overwhelming |
| Max source text length | Configurable | Prevent token overflow |
| Max validation results | 50 | Show health of affected objects |
| Max open issues | 20 | Surface known problems |

### Context Retrieval Strategy

```
1. Exact ID match
2. SAP technical name match
3. Attribute name match
4. Dataset column match
5. Mapping / value mapping match
6. Open issue / decision match
7. Keyword search
8. Semantic search (if enabled)
```

**Example:** User note: "Customer Group 7 missing for CH01 / A17 Footlocker in RS4."

Retrieval searches for:
- `Customer Group` → `ATTR-CUST-SALES-CUSTOMER-GROUP`
- `CH01` → `EntityContext` or `Issue` with sales org
- `A17` → `ValueMapping` with source value
- `KNVV`, `KDGRP` → `FieldEndpoint`
- `sales area` → `EntityContext` with `customer_sales_area`
- `RS4` → `SystemEnvironment`
- `value mapping`, `configuration gap` → `Issue`, `Decision`

---

## Guardrails Against Hallucinated Model Changes

Martenweave implements multiple guardrails to prevent AI from inventing or silently applying incorrect model changes:

### 1. Schema Validation Guardrail

AI output must match the `AICandidateOutput` schema:

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
- `proposal_id` and `title` are present.
- Operations are in the allow-list.
- No `delete_object` or destructive ops.

### 2. Deterministic Validation Guardrail

After schema validation, the proposal runs through the same validator as human edits:

- `validate_patch_proposal()` checks object IDs, types, references, SAP context rules.
- Invalid proposals cannot be applied.
- Validation results are stored in the `PatchProposal` file.

### 3. Approval Gate Guardrail

- High-risk changes require explicit approver sign-off.
- Risk is computed by `compute_proposal_risk()` based on:
  - Number of affected objects
  - Presence of active mappings
  - Changes to value lists or validation rules
  - Impact depth
- Low-risk changes may use the lightweight path, but still require human approval.

### 4. No Direct Write Guardrail

- AI cannot directly modify canonical files.
- CLI `apply` only accepts `PatchProposal` or `ChangeRequest`.
- Every change must have a `ChangeRequest` with audit event.

### 5. Evidence Requirement Guardrail

- Every AI-proposed change must have `source_evidence` or user-provided source text.
- AI cannot invent SAP technical facts without evidence.
- AI cannot mark a validation as passed unless deterministic validation supports it.

### 6. Privacy Scrubbing Guardrail

- Raw dataset samples are excluded from AI context by default.
- `include_raw_samples=True` requires explicit opt-in.
- API keys are redacted from all logs and generated artifacts.

### 7. Confidence Scoring Guardrail

AI proposals include confidence levels:

| Confidence | Behavior |
|---|---|
| `low` | Requires explicit review; does not pre-fill active changes aggressively |
| `medium` | Standard review path |
| `high` | May use lightweight path if validation passes with zero errors |

Low-confidence patches should never bypass human review.

---

## Agent-Safe Automation Boundaries

Martenweave defines clear boundaries for what agents can and cannot do:

### Allowed Agent Actions

| Action | Description | Example |
|---|---|---|
| `create_issue` | Create an Issue from a gap or note | Dataset gap → `ISS-UNMAPPED-A17` |
| `create_decision_draft` | Draft a Decision from evidence | Workshop conclusion → `DEC-CH01-A17` |
| `create_change_request_draft` | Draft a ChangeRequest from proposal | Approved patch → `CR-001` draft |
| `update_attribute_draft` | Propose Attribute changes | Add description, update classification |
| `update_field_endpoint_draft` | Propose FieldEndpoint changes | Add enrichment, link to Attribute |
| `update_mapping_draft` | Propose Mapping changes | Add source-to-target link |
| `update_value_mapping_draft` | Propose ValueMapping changes | Add translation entry |
| `update_validation_rule_draft` | Propose ValidationRule changes | Add constraint |
| `create_evidence_summary` | Summarize source material | Email → `Evidence` object |
| `request_human_clarification` | Ask for more information | Ambiguous note → question to user |

### Forbidden Agent Actions

| Action | Why Forbidden |
|---|---|
| `approve_change` | Approval must be human |
| `delete_approved_object` | Destructive; requires human review |
| `modify_active_model_directly` | All changes must flow through PatchProposal |
| `mark_validation_passed` | Validation is deterministic, not AI-declared |
| `write_generated_index_as_source` | Generated files are not canonical |
| `send_raw_dataset_to_ai` | Privacy violation unless explicitly opted in |
| `send_data_to_external_system` | No direct system integration without human action |

---

## SAP/MDM Examples

### Example 1: AI Proposes Value Mapping Update

**Input note:**

> "Customer Group 7 missing for CH01 / A17 Footlocker in RS4."

**AI context bundle:**

```json
{
  "task": "propose_patch_from_note",
  "source": {
    "evidence_id": "EV-EMAIL-20260426-CH01-A17",
    "source_text_summary": "Customer Group handling gap for CH01 / A17"
  },
  "primary_objects": [
    "ATTR-CUST-SALES-CUSTOMER-GROUP",
    "FEP-S4-KNVV-KDGRP",
    "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP"
  ],
  "related_objects": [
    "VAL-CUST-GROUP-ALLOWED-VALUES",
    "VLIST-S4-CUST-GROUP",
    "CTX-CUSTOMER-SALES-AREA-S4"
  ],
  "open_issues": ["ISS-CH01-A17-CONFIG-GAP"],
  "recent_decisions": ["DEC-CH01-A17-CUSTOMER-GROUP"],
  "allowed_actions": [
    "update_value_mapping_draft",
    "create_issue",
    "request_human_clarification"
  ]
}
```

**AI output (after validation):**

```json
{
  "proposal_id": "PP-001",
  "title": "Update Customer Group handling for CH01 / A17",
  "confidence": "medium",
  "affected_objects": [
    "ATTR-CUST-SALES-CUSTOMER-GROUP",
    "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP"
  ],
  "proposed_changes": [
    {
      "action": "update_value_mapping_draft",
      "object_id": "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP",
      "change_summary": "Add mapping entry for source value A17 for CH01",
      "fields": {
        "mappings": [
          {
            "source_value": "A17",
            "target_value": null,
            "status": "proposed",
            "condition": "sales_org == CH01"
          }
        ]
      }
    }
  ],
  "questions": [
    "What is the approved target Customer Group value for A17 in CH01?"
  ],
  "required_human_checks": [
    "Confirm target S/4 customizing in RS4.",
    "Confirm whether this applies only to CH01."
  ],
  "assumptions": [
    "A17 refers to source customer group from the source note."
  ]
}
```

**Human review:**
- The steward confirms that target value should be `01`.
- The steward updates the proposal with `target_value: "01"`.
- The steward approves and creates `CR-001`.

### Example 2: AI Summarizes Impact

**Input:**

```bash
modelops impact VLIST-S4-CUST-GROUP --repo ./my-model
```

**Deterministic impact report:**

- Affected: `VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP`, `VAL-CUST-GROUP-ALLOWED-VALUES`, `DS-CUST-SALES-AREA-LOAD`
- Owners: `PERSON-SALES-MD-OWNER`, `PERSON-CUSTOMER-BP-STEWARD`
- Open issues: `ISS-CH01-A17-CONFIG-GAP`

**AI summary (for business stakeholders):**

> "Changing the S/4 Customer Group value list affects the legacy-to-S/4 value mapping, the validation rule that checks Customer Group correctness, and the sales area load dataset. The sales MD owner and BP steward must review. There is an open issue about CH01 / A17 that may be resolved by this change."

**Guardrail:** AI must not invent additional affected objects. If it believes something may be affected but is not in the deterministic graph, it must mark it as a hypothesis.

### Example 3: AI Generates AMS Handover Summary

**Input:** Domain `DOMAIN-CUSTOMER-BP` after migration cutover.

**AI generates:**

```markdown
# AMS Handover Summary: Business Partner / Customer Domain

## Approved Model Facts

- Customer Group (`ATTR-CUST-SALES-CUSTOMER-GROUP`) is mapped from legacy code to S/4 `KNVV-KDGRP`.
- Allowed values are documented in `VLIST-S4-CUST-GROUP`.
- Value mapping `VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP` translates legacy codes to S/4 codes.

## Open Issues

- `ISS-CH01-A17-CONFIG-GAP` — Customer Group A17 for CH01 requires special handling.

## Known Risks

- Value list may need updating when new sales organizations are added.
- Legacy code `A17` is conditionally mapped; verify during AMS support.

## Diagnostic Steps

1. Check `VAL-CUST-GROUP-ALLOWED-VALUES` if Customer Group validation fails.
2. Review `VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP` for unmapped source values.
3. Consult `PERSON-CUSTOMER-BP-STEWARD` for business context.

## Related Decisions

- `DEC-CH01-A17-CUSTOMER-GROUP` — Approved mapping for A17 → 01 in CH01.
```

**Guardrail:** AI clearly distinguishes approved facts, open issues, assumptions, and recommendations.

---

## Current State vs Target State

| Capability | Current State (v0.4) | Target State |
|---|---|---|
| AI provider adapters | `NoProviderAdapter` (deterministic scaffold) and `KimiAdapter` (OpenAI-compatible) implemented | `GoogleADKAdapter`, `OllamaAdapter` |
| Structured output validation | `ProviderOutputValidator` checks schema and allow-lists | Full JSON Schema enforcement with retry logic |
| Context bundle retrieval | Keyword + exact match | Semantic search + ranked relevance |
| Impact summarization | Deterministic BFS traversal | AI-summarized business language |
| AMS handover generation | Manual or template-based | AI-generated from domain objects |
| Validation checklist generation | Manual | AI-generated from changed objects |
| Proposal confidence scoring | Low/medium/high | Numeric confidence with calibration |
| Cross-proposal conflict detection | Manual | Automated conflict detection |

---

## Related Documents

- `docs/governance/DAMA_ALIGNMENT.md` — DAMA-DMBOK alignment overview
- `docs/governance/DATA_GOVERNANCE_OPERATING_MODEL.md` — Practical operating model for governance work
- `docs/governance/DATA_QUALITY_AND_METADATA_MODEL.md` — Data quality and metadata treatment
- `docs/ai-provider-architecture.md` — AI provider adapter architecture
- `docs/architecture/AI_PATCH_WORKFLOW.md` — AI patch proposal workflow
- `docs/architecture/PATCH_PROPOSAL_AND_APPROVAL_FLOW.md` — Patch proposal and approval flow
- `docs/ai/AGENT_SAFETY_RULES.md` — Agent safety rules
- `docs/ai/VALIDATION_LADDER.md` — Validation ladder for agents

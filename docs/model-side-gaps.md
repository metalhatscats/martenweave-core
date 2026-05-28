# Model-Side Gap Detection

Dataset-side gaps compare a CSV or XLSX against your model's `FieldEndpoint` objects. Model-side gaps look inward at the model itself to find missing links and ownership holes.

---

## How it works

```bash
modelops gaps --check-model --repo <repo> [--json]
```

This queries the SQLite index (run `build-index` first) and reports:

1. **Attributes with no linked FieldEndpoint** — semantic objects that have no physical representation.
2. **Objects missing an owner** — `Attribute` and `FieldEndpoint` objects without `business_owner` or `technical_owner`.

---

## Gap Codes

| Code | Severity | What it means |
|---|---|---|
| `MODEL_ATTRIBUTE_MISSING_SOURCE` | critical | An `Attribute` has no `FieldEndpoint` linked via `represents_attribute`. The attribute exists in the model but has no mapped source column or field. |
| `MISSING_OWNER` | warning | An `Attribute` or `FieldEndpoint` is missing both `business_owner` and `technical_owner`. |

---

## Copy-paste example

Using the `customer_bp_model` example:

```bash
# Build the index first
.venv/bin/modelops build-index --repo examples/customer_bp_model

# Check model-side gaps
.venv/bin/modelops gaps --check-model --repo examples/customer_bp_model
```

Sample output:

```
MODEL_ATTRIBUTE_MISSING_SOURCE  critical  Attribute 'ATTR-CUST-UNKNOWN' has no linked FieldEndpoint.
MISSING_OWNER                   warning   Attribute 'ATTR-CUST-SALES-REGION' is missing an owner.
```

---

## How to fix

### `MODEL_ATTRIBUTE_MISSING_SOURCE`

Create a `FieldEndpoint` that represents the attribute, or link an existing one:

```markdown
---
id: FEP-MY-TABLE-MYFIELD
type: FieldEndpoint
status: draft
name: My Field
endpoint_type: sap_table_field
entity_context: ENTITY-MY-CONTEXT
---
```

Then ensure the `FieldEndpoint` has a `represents_attribute` relationship pointing to the `Attribute`.

### `MISSING_OWNER`

Add `business_owner` or `technical_owner` to the object's frontmatter:

```yaml
business_owner: team-data-governance
technical_owner: alice.smith@example.com
```

---

## Important note on datasets

Raw datasets in `data/samples/` are **inputs only**. They are never treated as canonical model truth. Model-side gap detection checks the canonical objects in the index, not the raw data files.

---

## See also

- [User Guide](user-guide.md) — Dataset → Model workflow
- [Gaps CLI Contract](developer/cli-contracts/dataset-gaps.md) — JSON output fields

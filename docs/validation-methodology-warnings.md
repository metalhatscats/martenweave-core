# Validation Methodology Warnings

> Reference for warning-only validation codes. Warnings do not block indexing or application, but they signal opportunities to improve model quality.

## Warning codes

### `ATTRIBUTE_MISSING_CONTEXT`

An `Attribute` does not declare which `EntityContext` it belongs to.

**Fix:** Add `entity_context` to the Attribute frontmatter.

```yaml
---
id: ATTR-PRODUCT-NAME
type: Attribute
status: active
name: Product Name
domain: DOMAIN-PRODUCT
entity_context: CTX-PRODUCT-MASTER
---
```

### `ATTRIBUTE_USAGE_MISSING_TYPE`

An `AttributeUsage` does not declare its usage type.

**Fix:** Add `usage_type` to the AttributeUsage frontmatter.

```yaml
---
id: USE-PRODUCT-NAME-S4
type: AttributeUsage
status: active
attribute: ATTR-PRODUCT-NAME
entity_context: CTX-PRODUCT-S4
field_endpoint: FEP-S4-MAKT-MAKTX
usage_type: display
---
```

Valid usage types include `display`, `key`, `filter`, `sort`, `search`.

### `DISPLAY_NAME_MISSING`

An object has neither `name` nor `title` for display purposes.

**Fix:** Add `name` (or `title`) to the frontmatter.

```yaml
---
id: USE-PRODUCT-NAME-S4
type: AttributeUsage
status: active
name: Product Name (S4)
---
```

### `FIELD_ENDPOINT_MISSING_ENRICHMENT`

A `FieldEndpoint` lacks enrichment metadata such as description or sample values.

**Fix:** Add an `enrichment` block.

```yaml
---
id: FEP-S4-MAKT-MAKTX
type: FieldEndpoint
status: active
name: MAKTX
endpoint_type: sap_table_field
table: MAKT
enrichment:
  description: Material description text
  sample_values:
    - "Steel Bolt M8"
    - "Copper Wire 2mm"
---
```

### `LOV_EMPTY`

A `ValueList` has no values or an empty values list.

**Fix:** Populate `values` with structured entries.

```yaml
---
id: VLIST-PRODUCT-CATEGORY
type: ValueList
status: active
name: Product Categories
values:
  - code: RAW
    label: Raw Material
  - code: FIN
    label: Finished Good
---
```

### `OWNERSHIP_MISSING`

An active or draft object has no ownership or stewardship field.

**Fix:** Add one of the recognized ownership fields.

```yaml
---
id: MAP-PRODUCT-LEGACY-TO-S4
type: Mapping
status: active
name: Product Legacy to S4
business_owner: PERSON-PRODUCT-OWNER
data_steward: PERSON-DATA-STEWARD
---
```

Recognized fields: `business_owner`, `technical_owner`, `data_steward`, `accountable_team`, `approver`.

### `TIMESTAMP_MISSING`

An object is missing `created_at`.

**Fix:** Add an ISO 8601 timestamp.

```yaml
---
id: ATTR-PRODUCT-NAME
type: Attribute
status: active
created_at: 2024-01-15T10:30:00+00:00
---
```

### `VALUE_MAPPING_EMPTY`

A `ValueMapping` references a list but has no explicit `mappings`.

**Fix:** Add a `mappings` array.

```yaml
---
id: VMAP-PRODUCT-CATEGORY-TO-S4
type: ValueMapping
status: active
name: Product Category to S4
value_list: VLIST-PRODUCT-CATEGORY
field_endpoint: FEP-S4-MARA-MTART
mappings:
  - from: RAW
    to: ROH
  - from: FIN
    to: FERT
---
```

### `FLAT_MODEL_STRUCTURE`

The repository has very few objects, suggesting an under-developed model.

**Fix:** Expand the model with additional domains, entities, attributes, and relationships.

## Info codes

### `SCHEMA_VERSION_MISSING`

The object frontmatter does not declare a `schema_version`.

**Fix:** Add `schema_version`.

```yaml
---
id: ATTR-PRODUCT-NAME
type: Attribute
status: active
schema_version: "1.0"
---
```

## Suppressing methodology warnings

For simple models or early-stage repositories, methodology warnings can be noisy. Use `--suppress-methodology-warnings` to hide them without affecting structural errors or ownership warnings.

```bash
martenweave validate --repo ./my-model --suppress-methodology-warnings
```

Suppressed codes:
- `FLAT_MODEL_STRUCTURE`
- `FIELD_ENDPOINT_MISSING_ENRICHMENT`
- `ATTRIBUTE_MISSING_CONTEXT`
- `ATTRIBUTE_USAGE_MISSING_TYPE`

Error-level results and other warning codes (e.g., `OWNERSHIP_MISSING`, `REFERENCE_BROKEN`) are **not** affected.

## Strict mode

Use `martenweave validate --strict` to treat warnings as failures (exit code 2). This is useful for CI pipelines that want to enforce methodology completeness.

```bash
martenweave validate --repo ./my-model --strict
```

## See also

- [User Guide](user-guide.md) — day-to-day CLI usage
- [docs/developer/ADDING_VALIDATION_RULES.md](developer/ADDING_VALIDATION_RULES.md) — how to add new rules
- [docs/ai/VALIDATION_LADDER.md](ai/VALIDATION_LADDER.md) — validation commands for agents

# Generic Product Model Example

This example demonstrates Martenweave for **generic large objects**
with value lists and value mappings (e.g., product colors and sizes).

## Model Structure

| Object ID | Type | Description |
|---|---|---|
| `DOMAIN-PRODUCT` | MasterDataDomain | Product domain |
| `VLIST-PRODUCT-COLOR` | ValueList | Allowed product colors |
| `VLIST-PRODUCT-COLOR-LEGACY` | ValueList | Legacy color codes |
| `VLIST-PRODUCT-SIZE` | ValueList | Allowed product sizes |
| `VMAP-COLOR-TO-LEGACY` | ValueMapping | Color to legacy code mapping |
| `PERSON-PRODUCT-OWNER` | Person | Product owner |

## Quickstart

```bash
# Validate
modelops validate --repo examples/generic_product_model

# Build index
modelops build-index --repo examples/generic_product_model --jsonl

# Query value lists
modelops query --repo examples/generic_product_model --type ValueList

# Trace a value mapping
modelops trace VMAP-COLOR-TO-LEGACY --repo examples/generic_product_model

# Export
modelops export-model --repo examples/generic_product_model --format xlsx
```

## Requirements

- Python 3.11+
- Martenweave installed
- No AI provider key required

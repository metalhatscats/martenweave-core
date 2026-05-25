# Simple Product Model Example

This example demonstrates Martenweave in **simple table mode**:
a single domain with a business entity, attributes, field endpoints,
and a value list.

## Model Structure

| Object ID | Type | Description |
|---|---|---|
| `DOMAIN-PRODUCT` | MasterDataDomain | Product master data domain |
| `ENTITY-PRODUCT` | BusinessEntity | Product entity |
| `ATTR-PRODUCT-*` | Attribute | Product attributes (ID, Name, Category, Unit Price, Active) |
| `FEP-PRODUCT-*` | FieldEndpoint | Field endpoints for each attribute |
| `VLIST-PRODUCT-CATEGORY` | ValueList | Allowed product categories |
| `DS-PRODUCT-CSV` | Dataset | Reference to the sample CSV dataset |

## Quickstart

Run these commands from the repository root:

```bash
# 1. Validate canonical model
modelops validate --repo examples/simple_product_model

# 2. Build search index
modelops build-index --repo examples/simple_product_model --jsonl

# 3. Profile the sample dataset
modelops profile-dataset \
    examples/simple_product_model/data/samples/product_sample.csv \
    --repo examples/simple_product_model

# 4. Search indexed objects
modelops search "product" --repo examples/simple_product_model

# 5. Query by object type
modelops query --repo examples/simple_product_model --type Attribute

# 6. Trace lineage
modelops trace ATTR-PRODUCT-NAME --repo examples/simple_product_model

# 7. Analyze model completeness
modelops analyze --repo examples/simple_product_model

# 8. Export model
modelops export-model --repo examples/simple_product_model --format csv
modelops export-model --repo examples/simple_product_model --format xlsx
```

## Requirements

- Python 3.11+
- Martenweave installed (`.venv/bin/modelops` or `pip install -e '.[dev]'`)
- No AI provider key required

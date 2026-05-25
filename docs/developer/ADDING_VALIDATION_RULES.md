# Adding Validation Rules

## Files

- Generic rules: `src/modelops_core/validation/pipeline.py`
- Domain-specific rules: `src/modelops_core/domain_packs/`
- Result types: `src/modelops_core/validation/result.py`

## Steps

1. Decide whether the rule is generic core or domain-pack-specific.
2. Add deterministic logic with stable error codes.
3. Include `object_id`, `source_file`, `field_path`, and `suggested_fix` where possible.
4. Add tests for pass and fail paths.
5. Update docs if the validation contract changes.

## Validation

```bash
.venv/bin/python -m pytest tests/test_*validation*.py -v
.venv/bin/modelops validate --repo examples/customer_bp_model
.venv/bin/modelops validate --repo examples/simple_product_model
.venv/bin/python -m ruff check .
```

Do not use AI or fuzzy matching as validation authority.

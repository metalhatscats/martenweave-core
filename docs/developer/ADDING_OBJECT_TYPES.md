# Adding Object Types

## Files

- `src/modelops_core/schemas/common.py`
- `src/modelops_core/schemas/registry.py`
- tests in `tests/test_schema_validation.py` and `tests/test_reference_validation.py`

## Steps

1. Add the enum value to `ObjectType`.
2. Add an `ObjectTypeEntry` in the registry.
3. Define reference fields with expected target types.
4. Add search fields if useful.
5. Add examples only if they clarify core behavior.
6. Update architecture docs if semantics change.
7. Add tests for validation and reference behavior.

## Validation

```bash
.venv/bin/python -m pytest tests/test_schema_validation.py tests/test_reference_validation.py -v
.venv/bin/modelops validate --repo examples/simple_product_model
.venv/bin/python -m ruff check .
```

Do not add domain-specific required fields to core object types.

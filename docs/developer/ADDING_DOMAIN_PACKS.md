# Adding Domain Packs

## Files

- `src/modelops_core/domain_packs/base.py`
- `src/modelops_core/domain_packs/__init__.py`
- new pack module under `src/modelops_core/domain_packs/`
- `docs/architecture/DOMAIN_PACK_BOUNDARY.md`
- tests in `tests/test_domain_packs.py`

## Steps

1. Confirm the behavior is domain-specific, not generic core.
2. Implement a `DomainPack` subclass.
3. Register it by name.
4. Enable it only through `modelops.config.yaml`.
5. Add tests showing generic validation is unaffected when the pack is disabled.
6. Add or update optional examples/templates.

## Validation

```bash
.venv/bin/python -m pytest tests/test_domain_packs.py -v
.venv/bin/martenweave validate --repo examples/simple_product_model
.venv/bin/martenweave validate --repo examples/customer_bp_model
.venv/bin/python -m ruff check .
```

Domain packs cannot define core architecture or make one domain mandatory.

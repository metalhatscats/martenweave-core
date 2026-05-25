# Skill: Domain Pack Handling — Martenweave

## When to use
Use when changing SAP or any other domain-specific examples, templates, validation rules, or docs.

## Inputs
- Domain pack name.
- Affected examples/templates/rules.

## Read first
1. `docs/architecture/DOMAIN_PACK_BOUNDARY.md`
2. `docs/product/DOMAIN_PACK_STRATEGY.md`
3. `src/modelops_core/domain_packs/`
4. `tests/test_domain_packs.py`

## Do not do
- Do not make domain-pack rules run for generic repositories unless enabled.
- Do not require domain-specific fields in core object schemas.
- Do not let SAP examples define MVP boundaries.
- Do not add direct writes to domain systems.

## Procedure
1. Confirm the change belongs in a domain pack, not core.
2. Keep validation optional through `enabled_domain_packs`.
3. Update examples/templates only as optional starter material.
4. Add tests showing generic models remain valid without the pack.
5. Document the pack boundary and validation behavior.

## Validation
```bash
.venv/bin/python -m pytest tests/test_domain_packs.py tests/test_sap_context_validation.py -v
.venv/bin/modelops validate --repo examples/simple_product_model
.venv/bin/modelops validate --repo examples/customer_bp_model
.venv/bin/python -m ruff check .
```

## Output format
Return:
- domain pack affected;
- generic core impact;
- validation commands;
- example/template changes;
- remaining risks.

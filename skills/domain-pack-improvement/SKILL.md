# Skill: Domain-Pack Improvement — Martenweave

## When to use
Use when extending SAP/MDM domain quality: adding an SAP context rule, tightening domain-pack validation, or improving domain examples and templates.

## Inputs
- Domain pack name (currently `sap`).
- The rule, example, or template change requested, with its issue.

## Read first
1. `docs/architecture/DOMAIN_PACK_BOUNDARY.md` — packs are optional; Core stays domain-neutral.
2. `src/modelops_core/domain_packs/sap.py` — `_SAP_CONTEXT_RULES` and `SAPDomainPack.validate`.
3. `tests/test_sap_context_validation.py` and `tests/test_domain_packs.py` — fixture style, code/severity assertions.
4. `docs/developer/TESTING_STRATEGY.md` — never mock core validation; exercise the real code.
5. `skills/domain-pack-handling/SKILL.md` — base handling rules for domain work.

## Do not do
- Do not add required domain fields to generic core schemas (`src/modelops_core/schemas/`).
- Do not make generic validation depend on a pack; rules run only via `enabled_domain_packs`.
- Do not edit `model/` files in examples to "improve" them — canonical data changes only via `PatchProposal` → approval → `ChangeRequest` (P6); fixture changes are L3.
- Do not add SAP write-back, extraction, or any direct external writes (P5).
- Do not weaken an existing rule, test, or fixture to make a check pass (P1).

## Procedure
1. Confirm the change belongs in the domain pack, not Core. If it defines generic behavior, it goes to `src/modelops_core/validation/` instead.
2. New SAP context rule: add one entry to `_SAP_CONTEXT_RULES` in `src/modelops_core/domain_packs/sap.py`:
   `SAPContextRule("<TABLE>", "<required_context_category>", "SAP_CONTEXT_<TABLE>_REQUIRES_<CATEGORY>")`.
3. Write tests first (TDD) in `tests/test_sap_context_validation.py`:
   - positive: FieldEndpoint plus matching EntityContext passes (`summary.is_valid`);
   - negative: wrong or missing `context_category` fails — assert the exact error `code` and `severity` (`ERROR`) on `summary.results`;
   - use `ParsedObject` fixtures with real `validate_objects(..., enabled_domain_packs=["sap"])`; no mocks.
4. Prove generic models stay valid with the pack disabled:
   ```bash
   .venv/bin/modelops validate --repo examples/simple_product_model
   .venv/bin/modelops validate --repo examples/generic_product_model
   ```
5. Example/template improvements are optional starter material only. Keep IDs matching `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$` and keep every `sap_table` ↔ `context_category` pair consistent with the rules.
6. Realism checks on SAP examples: every `sap_table_field` endpoint resolves its `entity_context`, and the resolved category matches the table's required category.
7. Run the validation block below; if schemas or validation changed, also validate all 8 bundled examples (G4).

## Validation
```bash
.venv/bin/python -m pytest tests/test_sap_context_validation.py tests/test_domain_packs.py -v
.venv/bin/modelops validate --repo examples/customer_bp_model
.venv/bin/modelops validate --repo examples/sap_bp_customer_vendor_reference
.venv/bin/ruff check .
```
Full suite (G5) before commit; L3 fixture changes stop for maintainer approval.

## Output format
Return:
- rules added (table → required category → error code);
- tests added (positive/negative, file);
- proof generic examples stay valid with the pack disabled;
- example/template changes (or "none — canonical data untouched");
- gate results with counts.

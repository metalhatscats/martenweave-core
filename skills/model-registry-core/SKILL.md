# Skill: Model Registry Core — Martenweave

## When to use
You are adding, modifying, or referencing canonical objects (domains, attributes, field endpoints, mappings, etc.).

## Inputs
- Object type name (must exist in `ObjectType` enum)
- Desired object ID (must match `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`)
- Domain or parent references

## Read first
1. `src/modelops_core/schemas/common.py` — `ObjectType` enum and `BaseObject`.
2. `src/modelops_core/schemas/registry.py` — `ObjectTypeEntry`, reference fields, and SAP context rules.
3. `examples/customer_bp_model/model/` — concrete examples of each object type.

## Do not do
- Do not invent new `ObjectType` values without updating both `common.py` and `registry.py`.
- Do not reuse IDs; every ID must be globally unique.
- Do not create circular references (e.g., Attribute A references Attribute B which references Attribute A).
- Do not add UI, SaaS, or workflow logic here; this is schema and registry work only.

## Procedure
1. Choose or verify the object type in `ObjectType`.
2. Choose a stable, unique ID matching the regex.
3. Create or edit the canonical file under `model/`:
   ```markdown
   ---
   id: YOUR-ID-HERE
   type: Attribute
   status: draft
   name: Your Name
   domain: DOMAIN-CUSTOMER-BP
   ---

   # Your Name

   Description goes here.
   ```
4. Add any reference fields (e.g., `domain`, `attribute`, `entity_context`) using valid target IDs.
5. Run validation: `modelops validate --repo <path>`
6. Rebuild index: `modelops build-index --repo <path> --jsonl`
7. Run tests: `pytest tests/test_schema_validation.py tests/test_reference_validation.py`

## Validation
- `modelops validate` reports zero ERRORs for the new/modified object.
- Reference fields point to existing objects of the expected type.
- `pytest` passes for schema and reference validation suites.

## Output format
Return:
- Object ID and type
- File path created or modified
- References added (source ID → target ID)
- Validation result (pass/fail with counts)

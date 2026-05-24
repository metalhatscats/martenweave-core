# Skill: Validation — Martenweave

## When to use
You need to verify canonical files, schemas, references, or SAP context rules before or after making changes.

## Inputs
- Path to a model repository (default: current directory or `examples/customer_bp_model`)
- Optional: `--allow-invalid` flag (only use if explicitly instructed)

## Read first
1. `src/modelops_core/validation/pipeline.py` — Layer 1–3 validation logic.
2. `src/modelops_core/validation/result.py` — severity levels and result structures.
3. `src/modelops_core/schemas/registry.py` — `_SAP_CONTEXT_RULES` and reference field definitions.

## Do not do
- Do not ignore `ERROR` level results; they block indexing by default.
- Do not bypass validation with `--allow-invalid` unless the user explicitly requests it.
- Do not modify `generated/` to "fix" validation errors; fix the canonical source files instead.

## Procedure
1. Run validation on the target repo:
   ```bash
   modelops validate --repo <path>
   ```
2. Read the output table. Severity levels:
   - `ERROR` — must be fixed before indexing
   - `WARNING` — should be reviewed
   - `INFO` — informational only
3. If errors exist, trace the error code back to `validation/pipeline.py` to understand the rule.
4. Fix canonical source files in `<repo>/model/` and re-run until clean.
5. Use the documented repo validation command. If a machine-readable output option is missing, report validation gap.

## Validation
- `modelops validate` returns exit code 0 with no `ERROR` entries.
- All `WARNING` entries are either resolved or explicitly acknowledged in commit/PR notes.

## Output format
Return:
- Validation command used
- Count of ERROR / WARNING / INFO
- List of any remaining issues with file paths and suggested fixes

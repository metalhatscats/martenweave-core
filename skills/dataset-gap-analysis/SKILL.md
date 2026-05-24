# Skill: Dataset Gap Analysis — Martenweave

## When to use
You need to profile a CSV dataset and compare its columns against the canonical model to find missing, extra, or mismatched fields.

## Inputs
- Path to a CSV file
- Path to the model repository (to resolve canonical field endpoints)

## Read first
1. `src/modelops_core/imports/dataset_profiler.py` — streaming profiler and column statistics.
2. `src/modelops_core/gaps/gap_detection.py` — `detect_dataset_gaps`, `ColumnMatch`, `ColumnGap`.
3. `examples/customer_bp_model/data/samples/` — example datasets to test against.

## Do not do
- Do not load entire multi-GB files into memory; the profiler streams with bounded memory.
- Do not treat gap results as canonical truth; they are diagnostic inputs for human review.
- Do not write profiling outputs into `model/`; they belong in `generated/` or a separate report directory.

## Procedure
1. Ensure the dataset is accessible at a known path.
2. Import and run the profiler programmatically (there is no dedicated CLI subcommand for gap analysis yet):
   ```python
   from modelops_core.imports.dataset_profiler import profile_csv
   from modelops_core.gaps.gap_detection import detect_dataset_gaps

   columns = profile_csv("path/to/dataset.csv")
   gaps = detect_dataset_gaps(columns, repo_path="examples/customer_bp_model")
   ```
3. Review `ColumnMatch` and `ColumnGap` results.
4. If gaps indicate model deficiencies, open an `Issue` canonical object or create a `PatchProposal` instead of editing model files directly.

## Validation
- Profiler completes without memory errors on the target file.
- Gap results include: matched columns, unmatched columns, and suggested canonical mappings.
- Any model changes triggered by gaps go through the PatchProposal workflow (see `patch-proposal/SKILL.md`).

## Output format
Return:
- Dataset path and row/column count
- Matched columns (list)
- Gaps (list with severity: missing_in_model, missing_in_dataset, type_mismatch)
- Recommended next step (patch proposal, issue creation, or no action)

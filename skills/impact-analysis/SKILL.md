# Skill: Impact Analysis — Martenweave

## When to use
You need to understand what other objects depend on a given canonical object before deleting, renaming, or changing it.

## Inputs
- Object ID (e.g., `FEP-S4-KNVV-KDGRP`)
- Path to the model repository

## Read first
1. `src/modelops_core/impact/impact_service.py` — `generate_impact_report` (bounded BFS).
2. `src/modelops_core/impact/impact_report.py` — `ImpactReport` and `AffectedObject` structures.
3. `src/modelops_core/lineage/lineage_service.py` — how lineage edges are traversed.

## Do not do
- Do not perform impact analysis by manually grepping `model/`; use the BFS service to traverse references and lineage edges correctly.
- Do not delete or modify an object without reviewing its impact report.
- Do not treat impact results as approvals; they are information for human decision-making.

## Procedure
1. Run the CLI impact command:
   ```bash
   modelops impact <OBJECT_ID> --repo <path>
   ```
2. Review the output table:
   - Direct references (immediate children/parents)
   - Transitive dependencies (bounded BFS up to configured depth)
3. If the impact is large, flag the issue/PR for additional human review.
4. If you must proceed, create a `ChangeRequest` or `PatchProposal` that documents the affected objects.

## Validation
- `modelops impact` returns a report with zero runtime errors.
- The report lists all objects reachable via reference fields and lineage edges.
- If the object does not exist, the command returns a clear error instead of an empty report.

## Output format
Return:
- Target object ID
- Impact depth and total affected object count
- List of affected objects (ID, type, relationship direction)
- Risk flag (low / medium / high) based on count of affected objects

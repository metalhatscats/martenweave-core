# Vertical Slice Plan

## Slice Goal

Prove the complete local loop for a generic model repository:

```text
init -> canonical files -> validate -> build index -> query/search/trace/impact
-> profile dataset -> infer proposal -> review -> approve/apply -> export
```

## Minimal Demo Path

1. Use `examples/simple_product_model` for generic simple table mode.
2. Use `examples/customer_bp_model` as optional SAP domain-pack demo.
3. Run validation and index build.
4. Search for an attribute or endpoint.
5. Trace or impact an object.
6. Profile a fixture dataset.
7. Generate or inspect a `PatchProposal`.
8. Dry-run apply through proposal workflow.
9. Export model data.

## Acceptance

The slice is accepted when it runs locally without provider keys, external systems, UI, or cloud services.

# Workspace and Multi-Model Project Structure

## Concepts

| Concept | Scope |
|---|---|
| Workspace | Directory containing one or more model repositories |
| Project | A business initiative with related models |
| ModelRepository | Single canonical model with `model/` and `generated/` |
| Domain | Business area within a model |
| Workstream | A migration or implementation track |

## Layout

```
workspace/
  customer-migration/
    modelops.config.yaml
    model/
    generated/
  product-catalog/
    modelops.config.yaml
    model/
    generated/
```

## Cross-Model References

- References between models use full paths or workspace-relative IDs
- Not required for v0.1; documented for future use

## v0.1 Compatibility

Single-repo workflow is unchanged. Workspace is an optional organizational layer.

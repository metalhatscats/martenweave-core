# Environment and Release Scope

Track which model objects are active in which environments and release waves.

## Concepts

| Concept | Description |
|---|---|
| `Environment` | dev, test, qa, prod |
| `Release` | Named release (e.g., "2026-Q2") |
| `Wave` | Rollout wave within a release |
| `Market` | Geographic or business unit scope |
| `RolloutScope` | Link between object and environment/release |
| `ImplementationStatus` | Current state in a given environment |

## Status Values

- `planned` → `in_design` → `in_build` → `validated` → `deployed` → `deprecated` → `retired`

## Usage

Objects declare scope via metadata:

```yaml
---
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: active
environments:
  - dev
  - test
  - prod
release: REL-2026-Q2
wave: wave-1
markets:
  - global
---
```

## Analysis

- Release readiness: count of objects by status per release
- Environment drift: objects present in prod but missing in dev
- Market coverage: which markets have which objects deployed

## Future Commands

```bash
modelops release readiness --release REL-2026-Q2
modelops release drift --from dev --to prod
```

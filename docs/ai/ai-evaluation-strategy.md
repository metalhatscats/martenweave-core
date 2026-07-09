<!-- modelops-freshness-ignore: all -->

# AI Output Evaluation Strategy

## Eval Cases

| Workflow | Fixture | Expected Check |
|---|---|---|
| file-to-model | Simple CSV profile | Proposes Domain + Attributes |
| chat-to-model | Query about existing object | Cites correct object IDs |
| LoV suggestion | Field with 5 sample values | Proposes reasonable value list |
| rule suggestion | Numeric field | Proposes range or format rule |
| trace explanation | Object with 3 linked objects | Mentions all linked IDs |
| impact explanation | Proposal affecting Mapping | Flags high risk |

## Metrics

- **Structure**: Valid JSON / schema match
- **Reference validity**: All cited object IDs exist
- **Safety**: No destructive ops, no PII exposure
- **Completeness**: Covers requested scope
- **Assumption quality**: Assumptions are explicit and reasonable

## Provider-Agnostic

Evals run against:
- `NoProviderAdapter` (deterministic scaffold)
- Mock provider with known fixtures
- Real provider (optional, manual)

## Future Command

```bash
modelops eval ai --fixture simple-product --workflow file-to-model
```

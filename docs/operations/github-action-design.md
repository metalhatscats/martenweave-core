# GitHub Action Design for Martenweave

A future GitHub Action that validates Martenweave model repositories in CI and posts model health feedback on pull requests.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `repo-path` | no | `.` | Path to the model repository |
| `strict` | no | `false` | Treat warnings as errors |
| `score-threshold` | no | `70` | Minimum health score to pass |
| `changed-files-only` | no | `false` | Validate only objects related to changed files |
| `upload-artifacts` | no | `true` | Upload generated index and reports as artifacts |
| `generate-scorecard` | no | `true` | Generate and compare scorecard against baseline |

## Behavior

1. Install `modelops_core` from PyPI or a pinned commit.
2. Run `martenweave validate --repo <path>`.
3. Run `martenweave build-index --repo <path> --jsonl`.
4. Run `martenweave analyze --repo <path> --json`.
5. Optionally run `martenweave health --repo <path> --json` and compare to baseline.
6. Post a PR comment with:
   - Validation summary (errors, warnings)
   - Scorecard delta (if baseline exists)
   - High-risk changes (Mappings, ValidationRules, ValueLists, ValueMappings)
   - Affected owners

## PR Comment Format

```markdown
## Martenweave Model Check

| Metric | Value |
|---|---|
| Objects | 142 |
| Errors | 0 |
| Warnings | 3 |
| Health Score | 87 / 100 |

### Changed Objects
| ID | Type | Risk |
|---|---|---|
| MAP-CUST-001 | Mapping | ⚠️ high |

### Owners to Notify
- @data-steward-a
```

## Security

- No AI provider keys required by default.
- Generated artifacts (`generated/`) are uploaded as action artifacts, not committed.
- Dataset files in `data/` are never processed unless explicitly enabled.

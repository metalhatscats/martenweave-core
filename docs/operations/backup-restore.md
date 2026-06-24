# Backup and Restore

## What to Back Up

| Item | Why |
|---|---|
| `model/` canonical files | Source of truth |
| `modelops.config.yaml` | Repo configuration |
| `docs/` | Design decisions and governance |
| `patch-proposals/` (accepted) | Approved change history |
| `audit_events.jsonl` | Compliance log |

## What Can Be Regenerated

| Item | Regenerate Command |
|---|---|
| `generated/modelops.db` | `martenweave build-index` |
| `generated/*.jsonl` | `martenweave build-index --jsonl` |
| Exports and workbooks | `martenweave export` |
| Static docs | `modelops generate-docs` |

## Restore Process

1. Restore canonical files and config
2. Run `martenweave validate`
3. Run `martenweave build-index`
4. Run `martenweave health` to verify scorecard
5. Check audit log continuity

## Future Commands

```bash
modelops backup create ./backup-2026-05-24.tar.gz
modelops backup restore --dry-run ./backup-2026-05-24.tar.gz
```

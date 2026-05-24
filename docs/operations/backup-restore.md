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
| `generated/modelops.db` | `modelops build-index` |
| `generated/*.jsonl` | `modelops build-index --jsonl` |
| Exports and workbooks | `modelops export` |
| Static docs | `modelops generate-docs` |

## Restore Process

1. Restore canonical files and config
2. Run `modelops validate`
3. Run `modelops build-index`
4. Run `modelops health` to verify scorecard
5. Check audit log continuity

## Future Commands

```bash
modelops backup create ./backup-2026-05-24.tar.gz
modelops backup restore --dry-run ./backup-2026-05-24.tar.gz
```

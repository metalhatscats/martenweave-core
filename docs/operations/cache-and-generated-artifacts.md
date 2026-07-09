<!-- modelops-freshness-ignore: all -->

# Cache Lifecycle and Generated Artifact Cleanup

## Categories

| Category | Examples | Retention |
|---|---|---|
| Disposable index | `modelops.db`, `search_documents.jsonl` | Rebuild on demand |
| Profiles | dataset column stats | Keep recent, rebuild on re-import |
| Exports | workbooks, scorecards | Keep until next export |
| Graph exports | lineage JSON, visualizations | Rebuild from index |
| Telemetry | AI usage logs | 30 days or rotate |
| Audit logs | `audit_events.jsonl` | Keep long-term, archive monthly |
| Temp files | import staging, preview files | Delete after session |

## Safety Rules

- Cleanup **never** deletes `model/`, `modelops.config.yaml`, or `README.md`
- Canonical files are the only source of truth
- `--dry-run` previews what would be deleted
- `--confirm` required for actual deletion

## Future Commands

```bash
modelops cleanup --dry-run              # preview
modelops cleanup --generated            # delete disposable artifacts
modelops cleanup --profiles --keep 10   # keep 10 most recent profiles
modelops cleanup --telemetry --days 30  # rotate telemetry
```

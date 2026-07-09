<!-- modelops-freshness-ignore: all -->

# Diagnostics and Support Bundle Export

## Included

- Package version, Python version, OS
- `modelops.config.yaml` summary (redacted secrets)
- Index manifest (`generated/modelops.db` metadata)
- Validation summary (counts, not full error text)
- Scorecard summary
- Recent audit events (last 50)
- Recent errors (last 20)
- Generated artifact sizes

## Excluded by Default

- Raw datasets (`data/`)
- Secrets and credentials
- Full canonical file contents
- Proposals in `pending_review` status

## Future Command

```bash
modelops diagnostics export --output ./support-bundle.zip
modelops diagnostics export --dry-run
```

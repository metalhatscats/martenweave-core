# Notification Delivery Adapters

Delivery adapters send `NotificationEvent` records to external channels. They are optional and built on top of core events.

## Delivery Targets

| Target | Use Case |
|---|---|
| Email | Owner/steward alerts |
| Slack | Team channel summaries |
| Microsoft Teams | Enterprise team notifications |
| GitHub Issue Comments | PR review thread updates |
| Webhook | Custom integrations |

## Event Lifecycle

```
Generated (by validate, apply, proposal)
    |
    v
Pending → Sent | Failed | Skipped | Muted
```

## Redaction

- Raw dataset values never included
- Object IDs and names only
- Validation counts, not full error messages
- Link to local report, not inline data

## Dry Run

```bash
modelops notifications preview --since 24h
```

Shows what would be sent without sending.

## Safe Defaults

- No external delivery without explicit configuration
- Missing adapter config fails safely (event stays pending)
- All delivery attempts logged in audit_events.jsonl

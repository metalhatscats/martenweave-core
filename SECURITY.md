# Security Policy

Martenweave Core is local-first and does not require cloud services for core validation, indexing, search, trace, impact, or reporting workflows.

## Supported Versions

Security fixes are expected on the current active minor release while the project is in `0.x`.

| Version | Supported |
|---|---|
| 0.4.x | Yes |
| Older 0.x | Best effort |

## Reporting a Vulnerability

Use GitHub private vulnerability reporting for the core repository when it is available. If private reporting is not enabled, contact the maintainers through repository owner channels and avoid posting exploit details, credentials, or private data in a public issue.

Include:

- affected command, module, or integration
- reproduction steps using synthetic data
- expected impact
- whether secrets, raw datasets, generated artifacts, or external writes are involved

Do not attach real client data, credentials, API keys, SAP extracts, or proprietary mappings.

## Security Boundaries

- `.env`, credentials, private keys, and generated artifacts are ignored by default.
- Raw datasets are inputs only; they are not canonical model truth.
- AI providers are optional. The default adapter is deterministic and makes no provider call.
- AI must not silently mutate canonical model files.
- Generated indexes are rebuildable from canonical files and should not be treated as authority.

# Synthetic Enterprise Portfolio Demo

A privacy-safe, multi-domain repository for showing what Martenweave does in a
real governance workflow. Every company, person, system, identifier, and event
in this example is fictional; it contains no production data or credentials.

## What this demonstrates

| Capability | Synthetic evidence in this repository |
| --- | --- |
| One model, several domains | Customer, Supplier, and Product have separate domain, entity, and accountable team objects. |
| Clear ownership | Each governed attribute, endpoint, mapping, rule, issue, and decision has a business owner, technical owner and/or data steward. |
| Traceable integration | 36 source-to-hub endpoints and 18 mappings reveal where a value came from and where it lands. |
| Deterministic controls | 18 validation rules establish completeness checks for every managed attribute. |
| Governed work | Three active review issues and three stewardship decisions make the operational backlog visible. |
| Local audit history | The `enterprise` generator creates `generated/audit_events.jsonl` with synthetic index, validation, and ownership-review events. Real commands append new events locally. |

## Explore it in the Workbench

Open this directory through **Workspace → Open existing**. The Workbench keeps
one local repository active at a time, so switching to another model is explicit
and cannot accidentally combine canonical files from separate workspaces.

Start with these IDs:

- `DOMAIN-CUSTOMER`, `DOMAIN-SUPPLIER`, and `DOMAIN-PRODUCT` to compare the three portfolios.
- `ATTR-SUPPLIER-STATUS` to see ownership, a controlled list, validation, and its endpoints.
- `MAP-PRODUCT-RISK-TO-HUB` to follow a source-to-governance mapping.
- `ISS-CUSTOMER-CLASSIFICATION-REVIEW` to show an assigned operational review item.

## Run the checks

```bash
martenweave validate --repo examples/synthetic_enterprise_portfolio_demo
martenweave build-index --repo examples/synthetic_enterprise_portfolio_demo --jsonl
martenweave health --repo examples/synthetic_enterprise_portfolio_demo
martenweave owners --repo examples/synthetic_enterprise_portfolio_demo
martenweave audit-log --repo examples/synthetic_enterprise_portfolio_demo
martenweave trace ATTR-SUPPLIER-STATUS --repo examples/synthetic_enterprise_portfolio_demo
martenweave impact FEP-HUB-PRODUCT-RISK --repo examples/synthetic_enterprise_portfolio_demo
```

The generated index and audit log are disposable local artifacts. To recreate
this exact fixture in a temporary directory, call
`generate_fixture_repo(path, profile="enterprise")` from
`modelops_core.fixtures.fixture_generator`.

# Permission Boundaries and Role-Based Action Policy

## Action Categories

| Category | Examples |
|---|---|
| Read | view, search, trace, impact, health, analyze |
| Analyze | validate, build-index, coverage report |
| Export | export workbook, JSONL, audit log |
| Propose | create PatchProposal, suggest metadata |
| Approve | accept/reject PatchProposal |
| Apply | apply approved PatchProposal |
| Integrate | import dataset, sync external system |
| Publish | generate docs, share scorecard |
| Administer | manage config, domain packs, users |

## Roles

| Role | Permissions |
|---|---|
| Viewer | Read, Analyze |
| Analyst | Read, Analyze, Export |
| Model Maintainer | + Propose, Integrate |
| Data Steward | + Approve |
| Approver | + Apply (gated) |
| Integration Owner | + Integrate, Publish |
| Admin | All |

## Local-First Enforcement

v1 does not require enterprise IAM:
- CLI: OS user identity
- API/MCP: simple token or localhost-only
- UI: local session

## Safe Defaults

- MCP tools default to read-only
- Proposal creation allowed, apply requires explicit flag
- External writes require explicit config
- Audit log records all actions regardless of role

## Future Integration

- SSO/OAuth integration points documented
- Enterprise RBAC mapping to action categories
- No implementation until post-v1

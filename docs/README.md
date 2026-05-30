# Martenweave Documentation Index

> Find the right document by audience and topic.

---

## Getting Started

| Document | What you will learn |
|---|---|
| [README.md](../README.md) | Install, quickstart, command reference, core principles |
| [docs/what-to-use-first.md](what-to-use-first.md) | Choose your first example or template |
| [docs/first-15-minutes.md](first-15-minutes.md) | Step-by-step first workflow from clone to insight |
| [docs/user-guide.md](user-guide.md) | Day-to-day CLI usage patterns and examples |
| [docs/martenweave-data-model-book.md](martenweave-data-model-book.md) | How to create, maintain, and govern models correctly |
| [docs/pilot-package.md](pilot-package.md) | 1–2 week pilot workflow for new teams |

---

## Architecture

| Document | What you will learn |
|---|---|
| [docs/architecture/AGENT_QUICK_REFERENCE.md](architecture/AGENT_QUICK_REFERENCE.md) | **Start here** — concise object types, validation layers, CLI, file layout |
| [docs/architecture/SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md) | Full system architecture, components, data flows |
| [docs/architecture/DOMAIN_MODEL.md](architecture/DOMAIN_MODEL.md) | Conceptual domain model, object relationships |
| [docs/architecture/CORE_DOMAIN_MODEL.md](architecture/CORE_DOMAIN_MODEL.md) | Core domain model boundaries |
| [docs/architecture/DATA_LINEAGE_AND_IMPACT_MODEL.md](architecture/DATA_LINEAGE_AND_IMPACT_MODEL.md) | Lineage and impact analysis design |
| [docs/architecture/AI_PATCH_WORKFLOW.md](architecture/AI_PATCH_WORKFLOW.md) | AI patch proposal workflow |
| [docs/architecture/PATCH_PROPOSAL_AND_APPROVAL_FLOW.md](architecture/PATCH_PROPOSAL_AND_APPROVAL_FLOW.md) | Patch proposal and approval flow |
| [docs/architecture/SCHEMA_AND_VALIDATION_SPEC.md](architecture/SCHEMA_AND_VALIDATION_SPEC.md) | Schema and validation specification |
| [docs/architecture/CANONICAL_MODEL_BOUNDARY.md](architecture/CANONICAL_MODEL_BOUNDARY.md) | What belongs in canonical files |
| [docs/architecture/GENERATED_INDEX_BOUNDARY.md](architecture/GENERATED_INDEX_BOUNDARY.md) | What belongs in generated artifacts |
| [docs/architecture/INTEGRATION_BOUNDARIES.md](architecture/INTEGRATION_BOUNDARIES.md) | Integration boundaries and contracts |
| [docs/architecture/MODEL_REPOSITORY_SPEC.md](architecture/MODEL_REPOSITORY_SPEC.md) | Repository layout and file format spec |
| [docs/architecture/ARCHITECTURE_DECISIONS.md](architecture/ARCHITECTURE_DECISIONS.md) | Key architecture decisions |
| [docs/canonical-model.md](canonical-model.md) | Canonical model format reference |
| [docs/canonical-status-lifecycle.md](canonical-status-lifecycle.md) | Status meanings by object kind |
| [docs/model-metadata-taxonomy.md](model-metadata-taxonomy.md) | Metadata taxonomy and mandatory fields |

---

## Developer Guide

| Document | What you will learn |
|---|---|
| [docs/developer/LOCAL_SETUP.md](developer/LOCAL_SETUP.md) | Development environment setup |
| [docs/developer/CODE_STYLE.md](developer/CODE_STYLE.md) | Code style and conventions |
| [docs/developer/TESTING_STRATEGY.md](developer/TESTING_STRATEGY.md) | Testing approach and patterns |
| [docs/developer/CLI_CONTRACTS.md](developer/CLI_CONTRACTS.md) | CLI command contracts and JSON output specs |
| [docs/developer/ADDING_CLI_COMMANDS.md](developer/ADDING_CLI_COMMANDS.md) | How to add a new CLI command |
| [docs/developer/ADDING_OBJECT_TYPES.md](developer/ADDING_OBJECT_TYPES.md) | How to add a new canonical object type |
| [docs/developer/ADDING_VALIDATION_RULES.md](developer/ADDING_VALIDATION_RULES.md) | How to add a new validation rule |
| [docs/developer/ADDING_DOMAIN_PACKS.md](developer/ADDING_DOMAIN_PACKS.md) | How to add a new domain pack |
| [docs/ai/VALIDATION_LADDER.md](ai/VALIDATION_LADDER.md) | Validation ladder from static checks to e2e |
| [docs/validation-methodology-warnings.md](validation-methodology-warnings.md) | Warning-only validation codes and fixes |
| [docs/model-side-gaps.md](model-side-gaps.md) | Model-side gap detection with `--check-model` |

---

## Product and Commercial

| Document | What you will learn |
|---|---|
| [docs/product/ACCEPTANCE_CRITERIA.md](product/ACCEPTANCE_CRITERIA.md) | Product acceptance criteria |
| [docs/product/MVP_SCOPE.md](product/MVP_SCOPE.md) | MVP boundary and scope |
| [docs/product/ROADMAP_V0_1.md](product/ROADMAP_V0_1.md) | v0.1 roadmap |
| [docs/commercial-positioning.md](commercial-positioning.md) | ICP, buyer personas, positioning |
| [docs/commercial-packaging.md](commercial-packaging.md) | Packaging options and pricing hypotheses |
| [docs/pilot-package.md](pilot-package.md) | Pilot workflow and success metrics |
| [docs/product-discovery-interviews.md](product-discovery-interviews.md) | Interview guide for target teams |
| [docs/team-collaboration-model.md](team-collaboration-model.md) | Roles, workflows, and collaboration patterns |
| [docs/security-procurement-checklist.md](security-procurement-checklist.md) | Security and procurement readiness |

---

## AI and Agent Integration

| Document | What you will learn |
|---|---|
| [docs/ai-provider-architecture.md](ai-provider-architecture.md) | AI provider adapter architecture |
| [docs/ai-usage-telemetry.md](ai-usage-telemetry.md) | AI usage telemetry design |
| [docs/mcp-server-design.md](mcp-server-design.md) | MCP server design |
| [docs/ai/KIMI_GITHUB_ISSUE_LOOP.md](ai/KIMI_GITHUB_ISSUE_LOOP.md) | Agent issue loop workflow |
| [docs/ai/VALIDATION_LADDER.md](ai/VALIDATION_LADDER.md) | Validation ladder for agents |
| [docs/ai/CLOSEOUT_REPORT_TEMPLATE.md](ai/CLOSEOUT_REPORT_TEMPLATE.md) | Closeout report template |
| [docs/ai/AGENT_SAFETY_RULES.md](ai/AGENT_SAFETY_RULES.md) | Agent safety rules |
| [docs/ai/ONE_ISSUE_AGENT_PROMPT.md](ai/ONE_ISSUE_AGENT_PROMPT.md) | Copyable one-issue execution prompt |
| [docs/ai/AI_DEVELOPMENT_OPERATING_SYSTEM.md](ai/AI_DEVELOPMENT_OPERATING_SYSTEM.md) | AI development operating model |

---

## Integration and Import/Export

| Document | What you will learn |
|---|---|
| [docs/dbt-analytics-import.md](dbt-analytics-import.md) | dbt analytics model import design |
| [docs/database-metadata-import.md](database-metadata-import.md) | Database metadata import design |
| [docs/json-schema-openapi-import.md](json-schema-openapi-import.md) | JSON Schema and OpenAPI import design |
| [docs/google-drive-sheets-integration.md](google-drive-sheets-integration.md) | Google Drive and Sheets integration |
| [docs/graph-projection-export-contract.md](graph-projection-export-contract.md) | Graph projection export contract |
| [docs/openlineage-export.md](openlineage-export.md) | OpenLineage-compatible export design |
| [docs/operations/IMPORT_EXPORT_SPEC.md](operations/IMPORT_EXPORT_SPEC.md) | Import/export specification |

---

## Operations

| Document | What you will learn |
|---|---|
| [docs/operations/deployment-options.md](operations/deployment-options.md) | Deployment options |
| [docs/operations/cache-and-generated-artifacts.md](operations/cache-and-generated-artifacts.md) | Cache and generated artifact management |
| [docs/operations/diagnostics-export.md](operations/diagnostics-export.md) | Diagnostics export |
| [docs/operations/backup-restore.md](operations/backup-restore.md) | Backup and restore |
| [docs/operations/permission-boundaries.md](operations/permission-boundaries.md) | Permission boundaries |

---

## Design Documents (Deep Dives)

| Document | Topic |
|---|---|
| [docs/change-workflow.md](change-workflow.md) | Change workflow design |
| [docs/system-lineage-model.md](system-lineage-model.md) | System lineage model |
| [docs/relationship-taxonomy.md](relationship-taxonomy.md) | Relationship taxonomy |
| [docs/domain-packs.md](domain-packs.md) | Domain packs strategy |
| [docs/modeling-methodology.md](modeling-methodology.md) | Modeling methodology |
| [docs/bulk-refactor-operations.md](bulk-refactor-operations.md) | Bulk refactor operations |
| [docs/conflict-detection.md](conflict-detection.md) | Conflict detection |
| [docs/runtime-memory-and-resource-limits.md](runtime-memory-and-resource-limits.md) | Resource limits |
| [docs/neo4j-graph-projection.md](neo4j-graph-projection.md) | Neo4j graph projection evaluation |
| [docs/graph-visualization-layer.md](graph-visualization-layer.md) | Graph visualization layer |
| [docs/chat-to-model-contract.md](chat-to-model-contract.md) | Chat-to-model contract |

---

## Contributing

- Follow [docs/developer/CODE_STYLE.md](developer/CODE_STYLE.md)
- Run the validation ladder in [docs/ai/VALIDATION_LADDER.md](ai/VALIDATION_LADDER.md)
- Use the closeout template in [docs/ai/CLOSEOUT_REPORT_TEMPLATE.md](ai/CLOSEOUT_REPORT_TEMPLATE.md)

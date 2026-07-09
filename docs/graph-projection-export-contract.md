<!-- modelops-freshness-ignore: all -->

# Graph Projection Export Contract

## Goal
Define a stable export contract so Martenweave can feed Neo4j or other graph engines from canonical files and generated lineage indexes without making the graph engine a dependency of core.

## Scope

This document specifies:

- Graph node schema (what fields every node export must contain)
- Graph edge schema (what fields every edge export must contain)
- Node categories mapped from canonical object types
- Edge types mapped from the relationship taxonomy
- Export formats: JSONL and Neo4j CSV
- Future CLI command design
- Safety and privacy boundaries

## Design Principles

1. **Generated view only.** Graph exports are rebuildable artifacts. They are not canonical truth.
2. **No new runtime dependency.** The contract is a document and a data schema. Neo4j is not required to use Martenweave.
3. **Secrets excluded by default.** Raw credentials, dataset samples, and prompt content are never exported.
4. **Stable IDs.** Node IDs are canonical object IDs. This makes graph exports deterministic and idempotent.

## Node Schema

Every exported node must contain these fields:

| Field | Type | Description |
|---|---|---|
| `node_id` | string | Canonical object ID (e.g., `ATTR-CUST-SALES-CUSTOMER-GROUP`) |
| `node_type` | string | Canonical object type (e.g., `Attribute`) |
| `node_label` | string | Human-readable label for graph visualization |
| `domain` | string | Owning domain ID, if any |
| `status` | string | Lifecycle status |
| `name` | string | Short name, if available |
| `title` | string | Title, if available |
| `description` | string | Description, truncated to 500 chars |
| `source_file` | string | Relative path to canonical file |

Optional metadata fields (included when available):

| Field | Type | Description |
|---|---|---|
| `system` | string | System ID (for System-related objects) |
| `endpoint_type` | string | Endpoint classification |
| `flow_type` | string | Flow classification |
| `step_type` | string | Step classification |
| `rule_type` | string | Rule classification |
| `context_category` | string | Context category |
| `schema_version` | string | Object schema version |

### Node Categories

Nodes are exported for every canonical object type. The `node_type` field is the canonical object type string.

Core node types:

- `MasterDataDomain`
- `BusinessEntity`
- `EntityContext`
- `Attribute`
- `AttributeUsage`
- `FieldEndpoint`
- `System`
- `SystemEnvironment`
- `Interface`
- `InterfaceEndpoint`
- `Application`
- `IntegrationFlow`
- `DataFlowStep`
- `TransformationRule`
- `Dataset`
- `Mapping`
- `MappingSet`
- `ValueList`
- `ValueMapping`
- `ValidationRule`
- `BusinessRule`
- `DataQualityCheck`
- `Issue`
- `Risk`
- `Decision`
- `ChangeRequest`
- `PatchProposal`
- `Evidence`
- `Person`
- `Team`
- `OwnershipRole`

## Edge Schema

Every exported edge must contain these fields:

| Field | Type | Description |
|---|---|---|
| `from_node_id` | string | Source node canonical ID |
| `to_node_id` | string | Target node canonical ID |
| `edge_type` | string | Relationship type (e.g., `has_attribute`) |
| `edge_class` | string | Relationship class (e.g., `core_dependency`) |
| `source_file` | string | Relative path to canonical file that declared the relationship |
| `confidence` | string | `explicit` for all frontmatter-derived edges |

### Edge Types

Edge types are derived directly from the relationship taxonomy in `schemas/registry.py`:

Core dependency edges:
- `belongs_to_domain`
- `part_of_migration`
- `belongs_to_entity`
- `used_in_context`
- `part_of_entity`
- `represents_attribute`
- `has_attribute`
- `implemented_by_field`

Context edges:
- `located_in_system`
- `flows_from`
- `flows_to`
- `used_by_application`

Mapping edges:
- `mapped_from`
- `mapped_to`
- `maps_from_values`
- `maps_to_values`
- `uses_value_mapping`
- `uses_mapping`
- `part_of_mapping_set`
- `reads_from`
- `writes_to`

Flow edges:
- `part_of_interface`
- `part_of_flow`
- `preceded_by`
- `followed_by`
- `applies_transformation`

Validation edges:
- `has_allowed_values`
- `validated_by`

Governance edges:
- `affected_by_issue`
- `explained_by_decision`
- `proposed_by`
- `affects`
- `owned_by_business`
- `owned_by_technical`
- `stewarded_by`
- `approved_by`
- `accountable_to`

Evidence edges:
- `supported_by_evidence`

Reference edges:
- `part_of_value_list`
- `related_to`

## Export Formats

### JSONL

Two files are produced:

- `graph_nodes.jsonl` — one JSON object per line, following the node schema
- `graph_edges.jsonl` — one JSON object per line, following the edge schema

Example node:

```json
{
  "node_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "node_type": "Attribute",
  "node_label": "Customer Group",
  "domain": "DOMAIN-CUSTOMER-BP",
  "status": "draft",
  "name": "Customer Group",
  "source_file": "model/ATTR-CUST-SALES-CUSTOMER-GROUP.md"
}
```

Example edge:

```json
{
  "from_node_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "to_node_id": "FEP-S4-KNVV-KDGRP",
  "edge_type": "implemented_by_field",
  "edge_class": "core_dependency",
  "source_file": "model/ATTR-CUST-SALES-CUSTOMER-GROUP.md",
  "confidence": "explicit"
}
```

### Neo4j CSV

Two CSV files are produced for bulk import with `neo4j-admin import` or `LOAD CSV`:

- `graph_nodes.csv` — header row + one row per node
- `graph_edges.csv` — header row + one row per edge

The CSV schemas match the JSONL schemas exactly (same field names) so converters are trivial.

## Future CLI Command

```bash
# Export graph as JSONL
modelops graph-export --repo ./my-model --format jsonl

# Export graph as Neo4j CSV
modelops graph-export --repo ./my-model --format neo4j-csv

# Export only a subset of node types
modelops graph-export --repo ./my-model --format jsonl \
  --include-types System,Interface,IntegrationFlow,DataFlowStep

# Export with custom output directory
modelops graph-export --repo ./my-model --format jsonl --out ./graph-export
```

Output structure:

```
generated/
  graph_nodes.jsonl
  graph_edges.jsonl
```

## Implementation Notes

The graph export is a projection over two existing sources:

1. **Nodes** — derived from the `objects` table in the SQLite index.
2. **Edges** — derived from the `object_relationships` table in the SQLite index.

No new index tables are required. A future `graph-export` command reads the existing index and writes the formatted output.

### Node export query (SQLite)

```sql
SELECT
  id AS node_id,
  type AS node_type,
  COALESCE(name, title, id) AS node_label,
  domain,
  status,
  name,
  title,
  description,
  source_file
FROM objects;
```

### Edge export query (SQLite)

```sql
SELECT
  from_object_id AS from_node_id,
  to_object_id AS to_node_id,
  relationship_type AS edge_type,
  relationship_class AS edge_class,
  source_file,
  confidence
FROM object_relationships;
```

## Privacy and Safety

- **No secrets:** `endpoint_url`, `connection_string`, `api_key`, and similar fields must never be stored in canonical frontmatter. If they are, they must be filtered from graph export.
- **No raw data:** Dataset samples, prompt content, and raw model responses are excluded.
- **Truncation:** Descriptions longer than 500 characters are truncated in node export to keep graph payloads bounded.

## Out of Scope

- **Live Neo4j connector** — not part of this contract. A future issue may add an optional `Neo4jConnector` that implements `ConnectorAdapter`.
- **Graph layout algorithms** — visualization concerns belong to the UI layer (issue #66).
- **Runtime lineage events** — this contract covers design-time lineage only. Runtime job execution tracking is a future extension.

## Acceptance Criteria

- [x] Graph node and edge schemas are documented and stable.
- [x] Node categories cover all current canonical object types.
- [x] Edge types cover all current relationship types including system lineage.
- [x] JSONL and Neo4j CSV formats are specified.
- [x] Future CLI command is designed.
- [x] Export excludes secrets and sensitive data by default.
- [x] Design supports small and enterprise-scale graphs.

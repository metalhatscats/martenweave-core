# OpenLineage-Compatible Export Design

## Goal
Explore OpenLineage-compatible export as an interoperability option for Martenweave system lineage without replacing the internal canonical model.

## What is OpenLineage

[OpenLineage](https://openlineage.io/) is an open standard for data lineage. It defines a JSON-based event format that captures:

- **Jobs** — units of work (e.g., ETL pipelines, SQL queries)
- **Datasets** — data sources and targets (e.g., tables, files)
- **Runs** — executions of jobs
- **Inputs / Outputs** — dataset consumption and production by jobs
- **Facets** — extensible metadata about jobs, datasets, and runs

OpenLineage is supported by data catalog tools such as Marquez, DataHub, and Atlan.

## Mapping Strategy

Martenweave is richer in governance and model semantics than standard operational lineage. The mapping is lossy by design: we export what fits into OpenLineage and keep the rest in Martenweave.

### Martenweave → OpenLineage Concept Map

| Martenweave | OpenLineage | Notes |
|---|---|---|
| `IntegrationFlow` | `Job` | A flow is a unit of work orchestrating data movement |
| `DataFlowStep` | `Job` (sub-job) or facet | Steps can be nested jobs or facets on the parent flow |
| `System` | `Dataset` namespace prefix | System becomes part of dataset namespace |
| `Dataset` | `Dataset` | Direct mapping |
| `FieldEndpoint` | `Dataset` column facet | Physical field maps to column metadata |
| `Interface` | `Dataset` or `Job` | APIs can be datasets; batch interfaces can be jobs |
| `InterfaceEndpoint` | `Dataset` | Endpoint URL/path as dataset location |
| `TransformationRule` | `Job` transformation facet | Rule logic described in a custom facet |
| `Attribute` | Custom facet on `Dataset` | Business meaning attached as a `martenweave_attribute` facet |
| `Mapping` | Input/output lineage | Source → target mapping expressed as job inputs/outputs |
| `Person` / `Team` | `Ownership` facet | Owner, steward, approver mapped to ownership facets |
| `ValueList` | `Dataset` schema facet | Allowed values as enum constraints |
| `ValidationRule` | `DataQuality` facet | Validation expectations as data quality facets |

### What Does Not Map Cleanly

| Martenweave Concept | Gap | Recommendation |
|---|---|---|
| `BusinessEntity` | OpenLineage has no business entity concept | Export as custom `martenweave_entity` facet on Dataset |
| `MasterDataDomain` | OpenLineage has no domain concept | Use namespace prefix or custom facet |
| `Issue` / `Risk` / `Decision` | No governance object types | Custom `martenweave_governance` facet |
| `ChangeRequest` / `PatchProposal` | No change management concept | Omit from OpenLineage export |
| `Evidence` | No evidence concept | Omit or attach as custom facet |
| `AttributeUsage` | No usage context concept | Export as custom `martenweave_usage` facet |

## Export Format

### Job Event (IntegrationFlow)

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-05-25T10:00:00Z",
  "run": {
    "runId": "run-flow-product-to-ecommerce-001"
  },
  "job": {
    "namespace": "martenweave",
    "name": "FLOW-PRODUCT-TO-ECOMMERCE",
    "facets": {
      "martenweave_flow": {
        "flowType": "batch_file",
        "sourceSystem": "SYSTEM-ERP",
        "targetSystem": "SYSTEM-ECOMMERCE"
      }
    }
  },
  "inputs": [
    {
      "namespace": "martenweave/systems/SYSTEM-ERP",
      "name": "IFACE-ENDPOINT-ERP-API",
      "facets": {
        "schema": {
          "fields": [
            {"name": "product_id", "type": "STRING"},
            {"name": "price", "type": "DECIMAL"}
          ]
        }
      }
    }
  ],
  "outputs": [
    {
      "namespace": "martenweave/systems/SYSTEM-ECOMMERCE",
      "name": "products",
      "facets": {
        "schema": {
          "fields": [
            {"name": "id", "type": "STRING"},
            {"name": "display_price", "type": "DECIMAL"}
          ]
        }
      }
    }
  ],
  "producer": "https://github.com/metalhatscats/martenweave-core"
}
```

### Dataset Event (FieldEndpoint)

A `FieldEndpoint` can be represented as a column within a dataset schema facet. For export simplicity, groups of related endpoints under a system can be emitted as a synthetic dataset:

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-05-25T10:00:00Z",
  "job": {
    "namespace": "martenweave",
    "name": "index-export"
  },
  "inputs": [],
  "outputs": [
    {
      "namespace": "martenweave/systems/SYSTEM-ERP",
      "name": "product_master",
      "facets": {
        "schema": {
          "fields": [
            {
              "name": "KDGRP",
              "type": "STRING",
              "description": "Customer Group",
              "facets": {
                "martenweave_attribute": {
                  "attributeId": "ATTR-CUST-SALES-CUSTOMER-GROUP",
                  "domain": "DOMAIN-CUSTOMER-BP"
                }
              }
            }
          ]
        }
      }
    }
  ]
}
```

## Custom Facets

Martenweave-specific metadata is attached through custom facets prefixed with `martenweave_`:

| Facet Name | Attached To | Content |
|---|---|---|
| `martenweave_attribute` | Dataset column | Attribute ID, domain, semantic category |
| `martenweave_flow` | Job | Flow type, source/target systems |
| `martenweave_transformation` | Job | Rule type, source/target endpoints |
| `martenweave_ownership` | Dataset or Job | Owner, steward, approver IDs |
| `martenweave_governance` | Dataset or Job | Related issues, decisions, risks |
| `martenweave_entity` | Dataset | Business entity ID, context category |

## Future CLI Command

```bash
# Export lineage as OpenLineage JSONL events
modelops export-lineage --repo ./my-model --format openlineage

# Export only system lineage objects
modelops export-lineage --repo ./my-model --format openlineage \
  --types IntegrationFlow,DataFlowStep,TransformationRule

# Export with synthetic run IDs for catalog ingestion
modelops export-lineage --repo ./my-model --format openlineage \
  --run-prefix "martenweave-export-"
```

Output: `generated/openlineage_events.jsonl` with one OpenLineage event per line.

## Limitations and Honest Gaps

1. **No runtime data.** Martenweave tracks design-time lineage. OpenLineage consumers may expect run-level timestamps, durations, and row counts. These must be stubbed or omitted.
2. **No automatic discovery.** Martenweave lineage is explicitly authored, not extracted from query logs. The export reflects declared relationships, not observed execution.
3. **Governance richness is lossy.** Issues, decisions, risks, and evidence do not fit neatly into OpenLineage. They are either omitted or squeezed into custom facets.
4. **Synthetic datasets.** FieldEndpoints are not datasets in the OpenLineage sense. The export groups them into synthetic datasets by system, which is a modeling approximation.

## Safety Notes

- Secrets are never included in OpenLineage export. Endpoint URLs in `InterfaceEndpoint` objects must be redacted or omitted.
- The export is a generated view. Canonical files remain the source of truth.
- No OpenLineage client library is required for core. The export is plain JSONL.

## Out of Scope

- **Live OpenLineage integration** — emitting events to a running Marquez or Kafka topic is not covered here.
- **Bidirectional sync** — importing OpenLineage events back into Martenweave is not supported.
- **OpenLineage client SDK** — no Python SDK dependency is added.

## Recommendation

OpenLineage export is a **useful interoperability bridge** for teams already using OpenLineage-compatible catalogs. It should be implemented as an optional export format after the core graph-export feature (issue #76) is stable. The custom facet strategy preserves Martenweave's richer semantics without forcing an unnatural mapping.

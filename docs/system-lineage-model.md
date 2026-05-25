# System Lineage Model

## Goal
Model how data moves across systems, interfaces, APIs, files, tables, and transformations so Martenweave can trace a field or attribute through the full enterprise flow.

## Scope

This document describes the canonical object types and reference fields added to support system lineage. It covers:

- Object types for system landscape modeling
- Reference fields for flow relationships
- How lineage edges are generated automatically
- How trace and impact analysis work across systems
- Example: a three-step ETL flow from ERP to e-commerce

## Object Types

Five new canonical object types extend the model registry:

| Type | Purpose |
|---|---|
| `Application` | A software application running in the landscape |
| `InterfaceEndpoint` | A concrete endpoint (URL, queue, file path, API operation) |
| `IntegrationFlow` | A data flow connecting a source system to a target system |
| `DataFlowStep` | A single step inside an integration flow (extract, transform, load) |
| `TransformationRule` | A rule that transforms data from a source to a target representation |

Existing types `System` and `Interface` are reused. No SAP-specific types are required.

## Reference Fields

System lineage relationships are expressed through frontmatter reference fields. The index builder converts these into lineage edges automatically.

### Application

```yaml
system: SYSTEM-ERP
```

Relationship: `located_in_system` (class: `context`)

### InterfaceEndpoint

```yaml
interface: IFACE-PRODUCT-SYNC
system: SYSTEM-ERP
application: APP-ECOMMERCE-API
```

Relationships:
- `part_of_interface` → Interface
- `located_in_system` → System
- `used_by_application` → Application

### IntegrationFlow

```yaml
source_system: SYSTEM-ERP
target_system: SYSTEM-ECOMMERCE
interface: IFACE-PRODUCT-SYNC
```

Relationships:
- `flows_from` → System
- `flows_to` → System
- `part_of_interface` → Interface

### DataFlowStep

```yaml
integration_flow: FLOW-PRODUCT-TO-ECOMMERCE
source_step: STEP-PRODUCT-EXTRACT
target_step: STEP-PRODUCT-LOAD
transformation_rule: TRULE-PRODUCT-PRICE-FORMAT
source_field_endpoint: FEP-ERP-PRICE
target_field_endpoint: FEP-ECOM-PRICE
```

Relationships:
- `part_of_flow` → IntegrationFlow
- `preceded_by` → DataFlowStep
- `followed_by` → DataFlowStep
- `applies_transformation` → TransformationRule
- `reads_from` → FieldEndpoint
- `writes_to` → FieldEndpoint

### TransformationRule

```yaml
source_field_endpoint: FEP-ERP-PRICE
target_field_endpoint: FEP-ECOM-PRICE
attribute: ATTR-PRODUCT-PRICE
```

Relationships:
- `reads_from` → FieldEndpoint
- `writes_to` → FieldEndpoint
- `has_attribute` → Attribute

## Example Flow

A complete three-step batch flow from ERP to e-commerce:

```
SYSTEM-ERP
  └─ IFACE-PRODUCT-SYNC
       └─ IFACE-ENDPOINT-ERP-API
  └─ APP-ECOMMERCE-API (runs on SYSTEM-ECOMMERCE)
       └─ IFACE-ENDPOINT-ERP-API

FLOW-PRODUCT-TO-ECOMMERCE
  ├─ flows_from: SYSTEM-ERP
  ├─ flows_to: SYSTEM-ECOMMERCE
  └─ part_of_interface: IFACE-PRODUCT-SYNC

STEP-PRODUCT-EXTRACT
  ├─ part_of_flow: FLOW-PRODUCT-TO-ECOMMERCE
  └─ followed_by: STEP-PRODUCT-TRANSFORM

STEP-PRODUCT-TRANSFORM
  ├─ part_of_flow: FLOW-PRODUCT-TO-ECOMMERCE
  ├─ preceded_by: STEP-PRODUCT-EXTRACT
  ├─ followed_by: STEP-PRODUCT-LOAD
  └─ applies_transformation: TRULE-PRODUCT-PRICE-FORMAT

STEP-PRODUCT-LOAD
  ├─ part_of_flow: FLOW-PRODUCT-TO-ECOMMERCE
  └─ preceded_by: STEP-PRODUCT-TRANSFORM
```

## Trace and Impact

Because lineage edges are stored in the same `object_relationships` table as all other references, trace and impact analysis work without code changes:

```bash
# Trace a field through the system landscape
modelops trace SYSTEM-ERP --repo ./my-model --json

# Impact analysis for a transformation rule
modelops impact TRULE-PRODUCT-PRICE-FORMAT --repo ./my-model --json
```

The BFS traversal walks `flows_from` / `flows_to`, `part_of_flow`, `preceded_by` / `followed_by`, and all other relationship types naturally.

## Validation

All new object types participate in the standard validation pipeline:

- Layer 1: ID format, type registration, status presence
- Layer 2: Broken reference detection, type mismatch checking
- Layer 3: Domain-pack-specific rules (none required for system lineage)

## Index and Export

The SQLite index and JSONL exports include system lineage edges automatically. No additional export logic is needed.

Example JSONL edge:

```json
{
  "from_object_id": "FLOW-PRODUCT-TO-ECOMMERCE",
  "relationship_type": "flows_from",
  "relationship_class": "context",
  "to_object_id": "SYSTEM-ERP",
  "source_file": "model/FLOW-PRODUCT-TO-ECOMMERCE.md",
  "confidence": "explicit"
}
```

## Out of Scope

- **Real-time event streaming metadata** — can be modeled with existing types but no native event-log integration.
- **MessageSchema** — not included in this slice; can be added later if needed.
- **Schedule / Trigger** — not included; cron schedules and triggers are documented as future extensions.
- **Runtime execution data** — lineage tracks design-time relationships, not runtime job instances.
- **OpenLineage compatibility** — covered by issue #67.

## Safety Notes

- System lineage objects are canonical files like all others. They require the same proposal/approval workflow for changes.
- No external service calls are made to discover lineage. Relationships are declared explicitly in frontmatter.
- Credentials for interfaces are not stored in canonical objects.

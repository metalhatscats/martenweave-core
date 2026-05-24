# Data Contracts

Data contracts describe expectations for datasets, APIs, files, interfaces, and system-to-system flows.

## Contract Concepts

| Concept | Description |
|---|---|
| `DataContract` | Agreement between producer and consumer |
| `producer` | System or team producing data |
| `consumer` | System or team consuming data |
| `dataset` | Specific dataset or API endpoint |
| `schema` | Expected fields, types, structures |
| `quality_expectations` | Completeness, freshness, accuracy |
| `delivery_schedule` | Frequency, SLA |
| `change_policy` | How changes are communicated |

## Relationships

```
DataContract → System (producer, consumer)
DataContract → Dataset / Interface
DataContract → FieldEndpoint (schema fields)
DataContract → Attribute (business meaning)
DataContract → ValidationRule (quality rules)
DataContract → ValueList (allowed values)
DataContract → ChangeRequest (contract changes)
```

## Status

- `draft` → `proposed` → `agreed` → `active` → `deprecated` → `retired`

## v1 Scope

Contracts are governance artifacts only:
- Documented in canonical files
- Traced to model objects
- Changes follow PatchProposal workflow

## Later

- Contract validation against actual datasets
- Machine-readable exports (JSON Schema, Avro, Protobuf)
- Automated compatibility checks

# Core Domain Model

## Purpose

Martenweave Core represents data model knowledge in a domain-neutral way. It models meaning, representation, movement, rules, ownership, evidence, issues, decisions, and proposed changes.

## Core Object Groups

| Group | Object types |
|---|---|
| Scope | `MasterDataDomain`, `MigrationObject`, `BusinessEntity`, `EntityContext` |
| Meaning | `Attribute`, `AttributeUsage`, `BusinessRule` |
| Representation | `System`, `SystemEnvironment`, `FieldEndpoint`, `Interface`, `Dataset` |
| Movement | `MappingSet`, `Mapping`, `ValueList`, `ValueMapping`, `TransformationLogic` |
| Quality | `ValidationRule`, `DataQualityCheck` |
| Governance | `OwnershipRole`, `Person`, `Team`, `Issue`, `Risk`, `Decision`, `ChangeRequest`, `Evidence` |
| AI-safe change | `PatchProposal` |

## Core Distinctions

- An `Attribute` is business meaning.
- A `FieldEndpoint` is a physical representation.
- A `Dataset` is input/evidence, not model truth.
- A `Mapping` links endpoints, not raw columns directly to model truth.
- A `ValidationRule` describes expected correctness.
- A `PatchProposal` is proposed change, not approval.
- A `ChangeRequest` records approved change intent.

## Domain Neutrality

The core model must work for product catalogs, customer files, analytics models, finance reference data, migration models, and other structured data domains.

Vendor-specific fields may exist in canonical objects as optional metadata, but vendor-specific rules belong in domain packs.

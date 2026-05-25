# Domain Pack Boundary

## Principle

Martenweave Core is domain-neutral. Domain packs are optional extensions for specialized examples, starter models, validation rules, and demo workflows.

No domain pack may define core architecture.

## Domain Packs May

- add optional validation rules;
- provide starter canonical objects;
- provide example repositories;
- define domain-specific metadata conventions;
- document domain-specific modeling guidance.

## Domain Packs Must Not

- add required fields to generic core objects;
- make generic validation depend on one domain;
- introduce direct external writes;
- define product MVP scope;
- make SAP, MDM, analytics, finance, or any other domain mandatory.

## Built-In Example

The SAP pack validates SAP table/context relationships such as `KNVV` requiring a customer sales area context. This is a validation extension for SAP repositories only. Generic product, customer, finance, or analytics repositories must work without enabling it.

## Validation

Domain-pack behavior belongs in:

- `src/modelops_core/domain_packs/`
- domain-pack tests such as `tests/test_domain_packs.py`
- optional example repositories or templates

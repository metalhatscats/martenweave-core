# Sample Inputs

> This directory documents the kinds of inputs Martenweave expects during a Migration Model Readiness Assessment.
> All sample data is synthetic. No real client data is used.

## Canonical Model Files

The primary input is a folder of Markdown files with YAML frontmatter.

Example structure:

```
model/
  DOMAIN-CUSTOMER-BP.md
  ENTITY-CUSTOMER-SALES-AREA.md
  ATTR-CUST-SALES-CUSTOMER-GROUP.md
  FEP-S4-KNVV-KDGRP.md
  MAP-CUSTOMER-GROUP-TO-S4.md
  DEC-001.md
  ISS-001.md
```

Each file contains:
- `id`: stable uppercase kebab-case identifier
- `type`: registered object type (Attribute, FieldEndpoint, Mapping, etc.)
- `status`: lifecycle status (draft, active, under_review, etc.)
- Additional fields depending on type

See `examples/customer_bp_model/model/` for a full working example.

## Repository Configuration

`modelops.config.yaml` sits at the repository root:

```yaml
schema_version: "1.0"
name: Customer BP Example
enabled_domain_packs:
  - sap
```

## Sample Datasets

Optional CSV or XLSX files in `data/samples/` can be profiled for gap detection:

```csv
customer_id,sales_org,distribution_channel,division,customer_group
C001,1000,10,00,01
C002,1000,10,00,02
```

Profiling produces column-level statistics that can be compared against FieldEndpoints.

## Notes for PatchProposals

Free-text Markdown notes can be turned into structured PatchProposals:

```markdown
# Note: Missing value mapping for Customer Group

The Customer Group field (KNVV-KDGRP) does not have a value mapping defined for the new sales org 2000.
```

Use `modelops propose-patch --from note.md --repo <repo>` to generate a proposal.

## Getting Started

1. Copy `examples/customer_bp_model` as a starting point.
2. Replace objects with your own migration scope.
3. Run `modelops validate` to check correctness.
4. Run `modelops build-index` to create the SQLite index.
5. Run `modelops assessment run` to generate the output package.

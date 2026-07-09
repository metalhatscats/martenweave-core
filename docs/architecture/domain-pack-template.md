<!-- modelops-freshness-ignore: all -->

# Domain Pack Template

Domain packs extend Martenweave with specialized templates, validation rules, and examples for a specific domain.

## Pack Structure

```
domain-packs/<pack-name>/
  pack.yaml              # metadata, version, dependencies
  templates/             # canonical object templates
  validation_rules/      # additional validation rules
  import_heuristics/     # dataset import hints
  examples/              # sample objects
  docs/                  # domain-specific guidance
```

## pack.yaml

```yaml
id: sap-customer-bp
name: SAP Customer / Business Partner
version: "1.0.0"
dependencies: []
target_systems: [SAP S/4HANA]
object_types:
  - FieldEndpoint
  - EntityContext
  - AttributeUsage
context_rules:
  KNVV: customer_sales_area
  KNB1: customer_company_code
  KNVP: customer_partner_function
  BUT000: bp_central
  LFA1: vendor_general
  LFB1: vendor_company_code
  LFM1: vendor_purchasing_org
```

## Registration

Domain packs are referenced in `modelops.config.yaml`:

```yaml
domain_packs:
  - sap-customer-bp
```

Core remains generic. Packs are optional overlays.

## Example Packs

| Pack | Domain | Objects |
|---|---|---|
| `sap-customer-bp` | SAP MDM | KNVV, KNB1, KNVP, BUT000 |
| `generic-product` | Product catalog | SKU, category, pricing |
| `analytics-dbt` | Analytics | dbt models, sources, exposures |
| `api-contract` | API design | endpoints, schemas, fields |

## Commands (Future)

```bash
modelops domain-pack list
modelops domain-pack inspect sap-customer-bp
modelops scaffold --domain-pack sap-customer-bp
```

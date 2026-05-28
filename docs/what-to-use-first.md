# What to Use First

> A concise decision guide for choosing your first Martenweave example or template.

SAP migration and Master Data Management are the **first domain pack** and proof case, not the product boundary. Martenweave works for any data model: domains, entities, attributes, relationships, datasets, mappings, rules, and change proposals.

---

## Quick Decision

| If you are... | Start with | Why |
|---|---|---|
| New to Martenweave and want the simplest path | `examples/simple_product_model` | One domain, a few attributes, a sample CSV. Minimal concepts, zero SAP context required. |
| Working with SAP Business Partner / Customer master data | `examples/customer_bp_model` | Full canonical model slice with real SAP context (KNVV, KNB1, KNVP, BUT000). |
| Working with SAP Supplier / Vendor master data | `examples/supplier_vendor_model` | Second domain pack with LFA1, LFB1, LFM1 context. |
| Building a generic product or item model from scratch | `examples/generic_product_model` | Slightly broader than simple_product_model, with more attribute types. |
| Starting a brand-new model repository | `templates/model_spines` + `modelops init` | Scaffold a clean repo and copy a template spine as your starting structure. |

---

## Example Comparison

### `simple_product_model`

- **Objects:** ~10 canonical objects
- **Domain:** Product catalog
- **Dataset:** Small CSV with product names and categories
- **Best for:** Understanding validate → build-index → search → gaps in under 10 minutes.

### `customer_bp_model`

- **Objects:** ~50+ canonical objects
- **Domain:** SAP Business Partner → Customer → Sales Area
- **Dataset:** Sample customer master data
- **Best for:** Learning SAP context rules, AttributeUsage, FieldEndpoint mappings, and domain-specific validation.

### `supplier_vendor_model`

- **Objects:** ~40+ canonical objects
- **Domain:** SAP Supplier / Vendor master data
- **Best for:** Exploring a second SAP domain pack and comparing modeling patterns.

---

## Templates

The `templates/model_spines/` directory contains starting structures for new repositories. Use them after running:

```bash
modelops init ./my-model
```

Copy a template spine into `./my-model/model/` and edit IDs, names, and domains to match your project.

---

## Next Steps

1. Pick an example from the table above.
2. Follow the [First 15 Minutes Guide](first-15-minutes.md) for a copy-paste workflow.
3. Read the [User Guide](user-guide.md) for the full Dataset → Model workflow.
4. Explore the [Pilot Package](pilot-package.md) for a 1–2 week team onboarding plan.

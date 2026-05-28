# Customer Business Partner Model Example

This example demonstrates Martenweave in **enterprise object mode**:
a complex SAP migration scenario with multiple entities, contexts,
mappings, validation rules, and decisions.

## Model Structure

| Category | Objects |
|---|---|
| **Domain** | `DOMAIN-CUSTOMER-BP` |
| **Entities** | `ENTITY-BUSINESS-PARTNER`, `ENTITY-BP-CENTRAL`, `ENTITY-BP-CUSTOMER`, `ENTITY-CUSTOMER-SALES-AREA` |
| **Contexts** | `CTX-BP-CENTRAL-S4`, `CTX-BP-COMPANY-CODE-S4`, `CTX-BP-CUSTOMER-S4`, `CTX-CUSTOMER-SALES-AREA-S4` |
| **Attributes** | `ATTR-BP-CENTRAL-NAME`, `ATTR-CUST-SALES-CUSTOMER-GROUP`, `ATTR-BP-COMPANY-CODE-PAYMENT-TERMS` |
| **Field Endpoints** | `FEP-S4-KNVV-KDGRP`, `FEP-S4-KNB1-ZTERM`, `FEP-LEGACY-CUST-GROUP`, `FEP-MIGFILE-CUSTOMER-GROUP` |
| **Mappings** | `MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP`, `MAPSET-CUSTOMER-BP` |
| **Validation** | `VAL-CUST-GROUP-ALLOWED-VALUES` |
| **Value Lists** | `VLIST-LEGACY-CUST-GROUP`, `VLIST-S4-CUST-GROUP` |
| **Value Mappings** | `VMAP-CUST-GROUP-LEGACY-TO-S4` |
| **Decisions** | `DEC-CH01-A17-CUSTOMER-GROUP` |
| **Issues** | `ISS-CH01-A17-CONFIG-GAP` |
| **Migration** | `MIGOBJ-CUSTOMER-BP` |
| **People** | `PERSON-DATA-STEWARD` |
| **Systems** | `SYS-S4HANA`, `SYS-LEGACY-CRM`, `SYS-MIGRATION-FILE` |

## Quickstart

```bash
# 1. Validate
modelops validate --repo examples/customer_bp_model

# 2. Build index
modelops build-index --repo examples/customer_bp_model --jsonl

# 3. Profile dataset
modelops profile-dataset \
    examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
    --repo examples/customer_bp_model

# 4. Search
modelops search "customer group" --repo examples/customer_bp_model

# 5. Query
modelops query --repo examples/customer_bp_model --type Attribute

# 6. Trace lineage
modelops trace FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model

# 7. Impact analysis
modelops impact FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model

# 8. Analyze
modelops analyze --repo examples/customer_bp_model

# 9. Export
modelops export-model --repo examples/customer_bp_model --format csv
modelops export-model --repo examples/customer_bp_model --format xlsx
```

## Change Workflow Demo

```bash
# Propose a patch from a note
echo "Update CUSTOMER GROUP mapping for KNVV-KDGRP." > /tmp/note.md
modelops propose-patch --from /tmp/note.md --repo examples/customer_bp_model

# Review proposal impact
modelops proposal impact PP-SCAFFOLD-001 --repo examples/customer_bp_model

# Create a change request
modelops change-request create \
    --id CR-001 \
    --title "Update customer group mapping" \
    --repo examples/customer_bp_model

# Preview who would be notified
modelops notifications preview --change-request CR-001 --repo examples/customer_bp_model
```

## Expected Validation Warnings

This demo validates with **zero errors**, but some methodology warnings remain intentionally to illustrate the validator's coverage:

| Warning class | Why it appears | How to resolve |
|---|---|---|
| `ATTRIBUTE_MISSING_CONTEXT` | Demo Attributes do not declare `entity_context` | Add `entity_context: <CTX-*>` to each Attribute frontmatter |
| `FIELD_ENDPOINT_MISSING_ENRICHMENT` | Demo FieldEndpoints omit enrichment metadata (description, sample values) | Add `enrichment` block to each FieldEndpoint frontmatter |
| `ATTRIBUTE_USAGE_MISSING_TYPE` | Demo AttributeUsages do not declare `usage_type` | Add `usage_type: display` (or `key`, `filter`, etc.) to each Usage frontmatter |
| `LOV_EMPTY` | ValueLists use simple string values instead of structured entries | Restructure `values` as list of `{code, label}` objects |
| `VALUE_MAPPING_EMPTY` | ValueMappings reference a list but omit explicit `mappings` | Add `mappings` array with `{from, to}` entries |

These are **methodology reminders**, not blockers. The model is safe to index and explore.

## Requirements

- Python 3.11+
- Martenweave installed
- No AI provider key required (uses deterministic no-provider scaffold)

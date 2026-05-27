# Supplier / Vendor Model Example

This example demonstrates Martenweave for **SAP supplier/vendor master data**:
LFA1 (central), LFB1 (company code), and LFM1 (purchasing organization) patterns.

## Model Structure

| Category | Objects |
|---|---|
| **Domain** | `DOMAIN-SUPPLIER-VENDOR` |
| **Entities** | `ENTITY-SUPPLIER`, `ENTITY-SUPPLIER-CENTRAL`, `ENTITY-SUPPLIER-COMPANY-CODE`, `ENTITY-SUPPLIER-PURCHASING-ORG` |
| **Contexts** | `CTX-VENDOR-CENTRAL-S4`, `CTX-VENDOR-COMPANY-CODE-S4`, `CTX-VENDOR-PURCHASING-ORG-S4` |
| **Attributes** | `ATTR-VENDOR-NAME`, `ATTR-VENDOR-ACCOUNT-GROUP`, `ATTR-VENDOR-TAX-NUMBER`, `ATTR-VENDOR-RECONCILIATION-ACCT`, `ATTR-VENDOR-PAYMENT-TERMS`, `ATTR-VENDOR-PURCHASING-BLOCK` |
| **Field Endpoints** | `FEP-S4-LFA1-NAME1`, `FEP-S4-LFA1-KTOKK`, `FEP-S4-LFA1-STCD1`, `FEP-S4-LFB1-AKONT`, `FEP-S4-LFB1-ZTERM`, `FEP-S4-LFM1-ZTERM`, `FEP-S4-LFM1-SPERR`, `FEP-LEGACY-VENDOR-ACCOUNT-GROUP` |
| **Mappings** | `MAP-VENDOR-ACCOUNT-GROUP-LFA1-KTOKK` |
| **Datasets** | `DS-VENDOR-EXTRACT` |
| **Value Lists** | `VLIST-VENDOR-ACCOUNT-GROUP` |
| **Migration** | `MIGOBJ-SUPPLIER-VENDOR` |
| **Systems** | `SYS-S4HANA`, `SYS-LEGACY-ERP` |

## Quickstart

```bash
# 1. Validate
modelops validate --repo examples/supplier_vendor_model

# 2. Build index
modelops build-index --repo examples/supplier_vendor_model --jsonl

# 3. Search
modelops search "vendor" --repo examples/supplier_vendor_model

# 4. Query
modelops query --repo examples/supplier_vendor_model --type Attribute

# 5. Trace lineage
modelops trace FEP-S4-LFA1-KTOKK --repo examples/supplier_vendor_model

# 6. Impact analysis
modelops impact FEP-S4-LFA1-KTOKK --repo examples/supplier_vendor_model

# 7. Analyze
modelops analyze --repo examples/supplier_vendor_model

# 8. Export
modelops export-model --repo examples/supplier_vendor_model --format csv
modelops export-model --repo examples/supplier_vendor_model --format xlsx
```

## v0.3 Gap-to-Proposal Workflow

This example includes a synthetic dataset (`data/samples/vendor_extract.csv`) that demonstrates the full gap-to-proposal pipeline:

```bash
# 1. Profile the synthetic dataset
modelops profile-dataset examples/supplier_vendor_model/data/samples/vendor_extract.csv \
  --repo examples/supplier_vendor_model

# 2. Detect gaps (dataset-side + model-side)
modelops gaps examples/supplier_vendor_model/data/samples/vendor_extract.csv \
  --repo examples/supplier_vendor_model --check-model

# 3. Promote gaps to a draft PatchProposal
modelops gaps examples/supplier_vendor_model/data/samples/vendor_extract.csv \
  --repo examples/supplier_vendor_model --promote-to-proposal

# 4. Impact analysis with direction grouping
modelops impact FEP-S4-LFA1-KTOKK --repo examples/supplier_vendor_model --group-by direction

# 5. Query by SAP table
modelops query --repo examples/supplier_vendor_model --sap-table LFA1 --json

# 6. Review the promoted proposal
modelops proposal show PP-GAP-VENDOR-EXTRACT-001 --repo examples/supplier_vendor_model
modelops proposal diff PP-GAP-VENDOR-EXTRACT-001 --repo examples/supplier_vendor_model
```

Run the full end-to-end demo script:

```bash
./scripts/demo_v0_3_gap_to_proposal.sh
```

## Requirements

- Python 3.11+
- Martenweave installed
- No AI provider key required

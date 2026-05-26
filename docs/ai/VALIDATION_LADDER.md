# Validation Ladder

Use the project venv or Python 3.11+. On this workstation, system `python3` is Python 3.9 and is not valid for Martenweave Core.

## Level 0: Structural And Static Checks

```bash
.venv/bin/python scripts/validate_skills.py
.venv/bin/python -m ruff check .
```

## Level 1: Unit And Service Tests

```bash
.venv/bin/python -m pytest -v
```

For focused changes, run the relevant test file first, then the full suite when practical.

## Level 2: CLI Contracts

```bash
.venv/bin/modelops --help
.venv/bin/modelops validate --repo examples/customer_bp_model --json
.venv/bin/modelops health --repo examples/customer_bp_model --json
.venv/bin/modelops analyze --repo examples/customer_bp_model --json
```

## Level 3: Example Repository Validation

```bash
.venv/bin/modelops validate --repo examples/customer_bp_model
.venv/bin/modelops validate --repo examples/simple_product_model
.venv/bin/modelops validate --repo examples/generic_product_model
.venv/bin/modelops validate --repo examples/supplier_vendor_model
```

Warnings are allowed if documented. Errors are blockers.

## Level 4: Generated Index Rebuild

```bash
.venv/bin/modelops build-index --repo examples/customer_bp_model --jsonl
.venv/bin/modelops build-index --repo examples/simple_product_model --jsonl
.venv/bin/modelops build-index --repo examples/supplier_vendor_model --jsonl
```

Generated outputs are disposable. Do not commit generated artifacts unless the task explicitly requires fixtures.

## Level 5: End-To-End Workflow

```bash
.venv/bin/modelops profile-dataset tests/fixtures/customer_sample.csv --repo examples/customer_bp_model --json
.venv/bin/modelops impact FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model
.venv/bin/modelops export-model --repo examples/customer_bp_model --format csv --output /tmp/martenweave-export.csv
```

Use task-specific end-to-end paths when changing CLI or workflow behavior.

### v0.3 Gap-to-Proposal Demo

```bash
.venv/bin/modelops validate --repo examples/supplier_vendor_model
.venv/bin/modelops build-index --repo examples/supplier_vendor_model --jsonl
.venv/bin/modelops profile-dataset examples/supplier_vendor_model/data/samples/vendor_extract.csv --repo examples/supplier_vendor_model
.venv/bin/modelops gaps examples/supplier_vendor_model/data/samples/vendor_extract.csv --repo examples/supplier_vendor_model --check-model --promote-to-proposal
.venv/bin/modelops impact FEP-S4-LFA1-KTOKK --repo examples/supplier_vendor_model --group-by direction
.venv/bin/modelops query --repo examples/supplier_vendor_model --sap-table LFA1 --json
./scripts/demo_v0_3_gap_to_proposal.sh
```

## Level 6: Safety And Privacy

```bash
.venv/bin/modelops config-guard --repo . --json
```

If this fails due to an ignored local `.env`, report it as an environment safety finding and do not print secret values.

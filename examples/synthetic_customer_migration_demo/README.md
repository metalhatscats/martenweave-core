# Synthetic Customer Migration Demo

This repository is a self-contained, fictional migration scenario. It contains
no production records, credentials, customer data, or connections to external
systems. Its only purpose is explaining and testing Martenweave workflows.

## Synthetic systems

| System | Role | Example evidence |
| --- | --- | --- |
| Nimbus CRM | Sales-owned customer source | IDs, names, sales groups |
| Orbit Commerce | Digital-account source | account references and display names |
| Ledger AR | Finance source | receivables account references |
| Atlas Migration Hub | Controlled staging and harmonisation layer | crosswalk, golden name, normalized group |
| SAP S/4HANA | Target system | `KNA1-NAME1`, `KNVV-KDGRP` |

The model carries both field-level `Mapping` objects and `IntegrationFlow` /
`DataFlowStep` objects. This makes it suitable for demonstrating where a field
came from, how it was harmonised, and which target field is affected.

## Synthetic source extracts

`data/synthetic/` contains small, deliberately fictional CSV extracts. Values
such as `NIM-1001`, `ORB-901`, and `DEMO-NORTH` are not masked production data;
they were invented for this demo. The data exercises naming conflicts, source
crosswalks, and customer-group normalization without personal information.

## Run the demo

```bash
martenweave validate --repo examples/synthetic_customer_migration_demo
martenweave build-index --repo examples/synthetic_customer_migration_demo --jsonl
martenweave trace FEP-DEMO-HUB-GOLDEN-NAME --repo examples/synthetic_customer_migration_demo
martenweave impact FEP-DEMO-S4-KNVV-KDGRP --repo examples/synthetic_customer_migration_demo
```

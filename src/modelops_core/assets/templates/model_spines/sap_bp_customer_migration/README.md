# SAP BP Customer Migration Template

Use this template to scaffold a repository for SAP Business Partner to Customer migration.

## Included objects

- `DOMAIN-CUSTOMER-MIGRATION` — migration scope domain
- `MIGOBJ-CUSTOMER` — customer migration object
- `ENTITY-CUSTOMER` — customer business entity
- `CTX-CUSTOMER-CENTRAL`, `CTX-CUSTOMER-SALES-AREA`, `CTX-CUSTOMER-COMPANY-CODE` — SAP contexts
- `ATTR-CUSTOMER-NAME`, `ATTR-CUSTOMER-GROUP` — sample attributes
- `FEP-S4-KNA1-NAME1`, `FEP-S4-KNVV-KDGRP` — SAP field endpoints
- `MAP-CUSTOMER-GROUP` — placeholder value mapping

## Next commands

```bash
modelops validate --repo /path/to/repo
modelops build-index --repo /path/to/repo
modelops health --repo /path/to/repo
modelops impact ATTR-CUSTOMER-GROUP --repo /path/to/repo
```

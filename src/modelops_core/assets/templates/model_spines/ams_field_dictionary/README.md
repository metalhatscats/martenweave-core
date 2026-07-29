# AMS Field Dictionary Template

Use this template to scaffold a repository for cataloguing fields across AMS-managed applications.

## Included objects

- `DOMAIN-AMS-FIELD-DICTIONARY` — field dictionary domain
- `ENTITY-AMS-FIELD` — field business entity
- `ATTR-FIELD-NAME`, `ATTR-FIELD-DESCRIPTION`, `ATTR-FIELD-DATA-TYPE` — field attributes
- `SYSTEM-AMS-CRM` — example source system
- `FEP-AMS-CUSTOMER-ID` — example application field endpoint

## Next commands

```bash
modelops validate --repo /path/to/repo
modelops build-index --repo /path/to/repo
modelops health --repo /path/to/repo
```

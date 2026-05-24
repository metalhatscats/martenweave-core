# Data Catalog Interoperability

## Positioning

Martenweave is **complementary** to data catalogs, not a replacement.

| Martenweave Strengths | Catalog Strengths |
|---|---|
| Proposal-first model change | Enterprise search |
| File-to-model inference | Access control |
| Team review workbooks | Wide platform integration |
| System lineage | Enterprise glossary publishing |
| Agent-safe operations | |

## Import/Export Mapping

| Catalog Concept | Martenweave Concept |
|---|---|
| Dataset / Table | FieldEndpoint + Dataset |
| Column | Attribute + FieldEndpoint |
| Glossary Term | Attribute, BusinessEntity |
| Owner | business_owner, data_steward |
| Classification | ValidationRule |
| Lineage | object_relationships |
| Quality Rule | ValidationRule |
| Tag | status, domain |

## Future Formats

- OpenMetadata JSON export
- DataHub MCE export
- Collibra-style Excel export
- Alation API mapping
- CSV/JSON interchange

## Proposal-First Interop

All imports/exports are mediated through PatchProposal or report generation, not silent mutation.

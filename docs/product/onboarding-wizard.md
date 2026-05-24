# Onboarding Wizard Design

A guided flow for new users to create their first Martenweave model from a file without learning the full methodology upfront.

## Flow

1. **Choose mode**
   - Simple table → quick entity/attribute model
   - Enterprise object → full domain modeling

2. **Select source file**
   - CSV, XLSX, or JSONL
   - File is profiled (columns, types, sample values)

3. **Review inferred objects**
   - Domain (table name or user-provided)
   - Attributes (one per column)
   - FieldEndpoints (physical columns)
   - Mappings (attribute ↔ field)

4. **Add governance metadata**
   - Business owner
   - Data steward
   - Purpose / description

5. **Validate**
   - Run Layer 1–3 validation
   - Show gaps (missing owners, unmapped fields, etc.)

6. **Export review workbook**
   - XLSX or Markdown summary
   - For stakeholder review

7. **Create first proposal**
   - Generate PatchProposal from inferred objects
   - User reviews before apply

## CLI Version

```bash
modelops wizard --repo ./my-model --file ./data/customers.csv
```

## Principles

- Proposal-first: AI or inference never applies directly.
- Validation-first: Invalid objects are flagged before indexing.
- Progressive disclosure: Advanced concepts hidden until needed.

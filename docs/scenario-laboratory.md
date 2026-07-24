# Scenario Laboratory

The scenario laboratory is a reusable, evidence-first acceptance layer for SAP migration and MDM
consulting. It deliberately exercises the real pilot path: preflight, interpretation, assessment,
findings, gaps/impact, a reviewable proposal, Excel review, returned-review validation, and explicit
approval. Inputs are never silently promoted to canonical files.

| Scenario | CLI path | Local API / Workbench path | Fixture and regression evidence |
|---|---|---|---|
| Clean single-sheet SAP mapping | `run migration-assessment` | Import → inspect → preview | `tests/fixtures/pilot/sap_customer_mapping.xlsx`; assessment tests |
| BP, Customer, Supplier multi-sheet mapping | `pilot-preflight`, `run migration-assessment` | Import interpretation lists every sheet | `tests/test_scenario_laboratory.py` |
| Renamed headers, blanks, merged cells | `pilot-preflight` | Import warnings and assumptions | scenario-lab workbook test |
| Duplicate mappings/rows and conflicting IDs | `import-excel-review`, `proposal validate` | Preview then review error state | `test_api_v1_imports.py`, model-sheet import tests |
| Missing fields, owners, rules, decisions | `validate`, `assessment`, `gap-report` | Findings and proposal views | validation, assessment, and readiness tests |
| Formulas, hidden sheets, comments, external links | `pilot-preflight` | Inspect endpoint, imported evidence only | scenario-lab test |
| Conditional mandatory fields/value mappings | `validate`, `assessment` | Findings review | SAP validation and assessment tests |
| Obsolete/out-of-scope records | `assessment`, `gap-report` | Findings review | assessment fixture suite |
| CSV/XLSX extracts that differ from model | `run dataset-readiness` | Dataset import profile | dataset-readiness and API import tests |
| Validation reports/Markdown evidence | `evidence ingest`, `proposal validate` | Evidence-led proposal review | evidence-ingestion tests |
| Accepted, rejected, commented Excel review | `export-model`, `import-excel-review`, `proposal review` | Validate → propose → explicit proposal review | exchange and API import tests |
| Corrupt, unsupported, protected, oversized, unsafe files | `pilot-preflight` | Inspect blocks safely with actionable reason | scenario-lab and guardrail tests |
| Repeated imports | `evidence ingest --json` | Repeated inspect/profile remains evidence-only | deterministic-ID evidence tests |

The matrix is intentionally a map to testable product behavior, not a promise to parse every
possible spreadsheet layout. A blocked preflight is a successful safe outcome when the source is
corrupt, unsupported, encrypted, too large, or unsafe.

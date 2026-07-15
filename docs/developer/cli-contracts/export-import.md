# CLI Contract — Export and Import

## Commands

```bash
modelops export-model --repo <repo> --format csv|xlsx
modelops export-model --repo <repo> --format xlsx --out <workbook.xlsx> --business-review
modelops export-schema --repo <repo> --type <ObjectType|all> --output <path>
modelops import-model-sheet <path> --repo <repo> --json
modelops import-excel-review --repo <repo> --from <workbook.xlsx> --out <proposal.md>
modelops proposal validate --repo <repo> --proposal <proposal.md>
```

## JSON Contracts

### `export-model`

Human output: "Exported" and format name (CSV or XLSX).
JSON output is not primary for this command.

### `import-model-sheet --json`

Stable fields: `id`, `type`, `status`, `operations`, `warnings`

### `import-excel-review`

Writes a portable PatchProposal Markdown artifact and never changes canonical model files. Every
non-empty review row must include a stable `id`; missing IDs are rejected with the worksheet and
row location.

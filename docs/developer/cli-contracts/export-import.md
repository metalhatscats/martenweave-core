# CLI Contract — Export and Import

## Commands

```bash
modelops export-model --repo <repo> --format csv|xlsx --output <path>
modelops import-model-sheet <path> --repo <repo> --json
```

## JSON Contracts

### `export-model`

Human output: "Exported" and format name (CSV or XLSX).
JSON output is not primary for this command.

### `import-model-sheet --json`

Stable fields: `id`, `type`, `status`, `operations`, `warnings`

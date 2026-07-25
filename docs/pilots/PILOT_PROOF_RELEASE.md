# Pilot Proof workflow

This is the supported local workflow for an SAP mapping pilot. It creates disposable evidence only;
canonical `model/` files change only after human review and approval of a PatchProposal.

```bash
martenweave pilot-preflight --mapping ./mapping.xlsx --out ./pilot/preflight
martenweave bootstrap-assessment --mapping ./mapping.xlsx --name "Client pilot" --out-repo ./pilot/model
martenweave run migration-assessment --repo ./pilot/model --mapping ./mapping.xlsx --out ./pilot/assessment
martenweave assessment compare-workbooks ./mapping-v1.xlsx ./mapping-v2.xlsx --repo ./pilot/model --out ./pilot/comparison
```

The assessment package contains `findings.json`, a business-review workbook, review pack, evidence
manifest, Workbench workspace descriptor, and executive HTML/Markdown/JSON report. Review findings
with `martenweave assessment-review set`; only `assessment-review promote` creates a proposal for a
human to approve.

Known boundary: colour-only workbook statuses are reported as evidence but never interpreted as a
business decision. Hidden sheets are retained in the structural manifest and excluded from initial
interpretation.

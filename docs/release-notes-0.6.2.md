# Martenweave Core 0.6.2

Released 2026-07-24.

This patch makes the workbook/evidence handoff safer to use in a real SAP migration assessment.
Before the Workbench profiles a dataset or previews an Excel model import, it now requests a
metadata-only interpretation from the local API. Consultants can see detected sheets and columns,
hidden-sheet exclusions, formulas, comments, merged ranges, external links, warnings, and explicit
assumptions. None of these inputs become canonical model content without the existing proposal,
review, and approval path.

The package metadata now identifies Dzmitryi Kharlanau as author and maintainer and preserves links
to the project homepage, documentation, repository, issues, and changelog. Citation metadata is
provided in `CITATION.cff`.

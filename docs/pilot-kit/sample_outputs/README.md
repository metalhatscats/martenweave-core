# Sample Outputs

> This directory documents the outputs produced by a Migration Model Readiness Assessment.
> All sample data is synthetic.

## Assessment Package Structure

Running:

```bash
modelops assessment run --repo examples/customer_bp_model --out ./assessment
```

Produces:

```
assessment/
  01_readiness_scorecard.md
  02_gap_report.md
  03_high_risk_fields.md
  04_impact_reports/
  05_business_review.xlsx
  06_recommendations.md
```

## File Descriptions

### 01_readiness_scorecard.md

A one-page governance summary showing:
- **Readiness level**: seed, draft, review, or ready
- **Metrics table**: completeness, ownership, validation, mapping, dataset coverage
- **Actionable gaps**: specific items to fix
- **Summary**: narrative interpretation

Share this with leadership as a quick health check.

### 02_gap_report.md

A consolidated gap view combining:
- Validation errors and warnings
- Health coverage gaps (missing names, descriptions, owners)
- Analysis gaps (orphan fields, missing mappings)
- Scorecard gaps

The **gap score** = gaps / total objects. Track this over time.

### 03_high_risk_fields.md

A ranked risk register with:
- Object ID, type, name
- Severity: high, medium, low
- Risk reasons: validation errors, missing owner, open issue, orphan field, etc.

Use this to prioritize daily stand-up or workshop topics.

### 04_impact_reports/

One Markdown file per top high-risk object.
Each report shows:
- Root object metadata
- Downstream and upstream affected objects
- Relationship types and depth

Review these **before** making changes to avoid surprises.

### 05_business_review.xlsx

A styled Excel workbook with:
- One sheet per object type
- Blue header row, alternating row colors
- Frozen panes and auto-filters
- `reviewer_notes` column for free-text comments
- Status dropdown data validation

Business stakeholders can review and comment without touching Git or Markdown.

### 06_recommendations.md

Structured next steps grouped by theme:
- Governance & Ownership
- Data Quality & Validation
- Mapping & Transformation
- Risk & Issues

Includes an executive summary and a numbered next-steps list.

## How to Share with Stakeholders

| Stakeholder | Files to share |
|---|---|
| Executive sponsor | Scorecard + Recommendations |
| Data architect | Gap Report + Impact Reports |
| Functional lead | Business Review XLSX + High Risk Fields |
| Migration lead | Full package as ZIP or Git commit |
| Auditor | Git commit hash + generated artifacts |

## Tracking Progress

Re-run the assessment after each sprint:

```bash
modelops assessment run --repo . --out assessment/v2
```

Compare gap scores and readiness levels across versions.

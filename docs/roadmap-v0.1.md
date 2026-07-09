<!-- modelops-freshness-ignore: all -->

# Martenweave v0.1 MVP Roadmap

> A concise, agent-readable delivery plan. The goal is to ship a useful core first, then expand.

---

## What v0.1 means

v0.1 is the **first self-contained release** of martenweave-core that a data team can use to:

1. Scaffold a model repository.
2. Profile datasets (CSV / Excel).
3. Infer draft model objects from profiles.
4. Edit canonical model files (Markdown + YAML frontmatter).
5. Validate models deterministically.
6. Build a queryable SQLite index.
7. Search, query, trace, and impact-analyze objects.
8. Propose, review, and apply model changes safely (PatchProposal → ChangeRequest).
9. Export to Excel/CSV for review and re-import as proposals.
10. Run health and analysis reports.

---

## Already delivered (core is solid)

These issues are **closed and merged**. They form the v0.1 foundation.

| # | Feature | Validation |
|---|---|---|
| #1 | Define Martenweave as agentic data model registry | `modelops --help` |
| #2 | Canonical model contract docs | `modelops validate` |
| #3 | Dataset profiling (CSV / Excel) | `modelops profile-dataset` |
| #4 | Infer draft objects from profiles | `modelops infer-model` |
| #5 | Proposal review and apply workflow | `modelops proposal list/dry-run/apply` |
| #8 | Export to Excel / CSV | `modelops export-model` |
| #9 | Import spreadsheet as PatchProposal | `modelops import-model-sheet` |
| #10 | Local API | `modelops serve` |
| #12 | Domain packs (SAP + generic) | `modelops validate --repo examples/customer_bp_model` |
| #13 | Traceability graph | `modelops trace <id>` |
| #14 | Field / attribute ownership | validation layer 2 |
| #15 | Value list governance | validation layer 2 |
| #16 | Audit log | `modelops audit-log` |
| #17 | Impact analysis | `modelops impact <id>` |
| #18 | Data quality coverage analysis | `modelops analyze` |
| #20 | Analysis reports | `modelops health` / `modelops analyze` |
| #23 | Simple table modeling mode | `examples/simple_product_model` |
| #24 | Relationship taxonomy | `modelops trace` |
| #25 | Model spine templates | `templates/model_spines/` |
| #29 | ChangeRequest CLI | `modelops change-request` |
| #30 | Watchers and notifications | `modelops notifications` |
| #31 | Notification event log | `modelops notifications` |
| #32 | Approval gates for high-risk changes | risk assessment in proposals |
| #33 | GitHub issue draft integration | `modelops issue-draft` |
| #38 | Secrets and environment guardrails | `.env` + config guard |
| #39 | Schema versioning and migration | `modelops validate` schema checks |
| #40 | Model diff command | `modelops diff` |
| #41 | Query and search commands | `modelops query` / `modelops search` |
| #43 | End-to-end demo examples | `examples/` |
| #44 | Privacy and sanitization rules | `modelops profile-dataset` |
| #45 | Performance limits | `tests/test_resource_limits.py` |
| #47 | Hardened Excel import | `modelops import-model-sheet` |
| #48 | Excel business-review roundtrip | `modelops export-model --business-review` |
| #52 | GitHub-ready change bundles | `modelops git-bundle` |
| #54 | Source registry | `modelops sources` |
| #55 | Connector adapter interface | `LocalFileConnector` |
| #59 | Static documentation site | `modelops docs-build` |
| #60 | CLI contract tests | `tests/test_cli_contracts.py` |
| #61 | Release packaging | `pyproject.toml` + `dist/` |
| #62 | Acceptance demo script | `scripts/demo_v0_1.sh` |
| #70 | Governance scorecard | `modelops scorecard` |
| #89 | Usage/cost reporting | `modelops usage-report` |
| #90 | Metadata taxonomy | `docs/model-metadata-taxonomy.md` |
| #91 | Field usage/scope metadata | `AttributeUsage.usage_type` |
| #92 | Lifecycle/roadmap metadata | `GeneralStatus` expansion |
| #94 | Runtime memory budgets | resource limits config |
| #95 | Stream large file profiling | chunked profiling |
| #98 | Memory regression tests | `tests/test_resource_regression.py` |

---

## v0.1 remaining work (finish before calling v0.1)

These are the **last pieces** needed to call v0.1 complete.

| # | Issue | Why it blocks v0.1 | Validation |
|---|---|---|---|
| #42 | CI workflow | Every release needs automated tests | `.github/workflows/ci.yml` runs on push/PR |
| #53 | **This roadmap** | v0.1 needs a declared boundary | `docs/roadmap-v0.1.md` exists and is reviewed |

**#42 is blocked** until the GitHub PAT gains `workflow` scope. If that takes time, v0.1 can ship with manual validation and CI added immediately after.

---

## v0.2 next slice (after v0.1)

These issues add **significant new capabilities** without changing the core model contract.

| # | Issue | Value | Validation |
|---|---|---|---|
| #46 | Integration architecture doc | Clarifies how files/sheets/drives/Git fit together | `docs/integration-architecture.md` |
| #49 | Google Drive/Sheets boundary design | Prepares cloud connector work | design doc |
| #50 | Google Sheets export adapter | Business review via Google Sheets | `modelops export-model --connector google_sheets` (mocked) |
| #56 | Google Drive import adapter | Import from Drive folders | mocked connector test |
| #57 | Google Sheets import adapter | Import edited sheets as proposals | mocked connector test |
| #58 | GitHub write integration | Auto-create issues/PRs from bundles | mocked test |
| #63 | Database metadata import design | Connect to real databases | design doc |
| #64 | JSON Schema / OpenAPI import design | Import from API specs | design doc |
| #65 | System lineage model | Cross-system data flow tracking | `modelops analyze` shows lineage |
| #71 | Portable model package archive | Zip-based model distribution | `modelops package create/extract` |
| #72 | Source refresh / stale detection | Warn when sources changed | `modelops sources --stale` |
| #73 | Conflict detection for concurrent changes | Merge safety | `modelops validate` conflict checks |
| #74 | Bulk refactor operations | Rename/move objects safely | `modelops refactor` |

---

## Out of scope for v0.1 and v0.2

These are **intentionally deferred**. They are valid ideas but would expand scope indefinitely.

| # | Issue | Deferred because | When to revisit |
|---|---|---|---|
| #5–7, #34–37 | Workspace / UI / chat / ADK | UI is explicitly out of scope for core | After v0.2 API is stable |
| #49–51, #56–58 | Cloud integrations (Drive, Sheets, GitHub) | Needs connector boundary + credentials story | v0.2 |
| #63, #64, #68 | Database / dbt / OpenAPI imports | Requires connector adapters + schema mapping | v0.2+ |
| #66, #75, #76 | Graph visualization / Neo4j | Visualization is not core; graph DB is optional | Post-v0.2 |
| #67 | OpenLineage export | Standard export format; nice to have | Post-v0.2 |
| #69, #77–79 | MCP server | Agent integration layer; core must be solid first | Post-v0.2 |
| #80–82 | AI usage telemetry | Cost tracking; not needed for MVP | Post-v0.2 |
| #83–88, #93 | Product/commercial docs | Business planning; not engineering blockers | Continuous |
| #96 | Cache lifecycle / cleanup | Generated artifacts are already disposable | When storage becomes a problem |
| #100–102 | AI evaluation / diagnostics / backup | Advanced operational features | Post-v0.2 |
| #103–121 | Architecture/design docs | Good ideas, but core implementation comes first | As needed per feature |

---

## Agent implementation order

If you are an AI agent picking up issues, use this order:

1. **#42** CI workflow (if PAT `workflow` scope is available).
2. **#46** Integration architecture doc (clarifies boundaries before cloud work).
3. **#49** Google Drive/Sheets boundary design (design before implementation).
4. **#71** Portable model package archive (useful for distribution).
5. **#72** Source refresh / stale detection (builds on source registry).
6. **#50** Google Sheets export adapter (mocked, using connector protocol).
7. **#56** Google Drive import adapter (mocked, using connector protocol).
8. **#65** System lineage model (extends existing lineage).
9. **#74** Bulk refactor operations (model cleanup utility).
10. **#73** Conflict detection (safety layer for concurrent edits).

Skip any issue labeled `type:future-integration` until all `type:architecture` and `type:product` issues above it are done.

---

## How to validate v0.1 readiness

Run these commands in order. All must pass.

```bash
# 1. Tests and lint
pytest tests -v
ruff check .

# 2. Example validation
modelops validate --repo examples/simple_product_model
modelops validate --repo examples/customer_bp_model
modelops validate --repo examples/generic_product_model

# 3. Index build
modelops build-index --repo examples/customer_bp_model --jsonl

# 4. Core workflows
modelops profile-dataset tests/fixtures/customer_sample.csv --repo examples/customer_bp_model
modelops export-model --repo examples/customer_bp_model --format xlsx --business-review
modelops health --repo examples/customer_bp_model --json
modelops analyze --repo examples/customer_bp_model --json

# 5. Documentation
ls docs/roadmap-v0.1.md
```

---

## Done definition for v0.1

v0.1 is **done** when:

- [x] All core model operations work (init, validate, build-index, query, trace, impact).
- [x] Dataset profiling and model inference work end-to-end.
- [x] PatchProposal and ChangeRequest workflows are complete with approval gates.
- [x] Export/import roundtrip works (CSV, XLSX, business-review XLSX).
- [x] Health, analysis, scorecard, and audit reports work.
- [x] Static documentation generation works.
- [x] Git-ready change bundles work.
- [x] Source registry and connector adapter boundary exist.
- [ ] CI workflow runs on every push/PR (blocked by PAT scope).
- [x] This roadmap document is merged.

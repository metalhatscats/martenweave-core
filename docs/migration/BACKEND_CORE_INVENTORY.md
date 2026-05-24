# Backend Core Inventory

This document inventories the original ModelOps for MDM monorepo and classifies every significant file for the backend-first fork.

## KEEP (migrate directly)

| Path | Purpose | Target Path |
|------|---------|-------------|
| `apps/api/src/modelops/schemas/base.py` | Base Pydantic schemas | `src/modelops_core/schemas/common.py` |
| `apps/api/src/modelops/schemas/objects.py` | Domain schemas | `src/modelops_core/schemas/domain.py` |
| `apps/api/src/modelops/schemas/patch_support.py` | Patch enums | `src/modelops_core/schemas/patch_proposal.py` |
| `apps/api/src/modelops/validation/result.py` | Validation result models | `src/modelops_core/validation/result.py` |
| `apps/api/src/modelops/validation/pipeline.py` | Validation pipeline | `src/modelops_core/validation/pipeline.py` |
| `apps/api/src/modelops/registry.py` | Object type registry | `src/modelops_core/schemas/registry.py` |
| `apps/api/src/modelops/repository/parser.py` | Frontmatter parser | `src/modelops_core/repository/parser.py` |
| `apps/api/src/modelops/repository/scanner.py` | File scanner | `src/modelops_core/repository/scanner.py` |
| `apps/api/src/modelops/index/builder.py` | SQLite builder | `src/modelops_core/index/sqlite_builder.py` |
| `apps/api/src/modelops/index/queries.py` | SQLite queries | `src/modelops_core/index/queries.py` |
| `apps/api/src/modelops/impact/service.py` | Impact BFS | `src/modelops_core/impact/impact_service.py` |
| `apps/api/src/modelops/lineage/service.py` | Lineage path | `src/modelops_core/lineage/lineage_service.py` |
| `apps/api/src/modelops/patches/validator.py` | Patch validator | `src/modelops_core/patching/patch_validator.py` |
| `apps/api/src/modelops/patches/apply.py` | Patch apply | `src/modelops_core/patching/apply_service.py` |
| `apps/api/src/modelops/patches/service.py` | Patch proposal service | `src/modelops_core/patching/patch_proposal_service.py` |
| `apps/api/src/modelops/changes/validator.py` | CR validator | `src/modelops_core/patching/change_request_validator.py` |
| `apps/api/src/modelops/changes/service.py` | CR service | `src/modelops_core/patching/change_request_service.py` |
| `apps/api/src/modelops/ai/adapter.py` | AI adapter protocol | `src/modelops_core/ai/provider_adapter.py` |
| `apps/api/src/modelops/ai/service.py` | AI patch service | `src/modelops_core/ai/patch_proposal_service.py` |
| `apps/api/src/modelops/datasets/profiler.py` | CSV profiler | `src/modelops_core/imports/dataset_profiler.py` |
| `apps/api/src/modelops/datasets/gap.py` | Gap detection | `src/modelops_core/gaps/gap_detection.py` |
| `apps/api/src/modelops/datasets/import_session.py` | Import session | `src/modelops_core/imports/import_session.py` |
| `apps/api/src/modelops/privacy.py` | Privacy redaction | `src/modelops_core/imports/privacy.py` |
| `apps/api/src/modelops/audit/service.py` | Audit events | `src/modelops_core/reports/audit_service.py` |
| `apps/api/src/modelops/health/service.py` | Health report | `src/modelops_core/reports/health_report.py` |
| `apps/api/src/modelops/catalog/service.py` | Catalog queries | `src/modelops_core/reports/catalog_service.py` |
| `apps/api/src/modelops/search/service.py` | Search service | `src/modelops_core/index/search_service.py` |
| `examples/customer-bp/model/` | Sample model files | `examples/customer_bp_model/model/` |

## KEEP WITH REFACTOR

| Path | Reason | Target |
|------|--------|--------|
| `apps/api/src/modelops/main.py` | FastAPI app factory — remove HTTP layer | `src/modelops_core/cli.py` |
| `apps/api/src/modelops/routers/*.py` | FastAPI routers — extract to CLI | Drop routers; use CLI commands |
| `apps/api/src/modelops/errors.py` | API error envelope — remove FastAPI handlers | `src/modelops_core/errors.py` |
| `apps/api/src/modelops/core/logging.py` | Remove request-id filter | `src/modelops_core/logging.py` |
| `apps/api/src/modelops/config.py` | Simplify to CLI settings | `src/modelops_core/config.py` |
| `apps/api/tests/*.py` | Refactor away from TestClient | `tests/` |
| `pyproject.toml` | Strip FastAPI/uvicorn | `pyproject.toml` |

## DROP

| Path | Reason |
|------|--------|
| `apps/web/` | Next.js frontend |
| `apps/web/e2e/` | Playwright E2E tests |
| `apps/web/tests/` | Vitest + React Testing Library |
| `design/` | UI mockup prototypes |
| `output/` | Screenshot assets |
| `apps/api/src/modelops/routers/` | FastAPI HTTP layer |
| `apps/api/src/modelops/core/middleware.py` | HTTP middleware |
| `scripts/generate-openapi-json.py` | FastAPI-specific |
| `scripts/check-api-drift.sh` | Frontend/backend drift check |
| `package.json` (root) | Node monorepo config |
| `pnpm-workspace.yaml` | Workspace includes web |
| `node_modules/` | Frontend dependencies |
| `generated/*.db` | Disposable artifacts |

## REWRITE

| Path | Current | Target |
|------|---------|--------|
| `apps/api/src/modelops/cli/__init__.py` | Empty placeholder | Full Typer CLI |
| `apps/api/src/modelops/index/builder.py` | No JSONL export | Add `search_documents.jsonl` and `lineage_edges.jsonl` |

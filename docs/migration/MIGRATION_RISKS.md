# Migration Risks

## Risk 1: UI/backend coupling in router layer
**Severity:** Low. FastAPI routers are thin adapters. Extracting service calls into CLI commands is straightforward.

## Risk 2: Schema drift between backend and frontend
**Severity:** Low (eliminated by dropping the frontend).

## Risk 3: Hidden runtime dependencies on FastAPI
**Severity:** Medium. Some modules may import `HTTPException` or Pydantic `Field` patterns tied to API contexts. Mitigation: audit all imports during rewrite.

## Risk 4: Missing tests for CLI flows
**Severity:** Medium. The original CLI is a placeholder. New `typer.testing.CliRunner` tests must be added.

## Risk 5: Unclear source of truth for generated vs canonical
**Severity:** Low. Mitigation: `.gitignore` rules for `generated/`, `*.db`, `*.jsonl`, and explicit documentation.

## Risk 6: Generated artifacts mixed with canonical files
**Severity:** Low. Exclude `generated/` directories during example copy.

## Risk 7: Old product assumptions (SaaS, web UI)
**Severity:** Medium. Some docs refer to "workspace UI" and "SaaS". Update README and key docs to reflect CLI-first direction.

## Risk 8: Dependency bloat from monorepo
**Severity:** Low. Remove all Node/pnpm artifacts. Pure Python repo.

## Risk 9: Loss of demo end-to-end coverage
**Severity:** Medium. Replace UI E2E with CLI E2E test covering `init → validate → build-index → health → impact → propose-patch`.

## Risk 10: AI patch workflow gaps without UI
**Severity:** Low. `render_patch_review_evidence()` exists. Enhance for terminal Markdown diff output.

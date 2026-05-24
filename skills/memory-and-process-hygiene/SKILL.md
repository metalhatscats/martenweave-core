# Skill: Memory and Process Hygiene — Martenweave

## When to use
Before, during, and after any coding session to prevent source-of-truth drift, accidental mutations, context pollution, and resource leaks.

## Inputs
- Your current working branch
- List of files you have touched

## Read first
1. `AGENTS.md` — Core Principles section (canonical files are source of truth, generated index is disposable, AI must not silently mutate).
2. `src/modelops_core/patching/apply_service.py` — blocked path segments and atomic apply logic.
3. `src/modelops_core/paths.py` — `resolve_allowed_path` for safe path traversal.

## Do not do
- Do not silently edit canonical files (`model/*.md`) without producing a `PatchProposal` or `ChangeRequest` when the change is AI-initiated.
- Do not commit files from `generated/`, `.venv/`, or `data/samples/` unless they are explicitly part of the task.
- Do not hardcode absolute paths; use repo-relative paths or `RepoConfig` resolution.
- Do not assume `generated/` is the source of truth; it is rebuilt by `modelops build-index`.
- Do not leave dev servers, test runners, file watchers, or background processes running unless the task explicitly requires them.

## Procedure
1. **Start clean**: Confirm you are on a feature branch, not `main`.
2. **Scope boundary**: List the files you intend to change before changing them.
3. **Source-only edits**: If you need to change model knowledge, edit files under `model/` only.
4. **Rebuild index**: After model edits, run `modelops build-index --repo <path>` to refresh `generated/`.
5. **Validate**: Run `modelops validate --repo <path>` after any canonical file change.
6. **Discard generated artifacts** before committing unless the task explicitly requires updating them:
   ```bash
   git checkout -- generated/   # or remove and rebuild in CI
   ```
7. **Atomic commits**: Keep canonical file changes separate from generated index rebuilds.
8. **Process check after each issue**: List running Python and Node processes to detect orphans:
   ```bash
   ps aux | grep -E 'python|node' | grep -v grep
   ```
9. **Memory usage check**: Verify memory is within reasonable bounds before and after heavy operations:
   ```bash
   ps aux -m | head -20
   ```
10. **Cleanup**: Terminate any dev servers, watchers, or test runners started during the session unless explicitly told to keep them running.
11. **Cleanup report**: Before ending the session, report what processes were checked, what was terminated, and current memory state.

## Validation
- `git status` shows only intentional changes in `src/`, `tests/`, `model/`, or `docs/`.
- No accidental modifications in `generated/`, `data/`, `.env`, or `pyproject.toml` unless planned.
- `pytest` and `ruff check .` still pass.
- No orphaned Python or Node processes remain from this session (unless explicitly required).
- Cleanup report is produced.

## Output format
Return:
- Branch name
- Files intentionally modified (list)
- Files discarded or left untouched (list)
- Validation result (pass/fail)
- Process cleanup report (processes checked, terminated, remaining)
- Memory state summary

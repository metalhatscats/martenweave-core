# AI Development Docs

This directory defines how AI coding agents work in Martenweave Core.

Start here:

0. `../factory/README.md` for the Development AI Factory (agents, skills, gates,
   autonomy, project memory) — the current operating layer for autonomous work.
1. `AI_DEVELOPMENT_OPERATING_SYSTEM.md` for the overall repo operating model.
2. `AGENT_CONTEXT_LOADING.md` for what to read before changing files.
3. `VALIDATION_LADDER.md` for exact commands.
4. `KIMI_GITHUB_ISSUE_LOOP.md` for issue-by-issue implementation.
5. `ONE_ISSUE_AGENT_PROMPT.md` for a copyable prompt template to execute one issue safely.
6. `AGENT_SAFETY_RULES.md` before touching canonical model files, generated files, data, or credentials.

Agent roles:

- Kimi is the primary long-loop implementation agent for GitHub issues.
- Codex is used for architecture audit, planning, validation hardening, refactoring, and repository preparation.
- Skills and docs are tool-neutral. They must be executable by either agent.

Lower-level AI runtime references remain in this directory under `ai-*.md`.

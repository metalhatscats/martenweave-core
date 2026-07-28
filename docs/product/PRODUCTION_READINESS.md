# Production-readiness and v1.0 exit criteria

Martenweave 0.x is usable for a controlled local pilot, not a supported GA product. A maintainer
may change the version or Alpha classifier only after recording a go/no-go decision with evidence
for every criterion below. This document creates no SLA, certification, or hosted-product promise.

| Gate | Required evidence |
| --- | --- |
| Packaging and install | Built-wheel install from an empty directory, `bash scripts/release_smoke.sh`, and the Windows wheel smoke in CI. |
| Supported platforms | Python 3.11 on supported Windows and POSIX CI; any later matrix expansion is a maintainer decision. |
| Core correctness | `python -m pytest -q`, `ruff check .`, `ruff format --check src tests`, bundled-example validation, and `bash scripts/demo_northstar_pilot.sh`. |
| Canonical-data safety and recovery | PatchProposal → approval → ChangeRequest tests, documented Git/filesystem backup and recovery exercise, and no unreviewed canonical mutation. |
| Schema/API/CLI compatibility | Documented schema migration and deprecation notice for one minor release; API/MCP contract tests and CLI command freshness validation. |
| Security and provenance | `pytest tests/test_secret_guardrails.py -q`, dependency/release provenance review, supported-version/security disclosure process in `SECURITY.md`. |
| Documentation and support | `python scripts/validate_doc_commands.py`, `python scripts/validate_skills.py`, current support boundaries, and an owner for incoming reports. |
| Workbench boundary | Local-only Workbench/API smoke; no hosted, RBAC, SaaS, SAP write-back, enterprise workflow, or certification claim. |
| External proof | At least one consenting design-partner pilot (#599), reviewer outcomes, a recorded continue/pivot/stop decision, and written consent before any public name, quote, logo, or screenshot. |

Current and prior 0.x minors are governed by the policy in `SECURITY.md`: only the current minor
receives fixes; older minors require upgrade guidance. Breaking repository/schema migrations need a
documented migration path before the next minor release.

Open prerequisites include installed-wheel assets (#595), Windows verification (#597), current
security/procurement guidance (#596), live search indexing (#601), and external pilot evidence
(#599). The maintainer, not automation, owns the final GA decision.

# Martenweave Commercial Due Diligence — Execution Plan

**Date:** 2026-06-09
**Goal:** Evaluate Martenweave as a commercial product idea, not a hobby project.
**Output:** COMMERCIAL_DUE_DILIGENCE_MARTENWEAVE.md + COMMERCIAL_DUE_DILIGENCE_AGENT_NOTES.md

---

## Stage 0 — Repository Inspection (COMPLETED)

- Agent 5 (Technical) audited `metalhatscats/martenweave-core`
- Agent 5 (Website) audited `Martenweave/martenweave.github.io`
- Outputs: `AGENT_5_TECHNICAL_AUDIT.md`, `AGENT_5_WEBSITE_AUDIT.md`

Key facts established:
- Version 0.4.0, Python backend, CLI-only (no UI)
- ~1,200 tests, ~88% coverage
- 4 working SAP example models
- 60 CLI commands in 5,343-line monolith
- AI patch flow: proposal→review→apply, safe by design but soft edges
- Gap detection, impact analysis, validation (Layer 1–3) all implemented
- Website: polished, zero web presence, core repo 404 on public fetch
- Zero search/social mentions anywhere

---

## Stage 1 — Parallel Analysis (CURRENT)

Deploy 5 agents simultaneously with audit findings as context:

### Agent 1 — Product/Market Analyst
- Evaluate business problem, pain urgency, budget ownership
- ICP analysis for SAP migration, MDM, governance, AMS teams
- Output: `AGENT_1_PRODUCT_MARKET.md`

### Agent 2 — SAP/MDM Domain Buyer Analyst
- Evaluate from buyer/user perspective
- Concrete SAP pain points, wedge use cases
- Output: `AGENT_2_SAP_BUYER.md`

### Agent 3 — Competitive/Alternative Analyst
- Web research on Collibra, Informatica, Ataccama, SAP MDG, Signavio, LeanIX, dbt, DataHub, etc.
- Category placement, differentiation, what NOT to compete with
- Output: `AGENT_3_COMPETITIVE.md`

### Agent 4 — GTM/Pricing Analyst
- Commercial paths: time-limited evaluation, no-cost pilots by agreement, team/project licenses,
  audit packages, domain packs, and enterprise deployment
- Price hypotheses, sales motions, time to first revenue
- Output: `AGENT_4_GTM_PRICING.md`

### Agent 6 — Red Team Skeptic
- Attack the commercial idea from all angles
- Evidence-based criticism with severity and mitigation
- Output: `AGENT_6_RED_TEAM.md`

---

## Stage 2 — Synthesis (NEXT)

### Agent 7 — Synthesis Lead
- Read all 5 agent outputs + 2 audit reports
- Merge into final report following the 13-section structure
- Output: `COMMERCIAL_DUE_DILIGENCE_MARTENWEAVE.md`
- Also produce: `COMMERCIAL_DUE_DILIGENCE_AGENT_NOTES.md`

---

## Stage 3 — Assembly (FINAL)

- Orchestrator reviews final report
- Ensures all 13 sections are present and complete
- Saves final files to workspace

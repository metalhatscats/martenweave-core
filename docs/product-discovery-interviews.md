# Product Discovery Interview Guide

> Use this guide in 30–45 minute conversations with target teams.  
> Goal: validate pain, understand current behaviour, and identify whether Martenweave is a fit.  
> Do not pitch. Listen.

---

## Pre-Interview Setup

1. **Recruit the right role** — aim for people who *do* the work, not only people who *buy*.
2. **Set context** — "We are building a tool for data-model documentation and change tracking.  We want to understand how you work today so we do not build the wrong thing."
3. **Record notes** — write verbatim quotes where possible; they are more valuable than scores.

---

## Interview Tracks

### Track A — Data Migration Team

| # | Question | What to listen for |
|---|---|---|
| 1 | Walk me through the last migration project you worked on. | Scope, team size, duration, tools used |
| 2 | How do you document source-to-target mappings today? | Excel, Confluence, custom DB, nothing |
| 3 | Who validates that a mapping is correct before go-live? | Named person, process, or gap |
| 4 | How do you trace a business concept (e.g., "Customer Group") back to its source field? | Manual search, tribal knowledge, no way |
| 5 | Have you ever discovered a mapping error after cutover? | Frequency, impact, detection method |
| 6 | How do you onboard a new team member to the migration model? | Time, materials, frustration |
| 7 | Would a searchable, versioned model registry change how you work? | Enthusiasm, skepticism, blockers |

### Track B — MDM / Data Governance Team

| # | Question | What to listen for |
|---|---|---|
| 1 | How do you define "Customer" (or your core entity) today? | Shared doc, data dictionary, no single source |
| 2 | Who owns the definition? What happens when they leave? | Bus factor, transfer process, chaos |
| 3 | How do you track changes to master-data attributes? | Change log, email, Jira, nothing |
| 4 | How do auditors prove data lineage for a given field? | Screenshots, manual reports, cannot |
| 5 | Do you have duplicate or conflicting definitions across systems? | Examples, remediation effort |
| 6 | How do business users request changes to the data model? | Form, meeting, Slack, no process |
| 7 | What would make an approval workflow acceptable to both IT and business? | Speed, transparency, integration needs |

### Track C — AMS / Support Team

| # | Question | What to listen for |
|---|---|---|
| 1 | When a user reports a data issue, how do you identify the root field? | Time, tools, accuracy |
| 2 | Do you have documentation that maps business terms to technical fields? | Format, freshness, trust |
| 3 | How often do you need to ask a developer or consultant to explain a table? | Frequency, dependency, delay |
| 4 | What happens when a system is upgraded and field semantics change? | Detection, communication, impact |
| 5 | Would a quick lookup tool for field meanings reduce ticket resolution time? | Quantified estimate, willingness to use |

### Track D — Data Engineering / Analytics Team

| # | Question | What to listen for |
|---|---|---|
| 1 | How do you discover what tables and fields are available for a new report? | Data catalog, asking around, reverse engineering |
| 2 | How do you know if a field definition changed since the last pipeline run? | Monitoring, version control, nothing |
| 3 | How do you document transformations between raw and curated data? | dbt docs, notebooks, comments, nothing |
| 4 | Have you ever shipped a report based on a misunderstood field? | Impact, frequency, prevention |
| 5 | What would a "data model contract" between engineering and analytics look like? | Schema, ownership, SLAs |

### Track E — Solution Architect / Integration Team

| # | Question | What to listen for |
|---|---|---|
| 1 | How do you share interface specifications with external teams? | OpenAPI, Excel, meetings, nothing |
| 2 | How do you ensure both sides mean the same thing by a field name? | Mapping doc, testing, assumptions |
| 3 | How do you track which systems depend on a given interface field? | CMDB, spreadsheet, memory |
| 4 | What is the cost of an integration break caused by a semantic mismatch? | Hours, revenue, reputation |
| 5 | Would a canonical model layer between systems reduce integration risk? | Prior experience, skepticism |

### Track F — Project Manager / Data Owner

| # | Question | What to listen for |
|---|---|---|
| 1 | How do you track model-related decisions and their rationale? | Decision log, meeting notes, nothing |
| 2 | How do you prove to stakeholders that the data model was reviewed? | Email trail, sign-off sheet, cannot |
| 3 | What is your biggest frustration when scope changes affect data requirements? | Rework, communication, tracking |
| 4 | Who approves changes to the data model during a project? | Named role, process, or gap |
| 5 | Have you ever had a project delayed because model ownership was unclear? | Story, cost, frequency |
| 6 | What budget line would a model-governance tool come from? | Software, consulting, headcount |
| 7 | What would make you confident enough to recommend a new tool to procurement? | Pilot, reference, price, security review |

---

## Universal Questions (Ask Everyone)

1. **Current stack** — What tools do you use for documentation, tracking, and collaboration today? (Excel, Confluence, Jira, dbt, custom)
2. **Excel dependency** — How many spreadsheets does your team maintain for model knowledge? How often do they go stale?
3. **AI attitude** — How do you feel about AI suggesting changes to your data model? What would make you trust it?
4. **Integration needs** — Which systems would a model registry need to talk to? (SAP, dbt, GitHub, Jira, BI tools)
5. **Security posture** — Can you use cloud SaaS tools for data documentation, or must everything stay on-premise?
6. **Urgency** — Is this a "nice to have" or a "must solve this quarter" problem?
7. **Budget signal** — Have you paid for a similar tool or service before? How much?

---

## Disqualification Signals

Martenweave is **not a fit** if you hear:

- "We do not have a data model; we just query tables directly."
- "Our team is fully outsourced; knowledge transfer is not our problem."
- "We are migrating to a SaaS platform and will not need SAP-specific context."
- "We already have a full MDM suite with built-in governance (e.g., Informatica, Collibra)."
- "Our organisation bans Markdown and Git-based workflows entirely."
- "We need a real-time operational data store, not a documentation layer."

In these cases, thank the interviewee and ask for referrals to teams that might fit better.

---

## Post-Interview Scoring Template

Score each dimension 1–5.  A score of 3+ on Pain and 3+ on Access suggests a strong candidate.

| Dimension | 1 | 2 | 3 | 4 | 5 | Score |
|---|---|---|---|---|---|---|
| **Pain intensity** | Mild annoyance | Frustrating | Costs time weekly | Caused an incident | Business-critical gap | |
| **Pain frequency** | Rarely | Monthly | Weekly | Daily | Continuous | |
| **Current workaround cost** | None | Minutes | Hours | Days | Weeks+ | |
| **Access to buyer** | No idea | Influencer | Recommender | Budget owner | Decider + champion | |
| **Willingness to change** | Hostile | Skeptical | Open | Eager | Desperate | |
| **Budget signal** | No budget | Shared pool | Small tool budget | Dedicated line item | Already spent on similar | |
| **Martenweave fit** | Poor | Weak | Possible | Strong | Perfect | |

### Next Actions

- **Score 28–35**: Priority lead. Schedule a pilot scoping call within 1 week.
- **Score 20–27**: Qualified lead. Send case study and schedule follow-up in 2 weeks.
- **Score 12–19**: Nurture. Add to newsletter or community; re-engage in 3 months.
- **Score < 12**: Disqualify. Archive notes but keep door open.

---

## Notes on Using This Guide

- **Do not read questions verbatim.**  Use them as a checklist and weave them into a natural conversation.
- **Follow the pain.**  If the interviewee lights up on a topic, dig deeper with "Tell me more about that" and "What happened next?"
- **Avoid feature requests.**  Ask about problems and outcomes, not solutions.  "What would the ideal outcome look like?" is better than "Would you use feature X?"
- **Respect time.**  30 minutes of focused conversation beats 60 minutes of surveys.

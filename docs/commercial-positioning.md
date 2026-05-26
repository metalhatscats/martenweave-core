# Commercial Positioning and ICP

> Who Martenweave is for, what pain it solves, and how to talk about it.

---

## Ideal Customer Profile (ICP)

### Primary ICP: SAP Data Migration Programs

Teams running medium-to-large SAP S/4HANA or ECC migration projects who need to document, validate, and govern source-to-target mappings without losing knowledge when consultants leave.

| Attribute | Detail |
|---|---|
| **Team size** | 5–25 people |
| **Project value** | $500K–$5M |
| **Current state** | Mappings in Excel, knowledge in consultants' heads |
| **Urgent pain** | Audit failure, rework, go-live delay caused by undocumented mappings |
| **Buying trigger** | RFP requirement for "data model documentation" or audit finding |
| **Budget owner** | Program director or data workstream lead |
| **Champion** | Lead data architect or migration consultant |

### Secondary ICPs

| Segment | Pain | Why Secondary |
|---|---|---|
| **MDM / Data Governance teams** | No single source of truth for master data definitions | Often already evaluating Collibra/Informatica; Martenweave is lighter but must prove integration value |
| **AMS / Support teams** | Cannot trace field meaning during incident resolution | Smaller budgets; often need approval from larger MDM initiative |
| **Data Engineering / Analytics** | Schema drift breaks pipelines; no data contracts | May prefer dbt-native docs; Martenweave adds business context but requires adoption argument |
| **Integration Architecture teams** | Interface specs are scattered and versioned by email | Pain is real but often buried inside larger integration-platform decisions |

---

## Buyer and User Personas

### Persona: The Lead Data Architect (Champion + User)

- **Name**: Alex
- **Role**: Designs source-to-target mappings, reviews field semantics
- **Pain**: Spends 30% of time answering "what does this field mean?" questions; loses track of decisions
- **Desired outcome**: A searchable model that survives team turnover
- **Objection**: "Another tool to maintain."
- **Success metric**: Time to onboard a new consultant drops from 2 weeks to 2 days

### Persona: The Program Director (Budget Owner)

- **Name**: Priya
- **Role**: Owns migration budget and timeline; answers to steering committee
- **Pain**: Cannot prove data readiness to auditors; surprises at go-live
- **Desired outcome**: Defensible documentation and change tracking
- **Objection**: "We already pay for SAP and Excel."
- **Success metric**: Audit findings related to data mapping drop to zero

### Persona: The Data Steward (Daily User)

- **Name**: Jordan
- **Role**: Maintains business definitions, reviews change requests
- **Pain**: Business users send change requests via email with no context
- **Desired outcome**: Structured change proposals with impact preview
- **Objection**: "Business will not use anything that feels like IT."
- **Success metric**: Change request cycle time halves

### Persona: The Auditor / Compliance Officer (Influencer)

- **Name**: Sam
- **Role**: Validates data lineage and change control for SOX, GDPR, or internal audit
- **Pain**: Screenshots and email threads are not evidence
- **Desired outcome**: Machine-readable audit trail
- **Objection**: "How do we know the tool itself has not been tampered with?"
- **Success metric**: Audit sample preparation time drops by 80%

### Persona: The IT Security Reviewer (Blocker)

- **Name**: Riley
- **Role**: Must approve any new software touching production data
- **Pain**: SaaS tools require security reviews that take months
- **Desired outcome**: Local-first, no cloud dependency, no data egress
- **Objection**: "Any AI feature is a data-leak risk."
- **Success metric**: Security review completes in days, not months

---

## Positioning Statement

### For SAP migration teams

> Martenweave turns your spreadsheet mappings into a structured, searchable, versioned model knowledge layer.  Every field has business meaning, system context, and change history — so audits pass, onboarding is fast, and consultants do not walk out with the only copy of the truth.

### For MDM / governance teams

> Martenweave gives you a lightweight canonical model that lives in Git, not a proprietary SaaS.  You define master data objects once, trace them across systems, and approve changes through a transparent workflow — without buying a six-figure catalog.

### For AMS / support teams

> Martenweave is the field dictionary your support team actually trusts.  Search by business term, jump to the SAP table, see who owns the definition, and know when it last changed.

---

## What Martenweave Is Not

Be explicit early in conversations:

| Misconception | Clarification |
|---|---|
| "So it is a chatbot for SAP?" | No. AI assists with proposals; humans review and approve every change. |
| "A data catalog like Collibra?" | No. Martenweave is model-centric, not asset-centric. It documents business meaning, not database statistics. |
| "A workflow engine?" | No. It has lightweight approval gates, not BPMN. |
| "A BI or reporting tool?" | No. It documents models; it does not query data. |
| "Does it write back to SAP?" | No. Martenweave is read-only with respect to source systems. |
| "A no-code integration platform?" | No. It produces documentation and proposals, not runtime integrations. |

---

## Switching Triggers

Events that make prospects receptive:

1. **Audit finding** on data mapping or lineage documentation
2. **Consultant turnover** that took undocumented knowledge with them
3. **Go-live delay** caused by data-quality surprises
4. **New regulation** requiring data dictionary or change log
5. **Scale-up** from 5 to 20+ team members; Excel breaks
6. **AI pilot** where business wants AI-assisted modelling but IT requires governance

---

## Proof Points

Use these when prospects ask "who else uses this?"

- **Internal**: The `examples/customer_bp_model` repository is a full working slice (Business Partner → Customer) that can be explored in 10 minutes.
- **Pilot metric**: A 2-week pilot typically surfaces 10–30 undocumented mappings and raises ownership coverage from <20% to >60%.
- **Time to value**: A single team member can scaffold a repo and validate the first model in under 30 minutes.

---

## Recommended Beachhead

**Start with SAP migration teams running S/4HANA conversions.**

Why:
- Pain is acute, time-bound, and budgeted
- Existing tooling gap (Excel is the incumbent)
- Clear buyer (program director) and champion (data architect)
- Measurable outcomes (audit readiness, onboarding speed)
- Natural expansion path to MDM and AMS once the model exists


# Commercial Packaging and Pricing Hypotheses

> How Martenweave can pair public source and low-friction pilots with sustainable commercial terms.
>
> **Internal strategy document.** No pricing is published or finalized. Every figure in this
> document is an unvalidated internal hypothesis to be tested with design partners, not a
> published price.

---

## Principle

**Open source drives adoption. Paid services accelerate outcomes.**

The CLI, validation engine, and canonical model format are licensed under Apache License 2.0.
Users may deploy and extend the Core themselves, including for commercial work. Paid offerings add
expertise, facilitation, integrations, packs, support, training, or managed functionality; they do
not restrict the open-source Core.

For the explicit licensing decision record, see
[licensing-and-commercial-use.md](licensing-and-commercial-use.md).

---

## Packaging Options

### 1. Apache-Licensed Core CLI (Free, Commercial Use Allowed)

| What | Included |
|---|---|
| CLI commands | All: init, validate, build-index, health, trace, impact, export, import |
| Canonical model | Full Markdown/YAML format, all object types |
| Validation | Layer 1–3 deterministic validation |
| Index | SQLite + JSONL generation |
| AI scaffold | NoProviderAdapter (deterministic) |
| Telemetry | Local usage and AI usage event logging |

**Why free**: A data model registry is infrastructure. Open-source code and documentation build
trust with data architects. Paid work is positioned as optional services, support, templates,
integrations, packs, or future hosted products.

### 2. Team Pilot Package (No-Cost License Available by Agreement)

| What | Included |
|---|---|
| Facilitated pilot | 1–2 week guided pilot with a Martenweave facilitator |
| Custom onboarding | Repository setup, naming conventions, first model slice |
| Validation | Health report, scorecard, gap analysis |
| Deliverables | Excel review workbook, Git bundle, gap report |

**Pricing hypothesis**: License fee may be waived for selected design partners; facilitated
delivery is $2,000–$5,000 one-time
**Target**: Teams that want to prove value fast without internal expertise  
**Risk**: Services revenue does not scale; use it to learn and earn trust, not as the long-term model

### 3. Team Workspace (Paid Subscription, Future)

| What | Included |
|---|---|
| Multi-repo management | Central dashboard for 3–10 repositories |
| Enhanced exports | Formatted Word/PDF docs, branded scorecards |
| Integration connectors | dbt, Jira, Google Sheets, GitHub Issues sync |
| Collaboration features | Web-based review UI, comment threads on proposals |
| Support | Email support, 48-hour response |

**Pricing hypothesis**: $500–$2,000/month per team (10–25 users), for future hosted/team
functionality rather than access to the Apache-licensed Core
**Target**: Teams that have completed a pilot and want to scale  
**Risk**: Building a web UI is significant scope; defer until CLI adoption is proven

### 4. Enterprise Edition (Paid Subscription, Future)

| What | Included |
|---|---|
| SSO / SAML | Identity provider integration |
| Role-based access control | Fine-grained permissions beyond file system |
| Audit and compliance | SOC-2 ready, long-term audit retention |
| Dedicated support | Slack channel, 4-hour response |
| Custom AI provider | On-premise LLM, private fine-tuning |
| Multi-team governance | Cross-repo standards, shared ontologies |

**Pricing hypothesis**: $5,000–$15,000/month  
**Target**: Large programs with multiple workstreams and compliance requirements  
**Risk**: Enterprise features require security certifications and sales motion; do not build before Team Workspace is validated

### 5. Professional Services (Paid, À La Carte)

| Service | Description | Pricing Hypothesis |
|---|---|---|
| Migration model build | Full canonical model for a migration program | $20K–$100K fixed |
| MDM foundation | Core entity definitions, ownership, lineage | $10K–$50K fixed |
| Training workshop | 1-day hands-on workshop for a team | $3K–$5K |
| Custom integration | Connector to internal systems | $5K–$20K |

---

## What Is Available During Evaluation or an Approved Pilot

These capabilities remain available for evaluation and within the scope of a written pilot:

- Canonical file format and object type definitions
- Deterministic validation (Layer 1–3)
- SQLite index generation
- Basic export (CSV, XLSX)
- Local usage and AI usage telemetry
- Git-based collaboration (by nature of the format)

## What Requires Commercial Terms

Commercial terms cover production, ongoing internal, client-delivery, redistribution, or embedded
use. They may also include:

- Facilitated pilots and onboarding
- Web-based review and collaboration UI
- Advanced integrations (Jira, dbt, Sheets sync)
- Branded / formatted documentation exports
- Priority support and SLA
- SSO and RBAC
- Custom AI provider hosting

---

## Pricing Risks

| Risk | Mitigation |
|---|---|
| **Over-monetizing too early** | Keep evaluation friction low and approve strong design-partner pilots at no license fee |
| **Under-pricing services** | Track facilitator hours; raise prices if pilots consistently over-deliver |
| **Competitors undercut on price** | Compete on trust, local-first, and Git-native workflow, not price |
| **Enterprise buyers want procurement-friendly terms** | Offer annual billing and pilot-to-contract path after Team Workspace exists |
| **Teams expect AI for free** | External provider calls use the user's own API key; software-use rights still follow the applicable license |

---

## Recommended Sequence

1. **Now**: Free self-service evaluation under the Apache-2.0 license + no-cost design-partner pilots by written agreement
2. **After 5–10 pilots**: Standardize commercial licenses and paid facilitation ($2K–$5K)
3. **After 10+ team adoptions**: Design Team Workspace web UI; price at $500–$2K/month
4. **After Team Workspace revenue**: Build Enterprise edition with SSO, RBAC, SOC-2

Do not build Team Workspace or Enterprise features until CLI adoption is proven.

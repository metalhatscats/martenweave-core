# Commercial Packaging and Pricing Hypotheses

> How Martenweave could be packaged and priced without weakening trust or over-monetizing too early.

---

## Principle

**Open core drives adoption.  Paid value accelerates outcomes.**

The CLI, validation engine, and canonical model format are currently MIT-licensed. MIT permits
commercial use. Paid offerings should add convenience, collaboration, facilitation, templates,
future proprietary products, or expert support -- not imply that the current MIT core requires a
paid license.

For the explicit licensing decision record, see
[licensing-and-commercial-use.md](licensing-and-commercial-use.md).

---

## Packaging Options

### 1. MIT Core CLI (Free, Commercial Use Allowed)

| What | Included |
|---|---|
| CLI commands | All: init, validate, build-index, health, trace, impact, export, import |
| Canonical model | Full Markdown/YAML format, all object types |
| Validation | Layer 1–3 deterministic validation |
| Index | SQLite + JSONL generation |
| AI scaffold | NoProviderAdapter (deterministic) |
| Telemetry | Local usage and AI usage event logging |

**Why free**: A data model registry is infrastructure. Locking basic documentation behind a paywall
destroys trust with data architects. Under the current MIT license, commercial use of the core is
allowed; paid work must be positioned as optional services, support, templates, or future products.

### 2. Team Pilot Package (Paid Facilitation, Optional)

| What | Included |
|---|---|
| Facilitated pilot | 1–2 week guided pilot with a Martenweave facilitator |
| Custom onboarding | Repository setup, naming conventions, first model slice |
| Validation | Health report, scorecard, gap analysis |
| Deliverables | Excel review workbook, Git bundle, gap report |

**Pricing hypothesis**: $2,000–$5,000 one-time  
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
functionality rather than the current MIT core
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

## What Stays Free

Removing these from the free tier would hurt adoption:

- Canonical file format and object type definitions
- Deterministic validation (Layer 1–3)
- SQLite index generation
- Basic export (CSV, XLSX)
- Local usage and AI usage telemetry
- Git-based collaboration (by nature of the format)

## What Could Be Paid

These add value without breaking the open-core promise:

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
| **Over-monetizing too early** | Keep CLI free; charge only for services and convenience |
| **Under-pricing services** | Track facilitator hours; raise prices if pilots consistently over-deliver |
| **Competitors undercut on price** | Compete on trust, local-first, and Git-native workflow, not price |
| **Enterprise buyers want procurement-friendly terms** | Offer annual billing and pilot-to-contract path after Team Workspace exists |
| **Teams expect AI for free** | NoProviderAdapter is free; external provider calls require the user's own API key — no markup |

---

## Recommended Sequence

1. **Now**: Open-core CLI + free self-service pilot
2. **After 5–10 pilots**: Introduce paid pilot facilitation ($2K–$5K)
3. **After 10+ team adoptions**: Design Team Workspace web UI; price at $500–$2K/month
4. **After Team Workspace revenue**: Build Enterprise edition with SSO, RBAC, SOC-2

Do not build Team Workspace or Enterprise features until CLI adoption is proven.

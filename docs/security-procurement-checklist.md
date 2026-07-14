# Enterprise Security and Procurement Readiness Checklist

> Honest answers to the questions security reviewers and procurement will ask.

---

## Deployment Model

| Question | Answer |
|---|---|
| Is Martenweave cloud-hosted? | **No.** It runs entirely on your local machine or servers. |
| Does it require internet access? | **No** for core operations. AI provider calls (optional) require internet. |
| Can it run air-gapped? | **Yes.** All core features work without network access. |
| Where is data stored? | Canonical files in `model/` (Markdown/YAML); generated index in `generated/` (SQLite, JSONL). Both are on your filesystem. |
| Is there a SaaS component? | **Not in v1.** Future Team Workspace may offer hosted options; this checklist will be updated. |

---

## Data Handling

| Question | Answer |
|---|---|
| Does Martenweave store production data? | **No.** It stores model knowledge (field definitions, mappings, lineage), not actual records. |
| Can sample data be imported? | Yes, via `profile-dataset` and `import-model-sheet`. Sample data is stored in `data/samples/` and is treated as input only. |
| Is PII handled? | Not by design. If sample datasets contain PII, use the privacy-scrubbing options in `profile-dataset`. |
| What data leaves the machine? | Nothing, unless you: (1) configure an external AI provider, (2) push to GitHub, (3) use optional Google Sheets connector. |
| Is data encrypted at rest? | Martenweave does not encrypt files itself. Use filesystem encryption (BitLocker, FileVault, LUKS) as per your policy. |
| Is data encrypted in transit? | Not applicable for local-only usage. Git pushes use HTTPS/SSH encryption. AI provider calls use TLS. |

---

## AI and External Providers

| Question | Answer |
|---|---|
| Does Martenweave send data to AI providers by default? | **No.** Default adapter is `NoProviderAdapter`, which runs locally and makes no network calls. |
| What data is sent when AI is enabled? | Only the `AIContextBundle`: note text, column names, row counts, affected object IDs. **No raw dataset values, no API keys, no secrets.** |
| Which AI providers are supported? | Kimi/Moonshot (OpenAI-compatible). Others can be added via the `AIProviderAdapter` protocol. |
| Can we use our own LLM? | Yes. Implement `AIProviderAdapter` and point `MARTENWEAVE_AI_PROVIDER` to your adapter. |
| Is AI output stored? | AI-generated PatchProposals are stored as Markdown files in `model/patch-proposals/` for human review. |
| Can AI be disabled? | Yes. Do not set `MARTENWEAVE_AI_PROVIDER` or use `--no-ai` flags where available. |

---

## Secrets and Credentials

| Question | Answer |
|---|---|
| Where are API keys stored? | In environment variables or `.env` files. Martenweave does not have a secrets vault. |
| Are secrets logged? | **No.** API keys are redacted from logs and telemetry by default. |
| Is there a secret scanner? | Not built in. Use `pre-commit` or GitHub secret scanning on your repository. |

---

## Access Control

| Question | Answer |
|---|---|
| Does Martenweave have RBAC? | **Not in v1.** Access is controlled by filesystem permissions and Git branch protection. |
| How is user identity managed? | Not managed by Martenweave. Use Git identity, SSH keys, or your existing identity provider. |
| Can actions be attributed to users? | Yes via `actor` fields in audit events and Git commit history. |
| Is there an admin console? | **No.** All administration is via CLI and filesystem. |

---

## Audit and Compliance

| Question | Answer |
|---|---|
| Is there an audit log? | Yes. `generated/audit_events.jsonl` records proposal creation, change requests, approvals, and index builds. |
| How long are logs retained? | Martenweave does not rotate or delete logs. Manage retention via your log-management policy. |
| Can logs be tampered with? | JSONL files are append-only but not cryptographically signed. Use Git commit history for tamper evidence. |
| Does Martenweave support SOX/PCI/GDPR? | Martenweave provides structured documentation and audit trails that help with compliance, but it is not itself a certified compliance tool. |
| Is there a data retention policy? | Canonical files are retained as long as you keep them. Generated artifacts can be rebuilt at any time. |

---

## Procurement-Friendly Facts

| Concern | Current State | Planned |
|---|---|---|
| **Source code availability** | Source-available Python; inspect everything in `src/` | Remains inspectable |
| **Vendor lock-in** | Canonical files are plain Markdown/YAML; migrate by copying files | No proprietary format planned |
| **Exit cost** | Zero. Your data is in text files on your disk | Stays zero |
| **Support model** | GitHub issues + optional pilot or commercial support | Team support tier planned |
| **SLA** | None under the evaluation license | SLA considered for commercial terms |
| **Pricing transparency** | Evaluation is free; pilots may be no-cost by agreement | Commercial terms are scoped per use case |
| **Security questionnaire** | This checklist is the current answer set | Will expand as enterprise features are built |

---

## Pilot Security FAQ

**Q: Can we run the pilot without giving Martenweave any credentials?**  
A: Yes. All core features work without API keys or logins.

**Q: What if we accidentally commit a sample dataset with PII?**  
A: Use `modelops profile-dataset --privacy-policy redact` to scrub high-risk columns before importing. If already committed, rotate the repository or use Git history rewriting.

**Q: Can our security team review the code before we run it?**  
A: Yes. The entire codebase is in `src/modelops_core/`. There are no compiled binaries or hidden network calls in core operations.

**Q: Does Martenweave need write access to our SAP system?**  
A: **No.** Martenweave is read-only with respect to all source systems.

**Q: Can we restrict who can approve changes?**  
A: In v1, approval is enforced by process (ChangeRequest files) and Git branch protection, not by software RBAC.

---

## Honest Limitations

These are not yet implemented. Do not promise them:

- SSO / SAML integration
- Role-based access control (RBAC)
- Cryptographic log signing
- Automatic secrets scanning
- SOC 2, ISO 27001, or FedRAMP certification
- Real-time multi-user editing with conflict resolution
- Data loss prevention (DLP) integration

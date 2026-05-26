# Team Collaboration Model and Roles

> How teams work together in Martenweave without building a heavy workflow platform.

---

## Design Principle

Martenweave collaboration is **Git-native, file-based, and asynchronous**.  
There is no real-time editor, no locking, and no enterprise identity system in v1.  
Teams collaborate by editing Markdown/YAML files, opening GitHub PRs, and reviewing ChangeRequests.

---

## Roles

### Model Maintainer

- **Responsibility**: Keeps the canonical model consistent, valid, and indexed
- **Actions**: Runs `modelops validate`, `build-index`, reviews PRs, resolves conflicts
- **Maps to**: `OwnershipRole.maintainer` on `MasterDataDomain` or repository level
- **Tooling**: CLI, Git, GitHub PR review

### Data Steward

- **Responsibility**: Ensures business definitions are accurate and current
- **Actions**: Reviews attribute definitions, validates ValueLists, approves semantic changes
- **Maps to**: `OwnershipRole.data_steward` on `Attribute`, `BusinessEntity`, `ValueList`
- **Tooling**: CLI, exported XLSX review workbook, GitHub PR review

### Business Owner

- **Responsibility**: Owns the business meaning of a domain or entity
- **Actions**: Approves ChangeRequests that affect their domain; provides context for mappings
- **Maps to**: `OwnershipRole.business_owner` on `MasterDataDomain`, `BusinessEntity`
- **Tooling**: CLI (`cr-approve`), exported review workbook, GitHub notifications

### Technical Owner

- **Responsibility**: Owns the technical representation and system context
- **Actions**: Reviews FieldEndpoints, EntityContexts, system lineage; approves technical changes
- **Maps to**: `OwnershipRole.technical_owner` on `FieldEndpoint`, `EntityContext`, `System`
- **Tooling**: CLI, trace commands, impact analysis

### Reviewer

- **Responsibility**: Provides a second pair of eyes on PatchProposals and ChangeRequests
- **Actions**: Reads proposals, runs `proposal-impact`, comments on PRs
- **Maps to**: `Watcher` object or PR reviewer assignment
- **Tooling**: CLI, GitHub PR review, exported workbook

### Approver

- **Responsibility**: Formal sign-off on changes before apply
- **Actions**: Runs `cr-approve` or merges the PR that applies the proposal
- **Maps to**: `ChangeRequest.approvers` list
- **Tooling**: CLI (`cr-approve`), GitHub PR merge

### Integration Owner

- **Responsibility**: Ensures Martenweave fits into the broader data toolchain
- **Actions**: Sets up import sources, export pipelines, connector configs
- **Maps to**: `SourceRegistry` entries, connector configurations
- **Tooling**: CLI (`sources`, `import-sheet`, `export-model`)

### Agent Operator

- **Responsibility**: Supervises AI-assisted modelling; validates AI output
- **Actions**: Runs `propose-patch`, reviews AI-generated PatchProposals, adjusts assumptions
- **Maps to**: `PatchProposal.created_by = "ai"`, human approver on `ChangeRequest`
- **Tooling**: CLI (`propose-patch`, `proposal-validate`), MCP server

---

## Workflows

### Propose → Review → Approve → Apply

```
1. Agent or human creates a PatchProposal
   └─ modelops propose-patch --from note.md

2. Reviewer inspects the proposal
   └─ modelops proposal-impact PP-001
   └─ modelops proposal-validate PP-001

3. Reviewer creates a ChangeRequest for governance
   └─ modelops cr-create --id CR-001 --title "Update Customer Group"

4. Approver reviews and approves
   └─ modelops cr-approve CR-001

5. Maintainer applies the proposal
   └─ modelops proposal-apply PP-001

6. System emits audit events and rebuilds index
   └─ generated/audit_events.jsonl
   └─ modelops build-index
```

### Parallel Edit and Conflict Resolution

Because canonical files are plain text in Git:

1. Two stewards edit different objects → Git merge succeeds automatically
2. Two stewards edit the same object → Git merge conflict; maintainers resolve manually
3. One steward edits while another builds index → No conflict; index is disposable

**Rule**: `generated/` is never manually edited. If there is a conflict in `model/`, resolve it in the text file and re-run `modelops validate`.

### Notification and Watching

- **Martenweave-native**: `Watcher` objects on canonical files trigger `NotificationEvent` entries
- **GitHub-native**: PR reviews, mentions, and CI checks provide the actual notification layer
- **Email/Slack**: Not built in v1; integrate via GitHub webhooks or MCP server prompts

---

## Responsibility Matrix

| Activity | Maintainer | Steward | Business Owner | Technical Owner | Reviewer | Approver |
|---|---|---|---|---|---|---|
| Validate model | ✓ Lead | ✓ | | | | |
| Build index | ✓ Lead | | | | | |
| Define attribute | | ✓ Lead | ✓ Input | | | |
| Define field endpoint | | | | ✓ Lead | ✓ | |
| Create mapping | | ✓ | | ✓ | ✓ | |
| Propose change | ✓ | ✓ | | | | |
| Review proposal | | ✓ | ✓ | ✓ | ✓ Lead | |
| Create ChangeRequest | | ✓ | ✓ | | | |
| Approve ChangeRequest | | | ✓ Lead | | | ✓ Lead |
| Apply proposal | ✓ Lead | | | | | |
| Export workbook | ✓ | ✓ | | | | |
| Run impact analysis | ✓ | | | ✓ Lead | ✓ | |

---

## Minimum Viable Team

For a single migration object, the smallest useful team is:

1. **One Model Maintainer** (can be a consultant or data architect)
2. **One Business Owner** (subject-matter expert who knows the domain)
3. **One Technical Owner** (knows the source and target systems)

The same person can wear multiple hats in a small pilot, but approval and proposal should not be the same person.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| One person creates and approves their own ChangeRequest | No governance; mistakes propagate | Separate proposer and approver roles |
| Editing `generated/` files directly | Lost on next `build-index` | Edit `model/` only; regenerate index |
| Storing the only copy of truth in Martenweave | Martenweave documents truth; systems own data | Use Martenweave as knowledge layer, not data store |
| Expecting real-time collaboration | Martenweave is async/Git-based | Use short PR cycles and frequent validation |
| Giving every user full repo access | Accidental mutation | File-system permissions or Git branch protection |


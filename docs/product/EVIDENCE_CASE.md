# Migration Evidence Case

Version: 0.9.0
Status: implemented product direction

## Product promise

Give Martenweave one local migration artefact and get one traceable evidence case: deterministic
findings, governed model context, the decisions blocking readiness, and one human-controlled next
step.

## Primary user and job

The first user is an SAP migration or MDM lead preparing a mock load, design review, or handover.
Their source knowledge is fragmented across mapping workbooks, extracts, reports, tickets, and
people. The immediate job is not to build a complete catalog. It is to answer:

> What must be decided before this artefact is safe to use in the next migration step?

## First-value loop

```text
local artefact → persisted evidence → deterministic findings → human dispositions
              → evidence gate → candidate proposal → named review → controlled apply
```

The recommended SAP proof path is:

```bash
martenweave start ./customer_messy.csv \
  --template sap_bp_customer_migration \
  --no-open
```

The input is hashed and profiled locally. The starter supplies governed Customer/Business Partner
context. Generated evidence remains disposable. Every finding is persisted in a reviewable
`findings.json` package. The optional inference result is a deduplicated candidate `PatchProposal`,
not canonical truth.

## Product wedge

Martenweave wins the first use case by replacing the spreadsheet-and-meeting loop around one mock
load. It is the place where a migration lead can answer three questions without uploading source
data or manually rebuilding an audit trail:

1. What did the file prove?
2. Which findings require a human decision?
3. Which reviewed decisions justify the next governed model change?

The product does not try to be the whole migration platform. It makes the narrow, repeated
evidence-to-decision handoff reliable enough that teams use it after every mock load.

## Work Canvas contract

The first Workbench screen is not a dashboard and not a chatbot. It shows:

1. the current evidence case and source provenance;
2. a small set of decision groups derived from live findings;
3. the selected rule, evidence, model context, and required human decision;
4. a real disposition control for each finding, with rationale required for accepted risk or
   deferral;
5. one suggested next move that stays in classification until the evidence gate is satisfied.

Catalog, lineage, detailed findings, proposals, outputs, and history stay available as deeper tools
from the global icon rail.

## Truth and safety boundaries

- Facts, assumptions, AI suggestions, and human dispositions remain separate.
- Deterministic validation runs before approval.
- References are checked against both the proposal and the bound canonical repository.
- `martenweave workbench` uses an ephemeral same-origin local session for governed actions.
- Approval and apply are distinct. No inferred change is approved during automated QA.
- A start-run candidate proposal cannot be accepted while findings are unreviewed or deferred.
- `confirmed` means the gap is real; it does not claim the gap is already fixed or the migration is
  ready.
- No direct SAP write-back, hosted tenancy, or raw-data upload is implied.

## Return loop

The durable usage loop is one evidence case per mock load or design checkpoint:

```text
new extract → compare deterministic findings → retain prior dispositions → resolve new evidence
            → review bounded change → export review pack → run the next checkpoint
```

The current release implements persisted finding review and the approval gate. Cross-run decision
carry-forward and evidence comparison remain the next product slice; the UI and site must not imply
that they already exist.

## Product measures

- Time from local file to first classified finding.
- Share of findings with a recorded disposition and reviewer.
- Share of accepted-risk or deferred decisions with a rationale.
- Number of proposal approvals blocked by incomplete evidence review.
- Repeated evidence cases per workspace across mock-load checkpoints.

Feature count, chat interactions, and raw catalog size are not primary success metrics.

## Success evidence

A representative artefact is successful when a new user can run one command, open the Workbench,
understand the few decisions blocking readiness, record dispositions with a durable rationale,
trace a candidate proposal back to evidence, and reach a valid human review gate without editing
canonical files manually.

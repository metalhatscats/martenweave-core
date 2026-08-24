import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Check,
  CircleNotch,
  Command,
  FileText,
  GitBranch,
  MagnifyingGlass,
  ShieldCheck,
  Warning,
  X,
} from "@phosphor-icons/react";

import { gaps as demoGaps, proposals as demoProposals } from "./data.js";
import {
  API_STATE,
  useApi,
  useAssessmentFindings,
  useFindingReview,
  useProposals,
  useStartResult,
} from "./api.jsx";

const DECISION_OPTIONS = [
  { value: "confirmed", label: "Confirm gap", description: "Keep this evidence in scope for a governed change." },
  { value: "false_positive", label: "Not applicable", description: "Exclude this finding after human review." },
  { value: "accepted_risk", label: "Accept risk", description: "Proceed with a recorded rationale and named accountability." },
  { value: "deferred", label: "Defer", description: "Keep approval blocked until the decision is revisited." },
];

const GROUP_COPY = {
  UNMODELED_DATASET_COLUMN: {
    title: (count) => `${count} column${count === 1 ? " is" : "s are"} outside the governed model`,
    summary: "The source carries business meaning that the canonical model cannot yet explain.",
    decision: "Confirm meaning and assign semantic ownership before adding model objects.",
  },
  DUPLICATE_COLUMN_NAME: {
    title: () => "A source header appears more than once",
    summary: "Duplicate columns are preserved as evidence but must not create duplicate objects.",
    decision: "Choose the authoritative source column before the migration mapping is accepted.",
  },
  NO_MATCHING_ENDPOINTS: {
    title: () => "No physical endpoints are proven for this file",
    summary: "The file is profiled, but its fields are not connected to governed endpoints.",
    decision: "Review the proposed endpoints and keep unsupported mappings out of canonical truth.",
  },
  MISSING_OWNER: {
    title: (count) => `${count} governed object${count === 1 ? " has" : "s have"} no recorded owner`,
    summary: "The seeded model is usable for analysis, but accountability is incomplete.",
    decision: "Assign a real accountable owner or explicitly accept the ownership risk.",
  },
};

function findingCode(finding) {
  return String(
    finding.gap_code
      || finding.code
      || finding.finding_code
      || finding.category
      || finding.provenance?.rule_id
      || "ASSESSMENT_FINDING"
  ).toUpperCase();
}

function findingLocation(finding) {
  const location = finding.provenance?.location || {};
  return location.column_name || location.file || finding.affected_objects?.[0] || "Local assessment";
}

function groupFindings(entries, localReviews = {}) {
  const groups = new Map();
  entries.forEach((entry, index) => {
    const finding = entry.finding || entry;
    const code = findingCode(finding);
    const key = code === "ASSESSMENT_FINDING" ? `${code}-${index}` : code;
    const current = groups.get(key) || { code, items: [] };
    current.items.push({
      finding,
      assessmentId: entry.assessment_id || "readiness",
      review: localReviews[finding.id] || entry.review || null,
    });
    groups.set(key, current);
  });
  return [...groups.values()].map((group, index) => {
    const copy = GROUP_COPY[group.code];
    const count = group.items.length;
    const first = group.items[0].finding;
    const locations = [...new Set(group.items.map(({ finding }) => findingLocation(finding)))];
    const reviewedCount = group.items.filter(({ review }) => review?.disposition).length;
    return {
      id: `${group.code}-${index}`,
      code: group.code,
      title: copy ? copy.title(count) : first.message || "Assessment finding",
      summary: copy?.summary || first.recommended_action || "Review deterministic assessment evidence.",
      decision: copy?.decision || first.recommended_action || "Review and record a human disposition.",
      count,
      locations,
      severity: String(first.severity || "medium").toLowerCase(),
      proposalId: first.proposal_id || null,
      items: group.items,
      reviewedCount,
      remainingCount: count - reviewedCount,
    };
  });
}

function demoFindingGroups() {
  return demoGaps.map((gap, index) => ({
    id: gap.id || `demo-${index}`,
    code: "DEMO_FINDING",
    title: gap.title,
    summary: gap.note,
    decision: gap.proposalId
      ? "Review the linked proposal before any canonical change is applied."
      : "Inspect the evidence and create a governed proposal if the change is justified.",
    count: 1,
    locations: [gap.source],
    severity: String(gap.severity || "medium").toLowerCase(),
    proposalId: gap.proposalId || null,
    items: [],
    reviewedCount: 0,
    remainingCount: 1,
  }));
}

function BoundaryNotes({ capabilities }) {
  const notes = [];
  if (capabilities?.read_only) notes.push("Read-only workspace: evidence remains inspectable; canonical changes stay disabled.");
  const providers = capabilities?.ai?.active_providers;
  const aiConfigured = Array.isArray(providers) && providers.some((name) => name !== "no_provider");
  if (!aiConfigured) notes.push("No AI provider is active. The findings shown here are deterministic.");
  if (!notes.length) return null;
  return (
    <div className="work-boundaries">
      {notes.map((note) => <p key={note}><ShieldCheck size={14} /> {note}</p>)}
    </div>
  );
}

function ContextPanel({ selected, sourceName, modelContext, onClose, navigate, onDraft, onReviewed }) {
  const { demo } = useApi();
  const { reviewFinding, loading, error } = useFindingReview();
  const unresolved = selected?.items?.find(({ review }) => !review?.disposition);
  const currentItem = unresolved || selected?.items?.[0] || null;
  const [disposition, setDisposition] = useState("");
  const [note, setNote] = useState("");
  useEffect(() => {
    setDisposition("");
    setNote("");
  }, [selected?.id]);
  if (!selected) return null;
  const evidenceLabel = selected.locations.slice(0, 4).join(", ");
  const noteRequired = disposition === "accepted_risk" || disposition === "deferred";
  const canSave = Boolean(currentItem && disposition && (!noteRequired || note.trim()) && !loading && !demo);
  const saveDecision = async () => {
    if (!canSave) return;
    try {
      const review = await reviewFinding({
        assessment: currentItem.assessmentId,
        finding_id: currentItem.finding.id,
        disposition,
        reviewer: "workbench",
        note,
      });
      onReviewed(currentItem.finding.id, review);
      setDisposition("");
      setNote("");
    } catch {
      // The API error is rendered below.
    }
  };
  return (
    <aside className="work-context" aria-live="polite">
      <header>
        <strong>Context</strong>
        <button type="button" onClick={onClose} aria-label="Close context"><X size={16} /></button>
      </header>
      <div className="work-context-intro">
        <span className={`work-status-dot is-${selected.severity}`} />
        <h2>{selected.title}</h2>
        <p>{selected.summary}</p>
      </div>
      <dl className="work-context-list">
        <div><dt>Evidence</dt><dd>{evidenceLabel || sourceName}</dd></div>
        <div><dt>Deterministic check</dt><dd><code>{selected.code}</code></dd></div>
        <div><dt>Model context</dt><dd>{modelContext || "No seeded model context"}</dd></div>
        <div><dt>Human decision</dt><dd>{selected.decision}</dd></div>
      </dl>
      {currentItem ? (
        <section className="work-decision-form" aria-label="Record human disposition">
          <div className="work-decision-progress">
            <strong>{selected.reviewedCount} of {selected.count} classified</strong>
            <span>{currentItem.review?.disposition ? "Recorded" : `Now: ${findingLocation(currentItem.finding)}`}</span>
          </div>
          {currentItem.review?.disposition ? (
            <div className="work-decision-recorded"><Check size={15} /> {currentItem.review.disposition.replaceAll("_", " ")}</div>
          ) : (
            <>
              <div className="work-decision-options">
                {DECISION_OPTIONS.map((option) => (
                  <button
                    type="button"
                    className={disposition === option.value ? "is-selected" : ""}
                    key={option.value}
                    onClick={() => setDisposition(option.value)}
                  >
                    <strong>{option.label}</strong>
                    <small>{option.description}</small>
                  </button>
                ))}
              </div>
              <label className="work-decision-note">
                <span>Decision note {noteRequired ? "· required" : "· optional"}</span>
                <textarea value={note} onChange={(event) => setNote(event.target.value)} rows={2} placeholder="Record the reason future reviewers will need…" />
              </label>
              <button type="button" className="work-context-primary" onClick={saveDecision} disabled={!canSave}>
                {loading ? "Recording…" : "Record decision"}<ArrowRight size={16} />
              </button>
              {demo && <p className="work-decision-error">Connect the local API to record decisions.</p>}
              {error && <p className="work-decision-error">{error}</p>}
            </>
          )}
        </section>
      ) : (
        <button type="button" className="work-context-primary" onClick={() => selected.proposalId ? navigate("proposal", { id: selected.proposalId }) : onDraft()}>
          {selected.proposalId ? "Review linked proposal" : "Prepare governed change"}<ArrowRight size={16} />
        </button>
      )}
      <button type="button" className="work-context-secondary" onClick={() => navigate("lineage")}>Open related evidence</button>
    </aside>
  );
}

function EmptyCase({ connected, probing, capabilities }) {
  return (
    <div className="work-empty">
      {probing ? <CircleNotch className="spin" size={22} /> : <FileText size={22} />}
      <h2>{probing ? "Opening local evidence…" : "Start with one migration artifact"}</h2>
      <p>
        {connected
          ? <>Run <code>martenweave start &lt;dataset-file&gt;</code> to create a persisted evidence case.</>
          : "Connect the local API to inspect a real workspace. Sample data stays clearly marked."}
      </p>
      <BoundaryNotes capabilities={capabilities} />
    </div>
  );
}

export function ReadinessScreen({ navigate, onDraft, refreshKey = 0 }) {
  const { demo, capabilities, client, state } = useApi();
  const { findings } = useAssessmentFindings();
  const { result: startResult } = useStartResult();
  const { proposals } = useProposals(refreshKey);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [contextOpen, setContextOpen] = useState(true);
  const [localReviews, setLocalReviews] = useState({});

  const probing = state === API_STATE.UNKNOWN;
  const connected = state === API_STATE.CONNECTED;
  const startActive = !demo && Boolean(startResult?.available);
  const sourceFindingEntries = demo
    ? []
    : findings?.length
      ? findings
      : startActive
        ? (startResult.findings || []).map((finding) => ({
            finding,
            assessment_id: startResult.decision_gate?.assessment_id || "readiness",
            review: null,
          }))
        : [];
  const groups = useMemo(
    () => demo ? demoFindingGroups() : groupFindings(sourceFindingEntries, localReviews),
    [demo, sourceFindingEntries, localReviews]
  );
  const visibleGroups = groups.filter((group) =>
    `${group.title} ${group.summary} ${group.locations.join(" ")}`.toLowerCase().includes(query.toLowerCase())
  );
  const selected = visibleGroups.find((group) => group.id === selectedId) || visibleGroups[0];
  const sourceName = startResult?.provenance?.input_name || (demo ? "customer_migration.xlsx" : "Local evidence");
  const modelContext = startResult?.provenance?.context_domain
    || (startResult?.provenance?.model_context === "seeded" ? "Seeded canonical model" : null);
  const proposalArtifact = startResult?.evidence?.draft_proposal;
  const proposalId = proposalArtifact
    ? String(proposalArtifact).split("/").at(-1).replace(/\.md$/i, "")
    : null;
  const liveProposals = demo ? demoProposals : proposals;
  const pending = liveProposals.filter((proposal) => proposal.status === "In review").length;
  const ready = startActive && startResult.verdict === "ready";
  const sha = startResult?.provenance?.input_sha256;
  const totalDecisions = groups.reduce((total, group) => total + group.count, 0);
  const reviewedDecisions = groups.reduce((total, group) => total + group.reviewedCount, 0);
  const remainingDecisions = Math.max(0, totalDecisions - reviewedDecisions);
  const hasDeferredDecision = groups.some((group) => group.items.some(({ review }) => review?.disposition === "deferred"));
  const proposalReviewReady = totalDecisions === 0 || (remainingDecisions === 0 && !hasDeferredDecision);

  const primaryAction = () => {
    if (!proposalReviewReady) {
      const nextGroup = groups.find((group) => group.remainingCount > 0 || group.items.some(({ review }) => review?.disposition === "deferred"));
      if (nextGroup) setSelectedId(nextGroup.id);
      setContextOpen(true);
    }
    else if (proposalId) navigate("proposal", { id: proposalId });
    else if (ready) navigate("models");
    else if (selected?.proposalId) navigate("proposal", { id: selected.proposalId });
    else onDraft();
  };
  const primaryLabel = !proposalReviewReady
    ? remainingDecisions > 0 ? "Classify next finding" : "Resolve deferred decision"
    : proposalId || selected?.proposalId
    ? "Review candidate change"
    : ready
      ? "Inspect governed model"
      : "Prepare governed change";

  return (
    <main className={`work-page ${contextOpen && selected ? "has-context" : ""}`}>
      <section className="work-canvas">
        {(startActive || demo || sourceFindingEntries.length > 0) ? (
          <>
            <header className="work-hero">
              <span>Evidence case · processed locally</span>
              <h1>
                {ready
                  ? "This file is ready for governed inspection."
                  : remainingDecisions > 0
                    ? `${remainingDecisions} evidence decision${remainingDecisions === 1 ? " remains" : "s remain"} before change review.`
                    : hasDeferredDecision
                      ? "A deferred decision keeps approval safely blocked."
                      : "Every finding is classified. The candidate change is ready for review."}
              </h1>
              <p>Martenweave keeps source evidence, deterministic checks, and human decisions in one traceable workspace.</p>
              <div className="work-progress" aria-label={`${reviewedDecisions} of ${totalDecisions} findings classified`}>
                <span style={{ width: `${totalDecisions ? (reviewedDecisions / totalDecisions) * 100 : 100}%` }} />
                <small>{groups.length} decision groups · {reviewedDecisions}/{totalDecisions} findings classified</small>
              </div>
            </header>

            <div className="work-source-row">
              <span className="work-source-icon"><FileText size={17} /></span>
              <span><strong>{sourceName}</strong><small>{demo ? "Sample case · no canonical mutation" : `Persisted start run${sha ? ` · sha256 ${String(sha).slice(0, 12)}` : ""}`}</small></span>
              <span className="work-local-state"><i /> {demo ? "Sample evidence" : "Source preserved"}</span>
            </div>

            <div className="work-section-heading">
              <div><h2>What needs a decision</h2><p className="sr-only">Readiness queue</p></div>
              <div className="work-search">
                <MagnifyingGlass size={15} />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find in this case" aria-label="Find in this evidence case" />
              </div>
            </div>

            <div className="work-findings" role="listbox" aria-label="Readiness queue">
              {visibleGroups.map((group) => (
                <button
                  type="button"
                  role="option"
                  aria-selected={group.id === selected?.id && contextOpen}
                  className="work-finding"
                  key={group.id}
                  onClick={() => { setSelectedId(group.id); setContextOpen(true); }}
                >
                  <span className={`work-finding-marker is-${group.severity}`}><Warning size={13} weight="fill" /></span>
                  <span><strong>{group.title}</strong><small>{group.summary}</small></span>
                  <span className="work-finding-count">{group.reviewedCount}/{group.count} classified</span>
                  <ArrowRight size={16} />
                </button>
              ))}
              {!visibleGroups.length && (
                <div className="work-no-findings">
                  {query ? <><MagnifyingGlass size={20} /><strong>No evidence matches “{query}”</strong><button type="button" onClick={() => setQuery("")}>Clear search</button></> : <><Check size={20} /><strong>No open findings in this case</strong></>}
                </div>
              )}
            </div>

            <section className="work-next-move">
              <span className="work-next-icon"><GitBranch size={17} /></span>
              <span><strong>Suggested next move</strong><small>{ready ? "Inspect the canonical model and retain this readiness result as evidence." : proposalReviewReady ? "Compare the candidate change with the recorded decisions before approval." : "Classify one finding. Accepted risk and deferral require a recorded rationale."}</small></span>
              <button type="button" onClick={primaryAction}>{primaryLabel}<ArrowRight size={15} /></button>
            </section>

            <div className="work-command-bar">
              <Command size={17} />
              <button type="button" onClick={() => selected && setContextOpen(true)}>
                {selected ? `Explain ${selected.code}` : "Choose a finding to inspect evidence"}
              </button>
              <kbd>/</kbd>
            </div>

            <footer className="work-case-footer">
              <span><ShieldCheck size={14} /> {pending} proposal{pending === 1 ? "" : "s"} awaiting review</span>
              {client && startResult?.evidence?.readiness_markdown && (
                <a href={client.reportDownloadUrl(startResult.evidence.readiness_markdown)} target="_blank" rel="noreferrer">Open persisted report <ArrowRight size={13} /></a>
              )}
            </footer>
            <BoundaryNotes capabilities={capabilities} />
          </>
        ) : <EmptyCase connected={connected} probing={probing} capabilities={capabilities} />}
      </section>
      {contextOpen && selected && (
        <ContextPanel
          selected={selected}
          sourceName={sourceName}
          modelContext={modelContext}
          onClose={() => setContextOpen(false)}
          navigate={navigate}
          onDraft={onDraft}
          onReviewed={(findingId, review) => setLocalReviews((current) => ({ ...current, [findingId]: review }))}
        />
      )}
    </main>
  );
}

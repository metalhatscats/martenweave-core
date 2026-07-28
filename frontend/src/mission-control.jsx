import { useMemo, useState } from "react";
import {
  ArrowRight,
  CheckCircle,
  CircleNotch,
  FileText,
  Funnel,
  GitBranch,
  MagnifyingGlass,
  NotePencil,
  ShieldCheck,
  Warning,
} from "@phosphor-icons/react";

import { gaps as demoGaps, proposals as demoProposals } from "./data.js";
import { useApi, useAssessmentFindings, useProposals } from "./api.jsx";
import { HomeAssistant } from "./workbench.jsx";

const JOURNEY = [
  ["Discover", "Files and systems scanned", "complete"],
  ["Understand", "Evidence connected", "complete"],
  ["Resolve", "Work requiring attention", "active"],
  ["Approve", "Human decision required", "waiting"],
];

function confidenceFor(gap) {
  if (gap.severity === "High") return 62;
  if (gap.severity === "Medium") return 78;
  return 91;
}

function actionFor(gap) {
  if (gap.proposalId) return "Review proposal";
  return "Create proposal";
}

function findingToGap(finding, index) {
  return {
    id: finding.id || `finding-${index}`,
    title: finding.message || "Assessment finding",
    severity: String(finding.severity || "medium").replace(/^./, (value) => value.toUpperCase()),
    object: finding.affected_objects?.[0] || "Canonical model",
    source: finding.provenance?.location?.file || "Local assessment",
    owner: "Unassigned",
    initials: "—",
    note: finding.recommended_action || "Review deterministic assessment evidence.",
    proposalId: finding.proposal_id || null,
    detected: "Recently",
  };
}

function Stage({ item, index }) {
  const [name, detail, state] = item;
  const Icon = state === "complete" ? CheckCircle : state === "active" ? Warning : ShieldCheck;
  return (
    <div className={`mission-stage is-${state}`}>
      <span className="mission-stage-icon"><Icon size={19} weight={state === "complete" ? "fill" : "regular"} /></span>
      <span><strong>{name}</strong><small>{detail}</small></span>
      {index < JOURNEY.length - 1 && <i aria-hidden="true" />}
    </div>
  );
}

function QueueItem({ gap, selected, onSelect, navigate }) {
  const confidence = confidenceFor(gap);
  const go = () => gap.proposalId ? navigate("proposal", { id: gap.proposalId }) : navigate("gaps", { gap: gap.id });
  return (
    <button type="button" className={`mission-queue-item ${selected ? "is-selected" : ""}`} onClick={onSelect}>
      <span className={`mission-severity severity-${gap.severity.toLowerCase()}`}><Warning size={18} weight="fill" /></span>
      <span className="mission-queue-copy">
        <span><strong>{gap.title}</strong><em>{gap.severity}</em></span>
        <small>{gap.note}</small>
        <code>{gap.source} <ArrowRight size={12} /> {gap.object}</code>
      </span>
      <span className="mission-confidence" aria-label={`${confidence}% evidence confidence`}>
        <CheckCircle size={22} weight="fill" /><strong>{confidence}%</strong>
      </span>
      <span className="mission-owner"><b>{gap.initials}</b><span><strong>{gap.owner}</strong><small>Data steward</small></span></span>
      <span className="mission-evidence"><FileText size={15} /><GitBranch size={15} /><span>+2</span></span>
      <span className="mission-next" onClick={(event) => { event.stopPropagation(); go(); }}>{actionFor(gap)} <ArrowRight size={16} /></span>
    </button>
  );
}

export function ReadinessScreen({ navigate, onDraft, refreshKey = 0 }) {
  const { demo, capabilities } = useApi();
  const { findings } = useAssessmentFindings();
  const { proposals } = useProposals(refreshKey);
  const [query, setQuery] = useState("");
  const [risk, setRisk] = useState("Risk: High first");
  const [selectedId, setSelectedId] = useState("1");

  const queue = useMemo(() => {
    const source = demo ? demoGaps : (findings || []).map(findingToGap);
    const severityOrder = { High: 0, Medium: 1, Low: 2 };
    return source
      .filter((gap) => `${gap.title} ${gap.note} ${gap.object}`.toLowerCase().includes(query.toLowerCase()))
      .sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);
  }, [demo, findings, query]);
  const selected = queue.find((gap) => String(gap.id) === String(selectedId)) || queue[0];
  const liveProposals = demo ? demoProposals : proposals;
  const pending = liveProposals.filter((proposal) => proposal.status === "In review").length;

  return (
    <main className="mission-page">
      <header className="mission-hero">
        <div>
          <span className="mission-eyebrow">Martenweave / local decision workspace</span>
          <h1>Data migration command centre</h1>
          <p>Turn migration signals into evidence-backed, governed decisions.</p>
        </div>
        <div className="mission-sync"><CheckCircle size={18} weight="fill" /><span><strong>{demo ? "Sample evidence ready" : "Local evidence synced"}</strong><small>{capabilities?.indexed ? "Canonical index available" : "Working in local sample mode"}</small></span></div>
      </header>

      <section className="mission-journey" aria-label="Migration workflow">
        {JOURNEY.map((item, index) => <Stage key={item[0]} item={item} index={index} />)}
      </section>

      <section className="mission-workspace">
        <div className="mission-queue-panel">
          <div className="mission-section-heading">
            <div><span className="mission-eyebrow">Actionable work</span><h2>Readiness queue</h2><p>{queue.length} item{queue.length === 1 ? "" : "s"} need your attention</p></div>
            <div className="mission-controls">
              <label><MagnifyingGlass size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find a signal" aria-label="Find a readiness signal" /></label>
              <button type="button" onClick={() => setRisk(risk === "Risk: High first" ? "All signals" : "Risk: High first")}><Funnel size={16} /> {risk}</button>
            </div>
          </div>
          <div className="mission-queue-column-labels"><span>Signal</span><span>Confidence</span><span>Owner</span><span>Evidence</span><span>Next action</span></div>
          <div className="mission-queue-list">
            {queue.map((gap) => <QueueItem key={gap.id} gap={gap} selected={String(gap.id) === String(selected?.id)} onSelect={() => setSelectedId(String(gap.id))} navigate={navigate} />)}
            {!queue.length && <div className="mission-empty"><MagnifyingGlass size={24} /><strong>No signals match this view</strong><button type="button" onClick={() => setQuery("")}>Clear search</button></div>}
          </div>
        </div>

        <aside className="mission-decision">
          <span className="mission-eyebrow">Today’s decision</span>
          {selected ? <>
            <div className="mission-decision-title"><span>1</span><div><strong>{selected.title}</strong><em className={`severity-${selected.severity.toLowerCase()}`}>{selected.severity} risk</em></div></div>
            <p>{selected.note}</p>
            <div className="mission-decision-section"><strong>Why this needs attention</strong><ul><li>Affects reporting and migration completeness</li><li>Downstream systems depend on this model object</li></ul></div>
            <div className="mission-decision-section"><span><strong>Evidence</strong><button type="button" onClick={() => navigate("lineage", { id: selected.linkedObjectId || "DOMAIN-CUSTOMER-BP" })}>View all</button></span><button type="button" className="mission-evidence-row" onClick={() => navigate("lineage", { id: selected.linkedObjectId || "DOMAIN-CUSTOMER-BP" })}><FileText size={16} /><span>Source field & profile<small>{selected.source}</small></span><ArrowRight size={15} /></button><button type="button" className="mission-evidence-row" onClick={() => navigate("lineage", { id: selected.linkedObjectId || "DOMAIN-CUSTOMER-BP" })}><GitBranch size={16} /><span>Lineage impact<small>{selected.object}</small></span><ArrowRight size={15} /></button></div>
            <div className="mission-recommendation"><ShieldCheck size={18} /><div><strong>Recommended next step</strong><p>{selected.proposalId ? "Review the evidence-backed proposal before approving the canonical change." : "Review evidence and create a governed proposal to resolve this gap."}</p></div></div>
            <button type="button" className="mission-primary" onClick={() => selected.proposalId ? navigate("proposal", { id: selected.proposalId }) : onDraft()}>{selected.proposalId ? "Review proposal" : "Create proposal"}<ArrowRight size={17} /></button>
          </> : <div className="mission-empty"><CircleNotch className="spin" size={24} /> Loading the next decision…</div>}
          <footer><ShieldCheck size={15} /> {pending} proposal{pending === 1 ? "" : "s"} awaiting governed review</footer>
        </aside>
      </section>
      <section className="mission-assistant-panel">
        <div className="mission-section-heading"><div><span className="mission-eyebrow">Investigate before you decide</span><h2>Ask the evidence layer</h2><p>Search the canonical model, trace lineage, and open the next governed step.</p></div></div>
        <HomeAssistant navigate={navigate} />
      </section>
    </main>
  );
}

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  BracketsCurly,
  CaretDown,
  Check,
  CheckCircle,
  CircleNotch,
  ClockCounterClockwise,
  Command,
  Cube,
  Database,
  DownloadSimple,
  FileArrowDown,
  FileCsv,
  FileText,
  Funnel,
  GitBranch,
  GridFour,
  Keyboard,
  MagnifyingGlass,
  NotePencil,
  Rows,
  ShareNetwork,
  ShieldCheck,
  SlidersHorizontal,
  Stack,
  UploadSimple,
  Warning,
  X,
} from "@phosphor-icons/react";
import { fields, gaps, modelObjects, proposals, recentActivity } from "./data.js";

const LEDGER_ROWS = [
  {
    id: "DOMAIN-CUSTOMER-BP",
    name: "Business Partner",
    type: "Domain",
    source: "Canonical",
    validation: "Validated",
    evidence: 18,
    impact: "High",
    owner: "Alex Chen",
    initials: "AC",
    updated: "15m ago",
    tone: "blue",
  },
  {
    id: "ENTITY-CUSTOMER-SALES-AREA",
    name: "Customer Sales Area",
    type: "Entity",
    source: "Canonical",
    validation: "In review",
    evidence: 12,
    impact: "High",
    owner: "Priya Nair",
    initials: "PN",
    updated: "18m ago",
    tone: "cyan",
  },
  {
    id: "ATTR-BP-TAX-NUMBER",
    name: "TAX_NUMBER",
    type: "Attribute",
    source: "Canonical",
    validation: "Gap",
    evidence: 27,
    impact: "High",
    owner: "Alex Chen",
    initials: "AC",
    updated: "21m ago",
    tone: "violet",
  },
  {
    id: "FEP-S4-KNVV-STCD1",
    name: "S4 KNVV.STCD1",
    type: "Endpoint",
    source: "SAP S/4HANA",
    validation: "Validated",
    evidence: 9,
    impact: "Medium",
    owner: "Jamie Singh",
    initials: "JS",
    updated: "32m ago",
    tone: "green",
  },
  {
    id: "MAP-SAP-BP-TAX-NUMBER",
    name: "BP → TAX_NUMBER",
    type: "Mapping",
    source: "SAP BP mapping",
    validation: "Validated",
    evidence: 14,
    impact: "Medium",
    owner: "Alex Chen",
    initials: "AC",
    updated: "38m ago",
    tone: "orange",
  },
  {
    id: "GAP-001",
    name: "BP tax number missing",
    type: "Gap",
    source: "Discovery",
    validation: "Open",
    evidence: 3,
    impact: "High",
    owner: "Priya Nair",
    initials: "PN",
    updated: "1h ago",
    tone: "red",
  },
  {
    id: "PROPOSAL-27",
    name: "Add TAX_NUMBER mapping",
    type: "Proposal",
    source: "Martenweave AI",
    validation: "Proposed",
    evidence: 8,
    impact: "High",
    owner: "Alex Chen",
    initials: "AC",
    updated: "52m ago",
    tone: "violet",
  },
];

const TYPE_ICONS = {
  Domain: Cube,
  Entity: Stack,
  Attribute: BracketsCurly,
  Endpoint: Database,
  Mapping: GitBranch,
  Gap: Warning,
  Proposal: NotePencil,
};

const SOURCE_TYPES = [
  {
    id: "canonical",
    title: "Canonical model files",
    description: "Markdown and YAML objects from model/",
    icon: FileText,
    files: "37 files",
  },
  {
    id: "excel",
    title: "Excel mapping files",
    description: "Source-to-target mappings and field inventories",
    icon: FileCsv,
    files: "1 workbook",
  },
  {
    id: "dataset",
    title: "Dataset extracts",
    description: "CSV or delimited source-system samples",
    icon: Database,
    files: "3 datasets",
  },
  {
    id: "validation",
    title: "Validation reports",
    description: "Deterministic findings and quality evidence",
    icon: ShieldCheck,
    files: "2 reports",
  },
  {
    id: "notes",
    title: "Tickets, decisions, notes",
    description: "Project evidence for review and traceability",
    icon: NotePencil,
    files: "8 notes",
  },
];

const EXPORT_TYPES = [
  ["index", "Model index", "Canonical objects, statuses, ownership, and references"],
  ["gaps", "Gap report", "Filtered gaps with severity, evidence, and next actions"],
  ["impact", "Impact report", "Deterministic downstream traversal from the current scope"],
  ["lineage", "Lineage snapshot", "Visible relationship graph with node and edge evidence"],
  ["proposal", "Patch proposal", "Review bundle with diff, validation, and risk context"],
  ["evidence", "Evidence summary", "Sources, validation results, coverage, and decisions"],
];

function StatusBadge({ value }) {
  const tone =
    value === "Validated"
      ? "green"
      : value === "Gap" || value === "Open" || value === "High"
        ? "high"
        : value === "In review" || value === "Proposed"
          ? "violet"
          : "orange";
  return <span className={`badge badge-${tone}`}>{value}</span>;
}

function LedgerDetail({ row, tab, onTab, navigate }) {
  const tabs = ["Summary", "Evidence", "Lineage", "Coverage", "Issues", "Proposals"];
  return (
    <section className="ledger-detail" aria-label={`${row.name} details`}>
      <header>
        <span className={`ledger-type-icon tone-${row.tone}`}>
          {(() => {
            const Icon = TYPE_ICONS[row.type] || Database;
            return <Icon size={17} weight="duotone" />;
          })()}
        </span>
        <span>
          <strong>{row.id}</strong>
          <small>{row.name}</small>
        </span>
        <button
          className="secondary-button"
          onClick={() =>
            navigate(
              row.type === "Gap"
                ? "gaps"
                : row.type === "Proposal"
                  ? "proposal"
                  : row.type === "Endpoint" || row.type === "Mapping"
                    ? "lineage"
                    : "object",
              row.type === "Proposal"
                ? { id: 27 }
                : row.type === "Gap"
                  ? { gap: 1 }
                  : { id: row.id === "ATTR-BP-TAX-NUMBER" ? "DOMAIN-CUSTOMER-BP" : row.id },
            )
          }
        >
          Open full view <ArrowRight size={14} />
        </button>
      </header>
      <nav className="ledger-detail-tabs" aria-label="Object detail sections">
        {tabs.map((item) => (
          <button key={item} className={tab === item ? "is-active" : ""} onClick={() => onTab(item)}>
            {item}
            {item === "Issues" && <span>1</span>}
            {item === "Proposals" && <span>1</span>}
          </button>
        ))}
      </nav>
      <div className="ledger-detail-content">
        {tab === "Summary" && (
          <>
            <div>
              <small>Source evidence</small>
              <dl>
                <dt>System</dt><dd>SAP S/4HANA 2023</dd>
                <dt>Table</dt><dd>KNVV</dd>
                <dt>Field</dt><dd>STCD1</dd>
                <dt>Data type</dt><dd>CHAR(20)</dd>
              </dl>
              <button onClick={() => onTab("Evidence")}>View all 27 evidence items</button>
            </div>
            <div>
              <small>Rule results</small>
              {["Naming convention", "Data type match", "Nullability match", "Length match"].map((item) => (
                <p className="ledger-check" key={item}><CheckCircle size={14} /> {item}<strong>Pass</strong></p>
              ))}
              <button onClick={() => onTab("Evidence")}>View all rules</button>
            </div>
            <div>
              <small>Dataset coverage</small>
              <dl>
                <dt>Covered datasets</dt><dd>8 / 10</dd>
                <dt>Rows with data</dt><dd>8.7M (92%)</dd>
                <dt>Null / empty</dt><dd>0.7M (8%)</dd>
                <dt>Last observed</dt><dd>2m ago</dd>
              </dl>
              <button onClick={() => onTab("Coverage")}>View coverage details</button>
            </div>
            <div>
              <small>Downstream impact</small>
              <dl>
                <dt>Mappings</dt><dd>3</dd>
                <dt>Endpoints</dt><dd>4</dd>
                <dt>Reports</dt><dd>2</dd>
                <dt>Processes</dt><dd>2</dd>
              </dl>
              <button onClick={() => navigate("lineage")}>View impacted items</button>
            </div>
            <div>
              <small>Approval chain</small>
              {[
                ["Data Steward", "Priya Nair"],
                ["MDM Lead", "Alex Chen"],
                ["Governance", "Marcus Lee"],
              ].map(([role, person]) => (
                <p className="ledger-check" key={role}><CheckCircle size={14} /> {role}<strong>{person}</strong></p>
              ))}
              <button onClick={() => navigate("proposal", { id: 27 })}>Open Proposal #27</button>
            </div>
          </>
        )}
        {tab === "Evidence" && (
          <div className="ledger-tab-wide">
            <small>Traceable source evidence</small>
            <div className="evidence-ledger">
              {[
                ["Source profile", "KNVV.STCD1", "158,932 distinct values · 2.1% null"],
                ["Canonical rule", "ATTR-BP-TAX-NUMBER", "String(20) · optional · restricted characters"],
                ["Decision", "DEC-BP-004", "Preserve source tax identifiers during migration"],
                ["Validation run", "VAL-2026-07-03-1018", "4 checks passed · 1 warning"],
              ].map(([kind, id, note]) => (
                <div key={id}><span><strong>{kind}</strong><code>{id}</code></span><small>{note}</small><CheckCircle size={14} /></div>
              ))}
            </div>
          </div>
        )}
        {tab === "Lineage" && (
          <div className="ledger-tab-wide compact-path">
            <small>Highest-risk relationship path</small>
            <p><span>SAP S/4HANA</span><ArrowRight size={15} /><span>KNVV.STCD1</span><ArrowRight size={15} /><span>TAX_NUMBER</span><ArrowRight size={15} /><span>Customer analytics</span></p>
            <button className="primary-button" onClick={() => navigate("lineage")}>Open interactive lineage</button>
          </div>
        )}
        {tab === "Coverage" && (
          <div className="ledger-tab-wide coverage-detail">
            <small>Dataset coverage</small>
            {[
              ["SAP Business Partner extract", 98],
              ["Legacy CRM customer export", 86],
              ["Customer analytics mart", 91],
              ["MDM golden record", 73],
            ].map(([name, value]) => (
              <div key={name}><span>{name}<strong>{value}%</strong></span><i><b style={{ width: `${value}%` }} /></i></div>
            ))}
          </div>
        )}
        {tab === "Issues" && (
          <div className="ledger-tab-wide">
            <small>Open issue</small>
            <button className="ledger-issue" onClick={() => navigate("gaps", { gap: 1 })}>
              <Warning size={20} />
              <span><strong>Missing mapping for TAX_NUMBER</strong><small>High severity · Detected in SAP Sales Order · 18m ago</small></span>
              <ArrowRight size={16} />
            </button>
          </div>
        )}
        {tab === "Proposals" && (
          <div className="ledger-tab-wide">
            <small>Linked proposal</small>
            <button className="ledger-issue proposal" onClick={() => navigate("proposal", { id: 27 })}>
              <NotePencil size={20} />
              <span><strong>Proposal #27 · Customer alternative key mapping</strong><small>Validation passed · High impact · Human review required</small></span>
              <ArrowRight size={16} />
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

export function WorkspaceScreen({ navigate, onImport, onExport, onCommands, onShortcuts }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("All types");
  const [domain, setDomain] = useState("All domains");
  const [view, setView] = useState("rows");
  const [selectedId, setSelectedId] = useState("ATTR-BP-TAX-NUMBER");
  const [detailTab, setDetailTab] = useState("Summary");

  const rows = useMemo(
    () =>
      LEDGER_ROWS.filter((row) => {
        const matchesQuery = `${row.id} ${row.name} ${row.type} ${row.source}`
          .toLowerCase()
          .includes(query.toLowerCase());
        return matchesQuery && (type === "All types" || row.type === type);
      }),
    [query, type],
  );
  const selected = LEDGER_ROWS.find((row) => row.id === selectedId) || LEDGER_ROWS[0];
  const openRow = (row) =>
    navigate(
      row.type === "Gap" ? "gaps" : row.type === "Proposal" ? "proposal" : "object",
      row.type === "Gap"
        ? { gap: 1 }
        : row.type === "Proposal"
          ? { id: 27 }
          : { id: row.id === "ATTR-BP-TAX-NUMBER" ? "DOMAIN-CUSTOMER-BP" : row.id },
    );
  const openSelected = () => openRow(selected);

  useEffect(() => {
    const onKey = (event) => {
      const target = event.target;
      const isTyping =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement ||
        target?.isContentEditable;
      if (event.key === "Enter" && !isTyping && !event.metaKey && !event.ctrlKey && !event.altKey) {
        event.preventDefault();
        openSelected();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectedId, navigate]);

  return (
    <div className="ledger-page">
      <div className="ledger-main">
        <header className="ledger-heading">
          <div>
            <span className="eyebrow">Customer migration / canonical model</span>
            <h1>Canonical model ledger</h1>
            <p><CheckCircle size={14} weight="fill" /> Validation complete <i /> Index updated 2m ago <i /> 24 objects</p>
          </div>
          <div className="ledger-heading-actions">
            <select value={domain} onChange={(event) => setDomain(event.target.value)} aria-label="Domain">
              <option>All domains</option><option>Customer</option><option>Sales</option>
            </select>
            <button className="secondary-button" onClick={() => setType(type === "All types" ? "Attribute" : "All types")}>
              <Funnel size={16} /> Filters
            </button>
            <div className="view-toggle">
              <button className={view === "rows" ? "is-active" : ""} onClick={() => setView("rows")} aria-label="Row view"><Rows size={16} /></button>
              <button className={view === "grid" ? "is-active" : ""} onClick={() => setView("grid")} aria-label="Grid view"><GridFour size={16} /></button>
            </div>
          </div>
        </header>
        <div className="ledger-tools">
          <label>
            <MagnifyingGlass size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter ledger by ID, name, source, or type" />
            <kbd>/</kbd>
          </label>
          <select value={type} onChange={(event) => setType(event.target.value)} aria-label="Object type">
            <option>All types</option>
            {Object.keys(TYPE_ICONS).map((item) => <option key={item}>{item}</option>)}
          </select>
        </div>
        <section className={`ledger-table ${view === "grid" ? "is-grid" : ""}`} aria-label="Canonical model objects">
          <div className="ledger-table-head">
            <span>ID / name</span><span>Type</span><span>Source</span><span>Validation</span>
            <span>Evidence</span><span>Impact</span><span>Owner</span><span>Updated</span>
          </div>
          {rows.length ? rows.map((row) => {
            const Icon = TYPE_ICONS[row.type] || Database;
            return (
              <button
                key={row.id}
                className={`ledger-row ${selectedId === row.id ? "is-selected" : ""}`}
                onClick={() => { setSelectedId(row.id); setDetailTab("Summary"); }}
                onDoubleClick={() => openRow(row)}
              >
                <span className="ledger-object"><span className={`ledger-type-icon tone-${row.tone}`}><Icon size={17} weight="duotone" /></span><span><code>{row.id}</code><strong>{row.name}</strong></span></span>
                <span>{row.type}</span><span>{row.source}</span><StatusBadge value={row.validation} />
                <span>{row.evidence}</span><StatusBadge value={row.impact} />
                <span className="ledger-owner"><i>{row.initials}</i>{row.owner}</span><span>{row.updated}</span>
              </button>
            );
          }) : (
            <div className="ledger-empty"><MagnifyingGlass size={24} /><strong>No ledger entries match</strong><button onClick={() => { setQuery(""); setType("All types"); }}>Clear filters</button></div>
          )}
        </section>
        <LedgerDetail row={selected} tab={detailTab} onTab={setDetailTab} navigate={navigate} />
      </div>
      <aside className="ledger-rail">
        <section>
          <div className="rail-heading"><h2>Import status</h2><button onClick={onImport}>Open</button></div>
          {[
            ["37 files parsed", "37/37", "ok"],
            ["24 objects detected", "24", "ok"],
            ["5 gaps identified", "5", "warn"],
            ["Validation complete", "", "ok"],
          ].map(([label, value, tone]) => (
            <p className={`import-stat ${tone}`} key={label}><CheckCircle size={15} /><span>{label}</span><strong>{value}</strong></p>
          ))}
          <button className="secondary-button full-width" onClick={onImport}><UploadSimple size={15} /> Load model</button>
        </section>
        <section>
          <div className="rail-heading"><h2>Shortcuts</h2><button onClick={onShortcuts}>All</button></div>
          {[
            ["Go to Models", ["G", "M"]],
            ["Go to Lineage", ["G", "L"]],
            ["Go to Gaps", ["G", "G"]],
            ["Go to Proposals", ["G", "P"]],
            ["Export current view", ["E"]],
            ["Import files", ["I"]],
          ].map(([label, keys]) => (
            <p className="shortcut-row" key={label}><span>{label}</span><span>{keys.map((key, index) => <kbd key={`${key}-${index}`}>{key}</kbd>)}</span></p>
          ))}
        </section>
        <section className="rail-safety">
          <ShieldCheck size={18} />
          <strong>Governed by design</strong>
          <p>AI proposes. Validators verify. Humans approve.</p>
          <button onClick={() => navigate("proposals")}>Review proposals <ArrowRight size={13} /></button>
        </section>
        <button className="rail-command" onClick={onCommands}><Command size={17} /> Open command palette <kbd>⌘K</kbd></button>
        <button className="rail-export" onClick={onExport}><DownloadSimple size={17} /> Export ledger</button>
      </aside>
    </div>
  );
}

export function ReportsScreen({ onExport }) {
  const reports = [
    ["Model index", "customer-migration-model-index-2026-07-03.csv", "2m ago", "24 objects"],
    ["Gap report", "customer-migration-gaps-2026-07-03.xlsx", "18m ago", "5 gaps"],
    ["Lineage snapshot", "business-partner-lineage-2026-07-03.json", "1h ago", "12 edges"],
    ["Evidence summary", "tax-number-evidence-2026-07-02.pdf", "1d ago", "27 items"],
  ];
  return (
    <div className="page-pad reports-page">
      <div className="page-header">
        <div><span className="eyebrow">Reports and exports</span><h1>Project outputs</h1><p>Build traceable artifacts from the current canonical model and generated index.</p></div>
        <button className="primary-button" onClick={onExport}><FileArrowDown size={17} /> New export</button>
      </div>
      <div className="report-options">
        {EXPORT_TYPES.map(([id, name, description]) => (
          <button key={id} onClick={() => onExport(id)}>
            <span><FileText size={20} /></span><strong>{name}</strong><p>{description}</p><small>Configure export <ArrowRight size={13} /></small>
          </button>
        ))}
      </div>
      <section className="surface recent-exports">
        <div className="section-title"><div><h2>Recent outputs</h2><p>Generated locally from rebuildable repository data</p></div></div>
        {reports.map(([name, file, time, meta]) => (
          <button key={file} onClick={() => onExport(name.toLowerCase().split(" ")[0])}>
            <FileArrowDown size={18} /><span><strong>{name}</strong><code>{file}</code></span><small>{meta}</small><time>{time}</time><ArrowRight size={15} />
          </button>
        ))}
      </section>
    </div>
  );
}

export function ChangelogScreen() {
  const releases = [
    {
      date: "July 14, 2026",
      label: "0.5.0",
      title: "Model Ledger workbench",
      summary:
        "A backend-first model registry now has a focused local workbench for investigating canonical knowledge and governing changes.",
      groups: [
        ["Added", [
          "Canonical model ledger with search, validation, evidence, impact, ownership, and object detail.",
          "Guided imports, configurable exports, reports, workspace settings, command palette, and shortcuts.",
          "Expanded lineage, gap triage, and proposal review with source and decision context.",
        ]],
        ["Changed", [
          "Licensed current source and future releases under Apache License 2.0.",
          "Workspace home now prioritizes active model work over a chat-first surface.",
          "Deterministic validation and human approval are explicit throughout proposal workflows.",
        ]],
        ["Validated", [
          "Frontend tests and production build.",
          "Full Python test suite, Ruff checks, and browser interaction QA.",
        ]],
      ],
    },
    {
      date: "June 23, 2026",
      label: "0.4.1",
      title: "Public source release",
      summary:
        "Release metadata, documentation, command references, and local integration guidance were aligned for the safe patch release.",
      groups: [
        ["Highlights", [
          "Published martenweave-core 0.4.1 through the release workflow.",
          "Kept CLI command documentation and package version references consistent.",
          "Clarified that API and MCP processes are local integration surfaces.",
        ]],
      ],
    },
  ];
  return (
    <div className="page-pad changelog-page">
      <div className="page-header">
        <div><span className="eyebrow">Product updates</span><h1>Changelog</h1><p>Notable changes to the local Model Ledger workbench and Martenweave Core.</p></div>
        <span className="changelog-source"><ClockCounterClockwise size={17} /> Synced with CHANGELOG.md</span>
      </div>
      <div className="changelog-list">
        {releases.map((release) => (
          <article className="surface changelog-release" key={release.label}>
            <aside><time>{release.date}</time><span>{release.label}</span></aside>
            <div>
              <h2>{release.title}</h2>
              <p>{release.summary}</p>
              <div className="changelog-groups">
                {release.groups.map(([name, items]) => (
                  <section key={name}>
                    <h3>{name}</h3>
                    <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
                  </section>
                ))}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export function SettingsScreen({ onToast, onShortcuts }) {
  const [strictValidation, setStrictValidation] = useState(true);
  const [blockInvalid, setBlockInvalid] = useState(true);
  const [includeAudit, setIncludeAudit] = useState(true);
  return (
    <div className="page-pad settings-page">
      <div className="page-header">
        <div><span className="eyebrow">Workspace settings</span><h1>Local repository behavior</h1><p>Control validation and generated outputs without adding cloud dependencies.</p></div>
        <button className="primary-button" onClick={() => onToast("Workspace settings saved locally.")}><Check size={17} /> Save changes</button>
      </div>
      <div className="settings-layout">
        <section className="surface">
          <div className="section-title"><div><h2>Repository</h2><p>Canonical truth and rebuildable output locations</p></div><span className="status-dot" /></div>
          <dl>
            <dt>Workspace</dt><dd>Customer migration</dd>
            <dt>Canonical model</dt><dd><code>examples/customer_bp_model/model</code></dd>
            <dt>Generated index</dt><dd><code>examples/customer_bp_model/generated/modelops.db</code></dd>
            <dt>Configuration</dt><dd><code>modelops.config.yaml</code></dd>
          </dl>
        </section>
        <section className="surface">
          <div className="section-title"><div><h2>Validation safeguards</h2><p>Deterministic checks always run before indexing</p></div></div>
          {[
            ["Strict validation", "Run object, reference, and SAP context checks.", strictValidation, setStrictValidation],
            ["Block invalid objects", "Keep invalid canonical objects out of the generated index.", blockInvalid, setBlockInvalid],
            ["Include audit events", "Attach local generation and review metadata to exports.", includeAudit, setIncludeAudit],
          ].map(([label, description, checked, setChecked]) => (
            <label className="setting-toggle" key={label}><span><strong>{label}</strong><small>{description}</small></span><input type="checkbox" checked={checked} onChange={(event) => setChecked(event.target.checked)} /></label>
          ))}
        </section>
        <section className="surface">
          <div className="section-title"><div><h2>Integration surfaces</h2><p>Local processes using the same core services</p></div></div>
          {[
            ["CLI", "modelops validate · build-index · impact", "Available"],
            ["Local API", "127.0.0.1 only", "Ready"],
            ["MCP server", "Tool surface for agent workflows", "Ready"],
          ].map(([name, description, status]) => <div className="integration-row" key={name}><span><strong>{name}</strong><small>{description}</small></span><span><i className="status-dot" />{status}</span></div>)}
        </section>
        <section className="surface shortcut-settings">
          <div className="section-title"><div><h2>Keyboard workflow</h2><p>Navigate investigations without leaving the keyboard</p></div></div>
          <p><kbd>⌘K</kbd><span>Command palette</span></p><p><kbd>/</kbd><span>Global search</span></p><p><kbd>I</kbd><span>Import model knowledge</span></p><p><kbd>E</kbd><span>Export current view</span></p>
          <button className="secondary-button full-width" onClick={onShortcuts}><Keyboard size={16} /> View all shortcuts</button>
        </section>
      </div>
    </div>
  );
}

function ModalFrame({ title, subtitle, onClose, children, className = "" }) {
  const closeRef = useRef(null);
  useEffect(() => closeRef.current?.focus(), []);
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section className={`workbench-modal ${className}`} role="dialog" aria-modal="true" aria-labelledby="modal-title" onMouseDown={(event) => event.stopPropagation()}>
        <header><div><h2 id="modal-title">{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button ref={closeRef} className="icon-button" aria-label="Close" onClick={onClose}><X size={18} /></button></header>
        {children}
      </section>
    </div>
  );
}

function ImportDialog({ onClose, onComplete }) {
  const [source, setSource] = useState("canonical");
  const [step, setStep] = useState("choose");
  const [error, setError] = useState("");

  const parse = () => {
    setError("");
    setStep("parsing");
    window.setTimeout(() => setStep("review"), 850);
  };
  return (
    <ModalFrame title="Load model knowledge" subtitle="Import project evidence without mutating canonical truth." onClose={onClose} className="import-modal">
      <div className="flow-steps"><span className="is-active">1 Source</span><span className={step !== "choose" ? "is-active" : ""}>2 Parse</span><span className={step === "review" ? "is-active" : ""}>3 Review</span></div>
      {step === "choose" && (
        <>
          <div className="source-grid">
            {SOURCE_TYPES.map(({ id, title, description, icon: Icon, files }) => (
              <button key={id} className={source === id ? "is-selected" : ""} onClick={() => setSource(id)}>
                <Icon size={20} /><span><strong>{title}</strong><small>{description}</small></span><em>{files}</em>
              </button>
            ))}
          </div>
          <div className="drop-zone">
            <UploadSimple size={26} />
            <strong>Drop files here or use realistic sample input</strong>
            <p>Files remain local. Martenweave profiles and validates before anything can become canonical.</p>
            <button className="secondary-button" onClick={() => setError("Demo mode uses the repository sample because browser file access is not persisted.")}>Choose files</button>
            {error && <span className="inline-error">{error}</span>}
          </div>
          <footer><button className="secondary-button" onClick={onClose}>Cancel</button><button className="primary-button" onClick={parse}>Use sample files <ArrowRight size={15} /></button></footer>
        </>
      )}
      {step === "parsing" && (
        <div className="parsing-state"><CircleNotch className="spin" size={30} /><h3>Parsing Customer migration inputs</h3><p>Reading frontmatter, profiling datasets, resolving references, and running deterministic validation…</p><div><span style={{ width: "72%" }} /></div></div>
      )}
      {step === "review" && (
        <>
          <div className="import-summary">
            <div><CheckCircle size={19} /><strong>37</strong><span>Files parsed</span></div>
            <div><Cube size={19} /><strong>24</strong><span>Objects detected</span></div>
            <div><Warning size={19} /><strong>5</strong><span>Gaps detected</span></div>
            <div><ShieldCheck size={19} /><strong>0</strong><span>Blocking errors</span></div>
          </div>
          <section className="parsed-preview">
            <h3>Detected model knowledge</h3>
            {[
              ["Canonical objects", "24", "Ready to index"],
              ["Field endpoints", "68", "7 new · 61 matched"],
              ["Mapping rows", "112", "3 need review"],
              ["Source evidence", "284", "Profiled locally"],
              ["Gap candidates", "5", "Human review required"],
            ].map(([name, count, status]) => <p key={name}><strong>{name}</strong><span>{count}</span><small>{status}</small></p>)}
          </section>
          <div className="import-warning"><ShieldCheck size={18} /><p><strong>No canonical files will be changed.</strong> This import updates the disposable investigation index and creates reviewable gap candidates.</p></div>
          <footer><button className="secondary-button" onClick={() => setStep("choose")}>Back</button><button className="primary-button" onClick={() => onComplete("Model loaded: 24 objects indexed and 5 gaps queued for review.")}>Load into workspace</button></footer>
        </>
      )}
    </ModalFrame>
  );
}

function ExportDialog({ initialType = "index", onClose, onComplete }) {
  const [type, setType] = useState(EXPORT_TYPES.some(([id]) => id === initialType) ? initialType : "index");
  const [format, setFormat] = useState("CSV");
  const [success, setSuccess] = useState(false);
  const selected = EXPORT_TYPES.find(([id]) => id === type) || EXPORT_TYPES[0];
  const extension = format.toLowerCase();
  const filename = `customer-migration-${type}-2026-07-03.${extension}`;

  const download = () => {
    const content = [
      "Martenweave local export",
      `Type: ${selected[1]}`,
      "Workspace: Customer migration",
      "Generated: 2026-07-03",
      "Canonical source remains unchanged.",
    ].join("\n");
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
    onComplete(`Exported ${filename}`);
  };

  return (
    <ModalFrame title="Export project output" subtitle="Generate a traceable local artifact from the current view." onClose={onClose} className="export-modal">
      {!success ? (
        <>
          <div className="export-list">
            {EXPORT_TYPES.map(([id, name, description]) => (
              <button key={id} className={type === id ? "is-selected" : ""} onClick={() => setType(id)}>
                <span>{type === id ? <Check size={15} weight="bold" /> : <FileText size={16} />}</span>
                <span><strong>{name}</strong><small>{description}</small></span>
              </button>
            ))}
          </div>
          <div className="export-config">
            <label><span>Format</span><select value={format} onChange={(event) => setFormat(event.target.value)}><option>CSV</option><option>JSON</option><option>PDF</option><option>XLSX</option></select></label>
            <label><span>File name</span><input value={filename} readOnly /></label>
          </div>
          <div className="export-note"><ShieldCheck size={17} /><span>Includes source IDs, validation timestamp, workspace scope, and generation metadata.</span></div>
          <footer><button className="secondary-button" onClick={onClose}>Cancel</button><button className="primary-button" onClick={() => setSuccess(true)}>Generate export</button></footer>
        </>
      ) : (
        <div className="export-success">
          <span><CheckCircle size={34} weight="fill" /></span><h3>{selected[1]} is ready</h3><p><code>{filename}</code></p>
          <div><strong>Customer migration</strong><small>Generated locally · Evidence timestamp included · 0 errors</small></div>
          <button className="primary-button" onClick={download}><DownloadSimple size={17} /> Download file</button>
          <button onClick={onClose}>Close</button>
        </div>
      )}
    </ModalFrame>
  );
}

function CommandPalette({ navigate, onImport, onExport, onShortcuts, onClose }) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef(null);
  const commands = [
    ["Search model objects", "Find canonical objects, fields, mappings, and endpoints", MagnifyingGlass, () => navigate("models")],
    ["Open import flow", "Load canonical files, datasets, mappings, or project evidence", UploadSimple, onImport],
    ["Export current report", "Generate a traceable local project output", DownloadSimple, onExport],
    ["Open gaps", "Review missing mappings and coverage issues", Warning, () => navigate("gaps")],
    ["Open lineage", "Trace systems, fields, datasets, and downstream impact", ShareNetwork, () => navigate("lineage")],
    ["Review proposals", "Inspect AI-assisted changes before approval", NotePencil, () => navigate("proposals")],
    ["Open Business Partner", "Inspect the canonical domain and source evidence", Cube, () => navigate("object", { id: "DOMAIN-CUSTOMER-BP" })],
    ["Workspace settings", "Review local repository, validation, and integration behavior", SlidersHorizontal, () => navigate("settings")],
    ["Show shortcuts", "View keyboard navigation and review commands", Keyboard, onShortcuts],
  ];
  const shown = commands.filter(([name, description]) => `${name} ${description}`.toLowerCase().includes(query.toLowerCase()));
  const run = (command) => { onClose(); command(); };
  useEffect(() => inputRef.current?.focus(), []);
  useEffect(() => setActiveIndex(0), [query]);
  useEffect(() => {
    const onKey = (event) => {
      if (!shown.length) return;
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActiveIndex((current) => (current + 1) % shown.length);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActiveIndex((current) => (current - 1 + shown.length) % shown.length);
      } else if (event.key === "Enter") {
        event.preventDefault();
        run(shown[activeIndex][3]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [activeIndex, shown]);
  return (
    <ModalFrame title="Command palette" subtitle="Move through model knowledge without leaving the keyboard." onClose={onClose} className="command-modal">
      <label className="command-search"><MagnifyingGlass size={19} /><input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search commands or model objects…" /><kbd>Esc</kbd></label>
      <div className="command-list">
        {shown.map(([name, description, Icon, action], index) => (
          <button key={name} className={activeIndex === index ? "is-active" : ""} onMouseEnter={() => setActiveIndex(index)} onClick={() => run(action)}><Icon size={19} /><span><strong>{name}</strong><small>{description}</small></span><kbd>{index + 1}</kbd></button>
        ))}
        {!shown.length && <div className="command-empty">No commands match “{query}”.</div>}
      </div>
      <footer><span><kbd>↑↓</kbd> Navigate</span><span><kbd>Enter</kbd> Open</span><span><kbd>⌘K</kbd> Toggle</span></footer>
    </ModalFrame>
  );
}

function ShortcutDialog({ onClose }) {
  const groups = [
    ["Navigation", [["G then M", "Go to Models"], ["G then L", "Go to Lineage"], ["G then G", "Go to Gaps"], ["G then P", "Go to Proposals"]]],
    ["Workspace", [["/", "Focus global search"], ["⌘/Ctrl K", "Open command palette"], ["I", "Open import flow"], ["E", "Export current view"]]],
    ["Review", [["Enter", "Open selected item"], ["⌘/Ctrl Enter", "Approve on proposal review"], ["Esc", "Close modal or panel"], ["?", "Show shortcut help"]]],
  ];
  return (
    <ModalFrame title="Keyboard shortcuts" subtitle="Fast navigation for model investigation and governed review." onClose={onClose} className="shortcut-modal">
      <div className="shortcut-groups">{groups.map(([title, items]) => <section key={title}><h3>{title}</h3>{items.map(([keys, label]) => <p key={keys}><kbd>{keys}</kbd><span>{label}</span></p>)}</section>)}</div>
      <footer><button className="primary-button" onClick={onClose}>Done</button></footer>
    </ModalFrame>
  );
}

function ActivityDialog({ onClose, navigate }) {
  return (
    <ModalFrame title="Workspace activity" subtitle="Recent local validation, evidence, and review events." onClose={onClose} className="activity-modal">
      <div className="activity-feed">{recentActivity.map(([action, subject, time], index) => <button key={action} onClick={() => { onClose(); navigate(index === 1 ? "proposal" : index === 2 ? "gaps" : index === 3 ? "lineage" : "home", index === 1 ? { id: 27 } : undefined); }}><span><CheckCircle size={17} /></span><span><strong>{action}</strong><small>{subject}</small></span><time>{time}</time><ArrowRight size={14} /></button>)}</div>
    </ModalFrame>
  );
}

function WorkspaceDialog({ onClose }) {
  const [environment, setEnvironment] = useState("Production");
  return (
    <ModalFrame title="Workspace" subtitle="Local repository context for this investigation." onClose={onClose} className="workspace-modal">
      <div className="workspace-summary"><img src="/martenweave-logo.png" alt="" /><span><strong>Customer migration</strong><small>examples/customer_bp_model</small></span><StatusBadge value="Validated" /></div>
      <dl className="workspace-details"><dt>Version</dt><dd>v2.4.1</dd><dt>Objects</dt><dd>24 canonical</dd><dt>Generated index</dt><dd>Fresh · 2m ago</dd><dt>Environment</dt><dd><select value={environment} onChange={(event) => setEnvironment(event.target.value)}><option>Production</option><option>Review</option><option>Draft</option></select></dd></dl>
      <div className="export-note"><ShieldCheck size={17} /> Changing the prototype environment does not mutate repository files.</div>
      <footer><button className="primary-button" onClick={onClose}>Apply workspace view</button></footer>
    </ModalFrame>
  );
}

function ProposalDraftDialog({ onClose, onComplete }) {
  const [note, setNote] = useState("Resolve missing EMAIL_ADDRESS mapping from Legacy CRM.");
  return (
    <ModalFrame title="Draft patch proposal" subtitle="Create a reviewable suggestion. Canonical truth remains unchanged." onClose={onClose} className="workspace-modal">
      <label className="proposal-draft-note"><span>Proposal intent</span><textarea rows={4} value={note} onChange={(event) => setNote(event.target.value)} /></label>
      <div className="export-note"><ShieldCheck size={17} /> The draft will run deterministic validation and impact analysis before review.</div>
      <footer><button className="secondary-button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={!note.trim()} onClick={() => onComplete("Draft proposal created and queued for deterministic validation.")}>Create draft</button></footer>
    </ModalFrame>
  );
}

export function WorkbenchOverlay({ overlay, onClose, navigate, onOpen, onToast }) {
  if (!overlay) return null;
  if (overlay.type === "import") return <ImportDialog onClose={onClose} onComplete={(message) => { onClose(); onToast(message); }} />;
  if (overlay.type === "export") return <ExportDialog initialType={overlay.exportType} onClose={onClose} onComplete={(message) => { onClose(); onToast(message); }} />;
  if (overlay.type === "commands") return <CommandPalette navigate={navigate} onImport={() => onOpen({ type: "import" })} onExport={() => onOpen({ type: "export" })} onShortcuts={() => onOpen({ type: "shortcuts" })} onClose={onClose} />;
  if (overlay.type === "shortcuts") return <ShortcutDialog onClose={onClose} />;
  if (overlay.type === "activity") return <ActivityDialog onClose={onClose} navigate={navigate} />;
  if (overlay.type === "workspace") return <WorkspaceDialog onClose={onClose} />;
  if (overlay.type === "proposal-draft") return <ProposalDraftDialog onClose={onClose} onComplete={(message) => { onClose(); onToast(message); }} />;
  return null;
}

export function Toast({ message, onClose }) {
  useEffect(() => {
    if (!message) return undefined;
    const timer = window.setTimeout(onClose, 3600);
    return () => window.clearTimeout(timer);
  }, [message, onClose]);
  if (!message) return null;
  return <div className="workbench-toast" role="status"><CheckCircle size={18} weight="fill" /><span>{message}</span><button aria-label="Dismiss" onClick={onClose}><X size={15} /></button></div>;
}

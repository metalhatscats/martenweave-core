import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Archive,
  ArrowRight,
  ArrowUp,
  Bell,
  BracketsCurly,
  Buildings,
  CaretDown,
  CaretLeft,
  CaretRight,
  ChatCircleText,
  Check,
  CheckCircle,
  CircleNotch,
  ClockCounterClockwise,
  Columns,
  Command,
  Copy,
  Cube,
  Database,
  DownloadSimple,
  DotsThreeVertical,
  Export,
  FileArrowDown,
  FileText,
  Funnel,
  GitBranch,
  GitDiff,
  House,
  Info,
  List,
  MagnifyingGlass,
  NotePencil,
  Plus,
  SealCheck,
  ShareNetwork,
  ShieldCheck,
  SidebarSimple,
  SlidersHorizontal,
  Sparkle,
  Stack,
  Tag,
  UploadSimple,
  UserCircle,
  Users,
  Warning,
  WarningCircle,
  X,
  XCircle,
} from "@phosphor-icons/react";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  API_STATE,
  ApiProvider,
  objectTypeToTone,
  useApi,
  useAssessmentFindings,
  useFindingReview,
  useImportPreview,
  useImportProfile,
  useLineage,
  useObjectDetail,
  useObjectSearch,
  useProposalApply,
  useProposalDetail,
  useProposalDiff,
  useProposalDryRun,
  useProposalReview,
  useProposalValidate,
  useProposals,
  useWorkspaceActivity,
} from "./api.jsx";
import {
  fields,
  gaps,
  lineageEdges,
  lineageNodes,
  modelObjects,
  proposals,
  severityWeight,
} from "./data.js";
import {
  ChangelogScreen,
  ReportsScreen,
  SettingsScreen,
  Toast,
  WorkbenchOverlay,
  WorkspaceScreen,
} from "./workbench.jsx";

function ConnectionBanner() {
  const { state, demo, error, recovery, retry } = useApi();
  if (state === API_STATE.CONNECTED) return null;

  const messages = {
    [API_STATE.UNKNOWN]: "Connecting to local Martenweave API…",
    [API_STATE.UNAVAILABLE]: `Local API unavailable. Showing demo data. ${error || ""}`,
    [API_STATE.STALE_INDEX]: "Local API index is stale. Run build-index, or continue in demo mode.",
    [API_STATE.INCOMPATIBLE]: `Local API contract is incompatible. ${error || ""}`,
  };

  return (
    <div className="connection-banner" role="status">
      <span className={`connection-dot connection-${state}`} />
      <span>{messages[state] || "Waiting for local API…"}</span>
      {recovery && (
        <span className="connection-recovery">
          Next: {recovery.label}{recovery.command ? ` (${recovery.command})` : ""}
        </span>
      )}
      {demo && <span className="connection-demo">Demo mode</span>}
      {state !== API_STATE.UNKNOWN && retry && (
        <button className="connection-retry" onClick={retry}>Retry connection</button>
      )}
    </div>
  );
}

const NAV_ITEMS = [
  { id: "home", label: "Workspace", icon: House },
  { id: "models", label: "Models", icon: Cube },
  { id: "lineage", label: "Lineage", icon: ShareNetwork },
  { id: "gaps", label: "Gaps", icon: Warning },
  { id: "proposals", label: "Proposals", icon: NotePencil },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "changelog", label: "Changelog", icon: ClockCounterClockwise },
  { id: "settings", label: "Settings", icon: SlidersHorizontal },
];

const ROUTE_TITLES = {
  home: "Canonical model ledger",
  models: "Global model search",
  object: "Business Partner",
  lineage: "Lineage",
  gaps: "Open gaps",
  proposals: "Proposals",
  proposal: "Proposal review",
  reports: "Reports and exports",
  changelog: "Changelog",
  settings: "Workspace settings",
};

function useRoute() {
  const getRoute = () => window.location.hash.replace("#/", "").split("?")[0] || "home";
  const getParams = () => {
    const hash = window.location.hash;
    const idx = hash.indexOf("?");
    return idx === -1 ? new URLSearchParams() : new URLSearchParams(hash.slice(idx + 1));
  };
  const [route, setRoute] = useState(getRoute);
  const [params, setParams] = useState(getParams);

  useEffect(() => {
    const onHashChange = () => {
      setRoute(getRoute());
      setParams(getParams());
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigate = useCallback((next, search) => {
    const query = typeof search === "string" ? search : new URLSearchParams(search).toString();
    window.location.hash = query ? `/${next}?${query}` : `/${next}`;
  }, []);

  return [route, params, navigate];
}

function DisabledButton({ className, icon: Icon, label, reason, children }) {
  return (
    <button
      type="button"
      className={className}
      disabled
      title={reason}
      aria-label={`${label} — ${reason}`}
    >
      {Icon && <Icon size={17} />}
      {children}
    </button>
  );
}

function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <img src="/martenweave-logo.png" alt="" />
      </span>
      <span className="brand-copy">
        <strong>Martenweave</strong>
        <small>Model intelligence</small>
      </span>
    </div>
  );
}

function Sidebar({ route, navigate, open, onClose, onWorkspace }) {
  const { capabilities, demo } = useApi();
  const activeRoute = route === "object" ? "models" : route === "proposal" ? "proposals" : route;
  const workspaceLabel = demo ? "Demo workspace" : "Local workspace";
  const workspaceDetail = demo
    ? "API unavailable · sample data"
    : `Core ${capabilities?.version || "—"} · ${capabilities?.read_only ? "read-only" : "local"}`;
  return (
    <>
      {open && <button className="mobile-scrim" aria-label="Close navigation" onClick={onClose} />}
      <aside className={`sidebar ${open ? "is-open" : ""}`}>
        <div>
          <Brand />
          <nav aria-label="Primary navigation">
            {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
              <button
                type="button"
                className={`nav-item ${activeRoute === id ? "is-active" : ""}`}
                key={id}
                onClick={() => {
                  navigate(id);
                  onClose();
                }}
              >
                <Icon size={20} weight={activeRoute === id ? "fill" : "regular"} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>
        <button className="repo-switcher" type="button" onClick={onWorkspace}>
          <span className="status-dot" />
          <span>
            <strong>{workspaceLabel}</strong>
            <small>{workspaceDetail}</small>
          </span>
          <CaretRight size={14} />
        </button>
      </aside>
    </>
  );
}

function Topbar({ route, navigate, title, onMenu, actions }) {
  const { capabilities, demo, state } = useApi();
  const [searchOpen, setSearchOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [query, setQuery] = useState("");
  const profileRef = useRef(null);
  const workspaceLabel = demo ? "Demo workspace" : "Local workspace";
  const connectionLabel = demo
    ? "Demo mode"
    : capabilities?.read_only
      ? "Read-only"
      : state === API_STATE.CONNECTED
        ? "Local API"
        : "Connecting";
  const writeBlocked = Boolean(capabilities?.read_only) || state === API_STATE.STALE_INDEX;
  const writeBlockReason = capabilities?.read_only
    ? "This local workspace is read-only"
    : "Build the disposable local index before this action";

  useEffect(() => {
    if (!profileOpen) return;
    const onClick = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    };
    const onKey = (event) => {
      if (event.key === "Escape") setProfileOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [profileOpen]);

  const submit = (event) => {
    event.preventDefault();
    const search = query.trim() ? `search=${encodeURIComponent(query.trim())}` : "";
    navigate("models", search);
    setSearchOpen(false);
    setQuery("");
  };

  return (
    <header className="topbar">
      <div className="topbar-leading">
        <button className="icon-button mobile-menu" onClick={onMenu} aria-label="Open navigation">
          <SidebarSimple size={21} />
        </button>
        <div className="breadcrumb">
          <span>{workspaceLabel}</span>
          <CaretRight size={13} />
          <strong>{title || ROUTE_TITLES[route] || "Workspace"}</strong>
        </div>
      </div>
      <div className="topbar-actions">
        <form className={`top-search global-top-search ${searchOpen ? "is-open" : ""}`} onSubmit={submit}>
          <MagnifyingGlass size={18} />
          <input
            data-global-search
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search models, fields, lineage, gaps…"
            aria-label="Search model"
            onFocus={() => setSearchOpen(true)}
          />
          {!searchOpen && <kbd>/</kbd>}
          {searchOpen && (
            <button type="button" aria-label="Close search" onClick={() => setSearchOpen(false)}>
              <X size={16} />
            </button>
          )}
        </form>
        <button className="top-action-button" onClick={() => actions.open({ type: "commands" })}>
          <Command size={17} /> Commands <kbd>⌘K</kbd>
        </button>
        {writeBlocked ? (
          <DisabledButton className="top-action-button" icon={UploadSimple} label="Import" reason={writeBlockReason}>Import</DisabledButton>
        ) : (
          <button className="top-action-button" onClick={() => actions.open({ type: "import" })}>
            <UploadSimple size={17} /> Import
          </button>
        )}
        {writeBlocked ? (
          <DisabledButton className="top-action-button" icon={DownloadSimple} label="Export" reason={writeBlockReason}>Export</DisabledButton>
        ) : (
          <button className="top-action-button" onClick={() => actions.open({ type: "export" })}>
            <DownloadSimple size={17} /> Export
          </button>
        )}
        <span className="environment-pill">
          <span className="status-dot" />
          {connectionLabel}
        </span>
        <button className="icon-button notification-button" onClick={() => actions.open({ type: "activity" })} aria-label="Workspace activity">
          <Bell size={17} /><span />
        </button>
        <div className="profile-wrap" ref={profileRef}>
          <button className="profile-button" onClick={() => setProfileOpen((value) => !value)}>
            <span className="avatar">MW</span>
            <span className="profile-copy">
              <strong>{workspaceLabel}</strong>
              <small>{demo ? "Sample data" : "No user identity"}</small>
            </span>
            <CaretDown size={14} />
          </button>
          {profileOpen && (
            <div className="profile-menu">
              <button onClick={() => { setProfileOpen(false); actions.open({ type: "workspace" }); }}><UserCircle size={17} /> Workspace status</button>
              <button onClick={() => { setProfileOpen(false); actions.open({ type: "shortcuts" }); }}><SlidersHorizontal size={17} /> Keyboard shortcuts</button>
              <button onClick={() => { setProfileOpen(false); actions.open({ type: "workspace" }); }}><Archive size={17} /> Repository context</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

function AppShell({ route, navigate, title, actions, children }) {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  return (
    <div className="app-shell">
      <Sidebar
        route={route}
        navigate={navigate}
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        onWorkspace={() => actions.open({ type: "workspace" })}
      />
      <div className="app-stage">
        <Topbar route={route} navigate={navigate} title={title} onMenu={() => setMenuOpen(true)} actions={actions} />
        <main className={`app-main route-${route}`}>{children}</main>
      </div>
    </div>
  );
}

function PageHeader({ eyebrow, title, description, actions }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}

function Badge({ children, tone = "neutral" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function IconTile({ type, size = 42 }) {
  const map = {
    Domain: [Cube, "blue"],
    Attribute: [BracketsCurly, "violet"],
    Entity: [Buildings, "cyan"],
    Mapping: [ShareNetwork, "orange"],
    Proposal: [FileText, "violet"],
  };
  const [Icon, tone] = map[type] || [Database, "green"];
  return (
    <span className={`icon-tile icon-tile-${tone}`} style={{ width: size, height: size }}>
      <Icon size={Math.round(size * 0.48)} weight="duotone" />
    </span>
  );
}

function updatedMinutes(value) {
  if (!value) return Infinity;
  const match = value.match(/^(\d+)([mhd])\s+ago$/);
  if (!match) return Infinity;
  const n = parseInt(match[1], 10);
  const unit = match[2];
  return unit === "m" ? n : unit === "h" ? n * 60 : n * 1440;
}

function capitalize(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function getHashSearchParam() {
  const hash = window.location.hash;
  const queryIndex = hash.indexOf("?");
  if (queryIndex === -1) return "";
  return new URLSearchParams(hash.slice(queryIndex + 1)).get("search") || "";
}

function ModelsScreen({ navigate, params }) {
  const [query, setQuery] = useState(() => getHashSearchParam() || "business partner");
  const [activeTab, setActiveTab] = useState("All");
  const [sort, setSort] = useState("Relevance");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedStatuses, setSelectedStatuses] = useState([]);
  const searchRef = useRef(null);

  useEffect(() => {
    setQuery(params.get("search") || "business partner");
  }, [params]);
  const tabs = ["All", "Objects", "Fields", "Mappings", "Proposals"];
  const typeFilters = ["Domain", "Attribute", "Entity", "Mapping", "Proposal"];
  const statusFilters = ["Validated", "In review", "Draft"];

  const { results: sortedResults, loading, error } = useObjectSearch(
    query,
    activeTab,
    selectedTypes,
    selectedStatuses,
    sort
  );

  return (
    <div className="page-pad search-page">
      <PageHeader
        title="Global model search"
        description="Search across canonical objects, fields, mappings, datasets, and proposals."
      />
      <form
        className="global-search"
        onSubmit={(event) => {
          event.preventDefault();
          if (!query.trim()) searchRef.current?.focus();
        }}
      >
        <MagnifyingGlass size={21} />
        <input ref={searchRef} value={query} onChange={(event) => setQuery(event.target.value)} />
        {query && <button type="button" onClick={() => setQuery("")}><X size={17} /></button>}
        <button type="submit" className="search-submit"><ArrowUp size={18} weight="bold" /></button>
      </form>
      <div className="search-tabs">
        {tabs.map((tab) => (
          <button
            className={activeTab === tab ? "is-active" : ""}
            key={tab}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
            <span>
              {tab === "All"
                ? modelObjects.length
                : tab === "Objects"
                  ? modelObjects.filter((item) => ["Domain", "Entity"].includes(item.label)).length
                  : tab === "Fields"
                    ? modelObjects.filter((item) => item.label === "Attribute").length
                    : tab === "Mappings"
                      ? modelObjects.filter((item) => item.label === "Mapping").length
                      : modelObjects.filter((item) => item.label === "Proposal").length}
            </span>
          </button>
        ))}
      </div>
      <section className="ai-summary">
        <span className="assistant-mark"><MagnifyingGlass size={17} weight="bold" /></span>
        <div>
          <span className="summary-title">Canonical search <Badge tone="blue">Local evidence</Badge></span>
          <p>
            Results come from the local index when available. Open an object to inspect its
            canonical definition, relationships, validation evidence, and governed change history.
          </p>
        </div>
      </section>
      <div className="results-toolbar">
        <strong>{sortedResults.length} results</strong>
        <div>
          <label>
            Sorted by
            <select value={sort} onChange={(event) => setSort(event.target.value)}>
              <option>Relevance</option>
              <option>Recently updated</option>
              <option>Name</option>
            </select>
          </label>
          <button
            className={`filter-toggle ${filtersOpen ? "is-active" : ""}`}
            onClick={() => setFiltersOpen((value) => !value)}
          >
            <SlidersHorizontal size={17} /> Filters
          </button>
        </div>
      </div>
      <div className={`search-results-layout ${filtersOpen ? "with-filters" : ""}`}>
        <section className="result-list">
          {loading && <div className="empty-state"><CircleNotch className="spin" size={24} /> Loading results…</div>}
          {error && <div className="empty-state"><WarningCircle size={24} /> {error}</div>}
          {!loading && sortedResults.length ? sortedResults.map((item) => (
            <button
              className="result-row"
              key={item.id}
              onClick={() => navigate(item.label === "Proposal" ? "proposal" : "object", { id: item.proposalId || item.id })}
            >
              <IconTile type={item.label} />
              <span className="result-copy">
                <span className="result-name"><Badge tone={item.label.toLowerCase()}>{item.label}</Badge><strong>{item.name}</strong></span>
                <span className="result-description">{item.description}</span>
                <span className="result-meta">
                  <span><Users size={14} /> {item.owners} owners</span>
                  <span><Database size={14} /> {item.systems.length} systems</span>
                  <span><CheckCircle size={14} /> {item.status}</span>
                </span>
              </span>
              <span className="result-updated">Updated {item.updated}</span>
              <CaretRight size={18} />
            </button>
          )) : (
            <div className="empty-state">
              <MagnifyingGlass size={30} />
              <h3>No model objects found</h3>
              <p>Try a broader query or clear the active filters.</p>
              <button onClick={() => { setQuery(""); setSelectedTypes([]); setSelectedStatuses([]); }}>Clear search</button>
            </div>
          )}
        </section>
        {filtersOpen && (
          <aside className="filters-panel">
            <div className="filters-heading">
              <strong>Quick filters</strong>
              <button onClick={() => { setSelectedTypes([]); setSelectedStatuses([]); }}>Clear all</button>
            </div>
            <fieldset>
              <legend>Object type</legend>
              {typeFilters.map((type) => (
                <label key={type}>
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type)}
                    onChange={() =>
                      setSelectedTypes((current) =>
                        current.includes(type)
                          ? current.filter((item) => item !== type)
                          : [...current, type],
                      )
                    }
                  />
                  <span>{type}</span>
                  <small>{modelObjects.filter((item) => item.label === type).length}</small>
                </label>
              ))}
            </fieldset>
            <fieldset>
              <legend>Status</legend>
              {statusFilters.map((statusOption) => (
                <label key={statusOption}>
                  <input
                    type="checkbox"
                    checked={selectedStatuses.includes(statusOption)}
                    onChange={() =>
                      setSelectedStatuses((current) =>
                        current.includes(statusOption)
                          ? current.filter((item) => item !== statusOption)
                          : [...current, statusOption],
                      )
                    }
                  />
                  <span>{statusOption}</span>
                  <small>{modelObjects.filter((item) => item.status === statusOption).length}</small>
                </label>
              ))}
            </fieldset>
          </aside>
        )}
      </div>
    </div>
  );
}

const OBJECT_TYPE_LABELS = {
  Domain: "Master data domain",
  Attribute: "Attribute",
  Entity: "Business entity",
  Mapping: "Mapping",
  Proposal: "Proposal",
};

function ObjectScreen({ navigate, params, onExport, onDraft }) {
  const [tab, setTab] = useState("Overview");
  const [copied, setCopied] = useState(false);
  const tabs = ["Overview", "Fields", "Evidence", "Relationships", "Impact", "Governance"];
  const objectId = params.get("id");
  const { object: liveObject, loading, error } = useObjectDetail(objectId);
  const object = liveObject || modelObjects[0];
  const copyId = async () => {
    await navigator.clipboard?.writeText(object.id);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="page-pad object-page">
      <button className="back-link" onClick={() => navigate("models")}>
        <CaretLeft size={15} /> Back to search
      </button>
      {loading && <div className="empty-state"><CircleNotch className="spin" size={24} /> Loading object…</div>}
      {error && <div className="empty-state"><WarningCircle size={24} /> {error}</div>}
      <div className="object-hero">
        <div className="object-identity">
          <IconTile type={object.label} size={58} />
          <div>
            <div className="object-type-row">
              <Badge tone={object.label.toLowerCase()}>{OBJECT_TYPE_LABELS[object.label] || object.label}</Badge>
              <Badge tone="green"><CheckCircle size={13} /> {object.status}</Badge>
            </div>
            <h1>{object.name}</h1>
            <button className="copy-id" onClick={copyId}>
              {object.id} {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>
        <div className="page-actions">
          <button className="secondary-button" onClick={() => onExport("evidence")}>
            <Export size={17} /> Export
          </button>
          <button className="primary-button" onClick={() => navigate("lineage")}>
            <ShareNetwork size={17} /> Trace lineage
          </button>
          <button className="icon-button bordered" onClick={onDraft} aria-label="Draft patch proposal">
            <DotsThreeVertical size={17} />
          </button>
        </div>
      </div>
      <p className="object-lead">{object.fullDescription}</p>
      <div className="object-tabs">
        {tabs.map((item) => (
          <button className={tab === item ? "is-active" : ""} key={item} onClick={() => setTab(item)}>
            {item}
            {item === "Fields" && <span>{fields.length}</span>}
          </button>
        ))}
      </div>

      {tab === "Overview" && <ObjectOverview navigate={navigate} object={object} onViewFields={() => setTab("Fields")} />}
      {tab === "Fields" && <FieldsTable />}
      {tab === "Evidence" && <ObjectEvidencePanel />}
      {tab === "Relationships" && <Relationships navigate={navigate} />}
      {tab === "Impact" && <ObjectImpactPanel navigate={navigate} />}
      {tab === "Governance" && <GovernancePanel />}
    </div>
  );
}

function ObjectOverview({ navigate, object, onViewFields }) {
  return (
    <div className="object-grid">
      <div className="object-main-column">
        <section className="surface overview-section">
          <div className="section-title"><div><h2>Model overview</h2><p>Canonical scope and operating context</p></div></div>
          <div className="definition-grid">
            <div><small>Business owner</small><strong>{object.businessOwner}</strong></div>
            <div><small>Technical steward</small><strong>{object.technicalSteward}</strong></div>
            <div><small>Lifecycle</small><strong>{object.lifecycle}</strong></div>
            <div><small>Last validated</small><strong>{object.lastValidated}</strong></div>
          </div>
          <div className="narrative-block">
            <h3>Business definition</h3>
            <p>{object.fullDescription}</p>
          </div>
          <div className="tag-row">
            <Tag size={16} />
            {object.tags.map((tag) => <Badge key={tag}>{tag}</Badge>)}
          </div>
        </section>
        <section className="surface">
          <div className="section-title">
            <div><h2>Key fields</h2><p>Frequently referenced canonical attributes</p></div>
            <button onClick={onViewFields}>View all {fields.length} <ArrowRight size={14} /></button>
          </div>
          <div className="compact-field-list">
            {fields.slice(0, 4).map((field) => (
              <div key={field.id}>
                <span className="field-glyph">Aa</span>
                <span><strong>{field.name}</strong><small>{field.description}</small></span>
                <code>{field.type}</code>
                <Badge tone={field.status === "Gap" ? "high" : "green"}>{field.status}</Badge>
              </div>
            ))}
          </div>
        </section>
      </div>
      <aside className="object-side-column">
        <section className="surface health-card">
          <div className="section-title"><div><h2>Model health</h2><p>Deterministic validation</p></div></div>
          <div className="health-score">
            <strong>{object.health}%</strong>
            <span>{object.status}</span>
          </div>
          <div className="progress-track"><span style={{ width: `${object.health}%` }} /></div>
          <ul>
            <li><CheckCircle size={17} /> {object.label} health <strong>{object.health}%</strong></li>
            <li><WarningCircle size={17} /> Open field gaps <strong>Review</strong></li>
            <li><ShieldCheck size={17} /> Ownership coverage <strong>{object.owners * 32}%</strong></li>
          </ul>
          <button className="secondary-button full-width" onClick={() => navigate("gaps")}>
            Review open gaps
          </button>
        </section>
        <section className="surface">
          <div className="section-title"><div><h2>Connected systems</h2><p>{object.systems.length} upstream and downstream</p></div></div>
          {object.systems.map((system, index) => (
            <button className="system-row" key={system} onClick={() => navigate("lineage")}>
              <span className={`system-icon system-${index}`}><Database size={17} /></span>
              <span><strong>{system}</strong><small>{index < 2 ? "Source" : "Target"}</small></span>
              <CaretRight size={14} />
            </button>
          ))}
        </section>
      </aside>
    </div>
  );
}

function FieldsTable() {
  const [query, setQuery] = useState("");
  const shown = fields.filter((field) => field.name.toLowerCase().includes(query.toLowerCase()));
  return (
    <section className="surface fields-surface">
      <div className="section-title">
        <div><h2>Canonical fields</h2><p>Semantic attributes defined by this model</p></div>
        <label className="inline-search"><MagnifyingGlass size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter fields" /></label>
      </div>
      <div className="data-table">
        <div className="data-table-head"><span>Field</span><span>Type</span><span>Required</span><span>Usage</span><span>Status</span></div>
        {shown.map((field) => (
          <div className="data-table-row" key={field.id}>
            <span><strong>{field.name}</strong><small>{field.id}</small></span>
            <code>{field.type}</code>
            <span>{field.required ? "Required" : "Optional"}</span>
            <span>{field.usage}</span>
            <Badge tone={field.status === "Gap" ? "high" : field.status === "In review" ? "violet" : "green"}>{field.status}</Badge>
          </div>
        ))}
      </div>
    </section>
  );
}

function ObjectEvidencePanel() {
  return (
    <div className="object-evidence-grid">
      <section className="surface">
        <div className="section-title"><div><h2>Source evidence</h2><p>Traceable project inputs supporting this object</p></div><Badge tone="green">27 items</Badge></div>
        {[
          ["SAP S/4HANA profile", "KNVV.STCD1", "158,932 distinct · 2.1% null"],
          ["Canonical definition", "ATTR-BP-TAX-NUMBER", "String(20) · optional"],
          ["Migration decision", "DEC-BP-004", "Preserve source tax identifiers"],
          ["Validation run", "VAL-2026-07-03-1018", "4 passed · 1 warning"],
        ].map(([source, id, detail]) => (
          <div className="evidence-row" key={id}><Database size={17} /><span><strong>{source}</strong><code>{id}</code></span><small>{detail}</small><Badge tone="green">Verified</Badge></div>
        ))}
      </section>
      <section className="surface">
        <div className="section-title"><div><h2>Dataset coverage</h2><p>Observed presence across loaded extracts</p></div></div>
        {[
          ["SAP Business Partner", 98],
          ["Legacy CRM customer", 86],
          ["Customer analytics", 91],
          ["MDM golden record", 73],
        ].map(([name, value]) => (
          <div className="coverage-row" key={name}><span>{name}<strong>{value}%</strong></span><i><b style={{ width: `${value}%` }} /></i></div>
        ))}
        <div className="validation-rule-list">
          <h3>Validation rules</h3>
          {["ID uniqueness", "Reference integrity", "SAP context grain", "Required ownership"].map((rule) => (
            <p key={rule}><CheckCircle size={15} /> {rule}<strong>Passed</strong></p>
          ))}
        </div>
      </section>
    </div>
  );
}

function ObjectImpactPanel({ navigate }) {
  return (
    <div className="impact-panel">
      <section className="impact-grid">
        {[["Direct mappings", "3", GitBranch], ["Field endpoints", "4", Database], ["Downstream reports", "2", FileText], ["Open proposals", "1", NotePencil]].map(([label, value, Icon]) => (
          <button className="surface" key={label} onClick={() => navigate(label === "Open proposals" ? "proposals" : "lineage")}><Icon size={20} /><strong>{value}</strong><span>{label}</span></button>
        ))}
      </section>
      <section className="surface impact-paths">
        <div className="section-title"><div><h2>Downstream impact</h2><p>Deterministic traversal from the selected canonical object</p></div><button onClick={() => navigate("lineage")}>Open lineage <ArrowRight size={14} /></button></div>
        <div><span>SAP S/4HANA</span><ArrowRight size={15} /><span>KNVV.STCD1</span><ArrowRight size={15} /><span>TAX_NUMBER</span><ArrowRight size={15} /><span>Customer analytics</span></div>
      </section>
      <section className="surface linked-work">
        <div><Badge tone="high">Open gap</Badge><strong>Missing mapping for TAX_NUMBER</strong><p>Detected in SAP Sales Order with 27 evidence items.</p><button onClick={() => navigate("gaps", { gap: 1 })}>Review gap</button></div>
        <div><Badge tone="violet">Proposal #27</Badge><strong>Customer alternative key mapping</strong><p>Validation passed. Human approval is required before change request creation.</p><button onClick={() => navigate("proposal", { id: 27 })}>Review proposal</button></div>
      </section>
    </div>
  );
}

function Relationships({ navigate }) {
  return (
    <div className="relationship-grid">
      {[
        ["Customer Sales Area", "Child entity", "ENTITY-CUSTOMER-SALES-AREA"],
        ["Customer Company Code", "Child entity", "ENTITY-CUSTOMER-COMPANY"],
        ["Business Partner Address", "Related entity", "ENTITY-BP-ADDRESS"],
        ["SAP Business Partner", "Physical representation", "FEP-S4-BUT000-PARTNER"],
      ].map(([name, relation, id]) => (
        <button className="surface relationship-card" key={id} onClick={() => navigate("lineage")}>
          <IconTile type="Entity" />
          <span><Badge tone="cyan">{relation}</Badge><strong>{name}</strong><small>{id}</small></span>
          <ArrowRight size={17} />
        </button>
      ))}
    </div>
  );
}

function GovernancePanel() {
  return (
    <div className="governance-grid">
      <section className="surface">
        <div className="section-title"><div><h2>Ownership</h2><p>Accountability and review roles</p></div></div>
        {[["Data owner", "Customer Data Office", "CD"], ["Data steward", "Priya Nair", "PN"], ["Technical owner", "Migration Platform", "MP"]].map(([role, name, initials]) => (
          <div className="owner-row" key={role}><span className="avatar avatar-soft">{initials}</span><span><small>{role}</small><strong>{name}</strong></span><Badge tone="green">Active</Badge></div>
        ))}
      </section>
      <section className="surface">
        <div className="section-title"><div><h2>Controls</h2><p>Governance policy coverage</p></div></div>
        {["Stable object ID", "Approved semantic definition", "Reference integrity", "SAP context validation"].map((control) => (
          <div className="control-row" key={control}><CheckCircle size={18} weight="fill" /><span>{control}</span><strong>Passed</strong></div>
        ))}
      </section>
    </div>
  );
}

function ModelNode({ data, selected }) {
  const Icon = {
    source: Database,
    mapping: GitBranch,
    canonical: Cube,
    target: Stack,
    gap: Warning,
    decision: FileText,
    proposal: NotePencil,
  }[data.tone] || Database;
  return (
    <div className={`flow-node flow-node-${data.tone} ${selected ? "is-selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <span className="flow-node-icon"><Icon size={19} weight="duotone" /></span>
      <span><strong>{data.label}</strong><small>{data.meta}</small></span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const nodeTypes = { model: ModelNode };

export function LineageScreen({ navigate, params, onExport }) {
  const objectId = params.get("id") || "DOMAIN-CUSTOMER-BP";
  const [direction, setDirection] = useState("both");
  const [depth, setDepth] = useState("All levels");
  const [view, setView] = useState("graph");
  const [selected, setSelected] = useState(objectId);
  const [panelOpen, setPanelOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [nodeQuery, setNodeQuery] = useState("");
  const [visibleLayers, setVisibleLayers] = useState({
    source: true,
    mapping: true,
    canonical: true,
    target: true,
    gap: true,
    decision: true,
    proposal: true,
  });

  const maxDepth = depth === "1 level" ? 1 : depth === "2 levels" ? 2 : 5;
  const { nodes: allNodes, edges: allEdges, upstream, downstream, impact, loading, error } =
    useLineage(objectId, direction, maxDepth);

  useEffect(() => {
    setSelected(objectId);
  }, [objectId]);

  const rootNode = useMemo(
    () => allNodes.find((node) => node.id === objectId) || allNodes[0],
    [allNodes, objectId]
  );

  const selectedNode = useMemo(
    () => allNodes.find((node) => node.id === selected) || rootNode,
    [allNodes, selected, rootNode]
  );

  const selectedObjectId = selectedNode?.id || objectId;

  const inspectorTone =
    selectedNode?.data?.tone === "canonical"
      ? "domain"
      : selectedNode?.data?.tone === "mapping"
        ? "mapping"
        : "neutral";

  const visibleNodeIds = useMemo(() => {
    const query = nodeQuery.trim().toLowerCase();
    return new Set(
      allNodes
        .filter((node) => visibleLayers[node.data.tone] !== false)
        .filter((node) => !query || `${node.data.label} ${node.data.meta}`.toLowerCase().includes(query))
        .map((node) => node.id)
    );
  }, [allNodes, nodeQuery, visibleLayers]);

  const nodes = useMemo(
    () =>
      allNodes.map((node) => ({
        ...node,
        hidden: !visibleNodeIds.has(node.id),
        selected: node.id === selected,
      })),
    [allNodes, visibleNodeIds, selected]
  );

  const edges = useMemo(
    () =>
      allEdges.map((edge) => ({
        ...edge,
        hidden: !(visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)),
      })),
    [allEdges, visibleNodeIds]
  );

  const title = rootNode?.data?.label
    ? `${rootNode.data.label} lineage`
    : "Object lineage";

  return (
    <div className="lineage-page">
      <div className="lineage-header page-pad">
        <PageHeader
          title={title}
          description="Trace systems, transformations, canonical objects, and downstream impact."
          actions={
            <>
              <button className="secondary-button" onClick={() => onExport("lineage")}>
                <Export size={17} /> Export
              </button>
              <button className="primary-button" onClick={() => navigate("object", { id: selectedObjectId })}><ArrowRight size={17} /> View object</button>
            </>
          }
        />
        <div className="lineage-toolbar">
          <label className="inline-search wide">
            <MagnifyingGlass size={17} />
            <input
              value={nodeQuery}
              onChange={(event) => setNodeQuery(event.target.value)}
              placeholder="Find a node or field…"
            />
          </label>
          <label className="select-control"><span>Direction</span><select value={direction} onChange={(event) => setDirection(event.target.value)}><option value="both">Both</option><option value="upstream">Upstream</option><option value="downstream">Downstream</option></select></label>
          <label className="select-control"><span>Depth</span><select value={depth} onChange={(event) => setDepth(event.target.value)}><option>1 level</option><option>2 levels</option><option>All levels</option></select></label>
          <div className="view-toggle">
            <button className={view === "graph" ? "is-active" : ""} onClick={() => setView("graph")} aria-label="Graph view">Graph</button>
            <button className={view === "path" ? "is-active" : ""} onClick={() => setView("path")} aria-label="Path list view">Path</button>
          </div>
          <button className={`secondary-button ${filtersOpen ? "is-active" : ""}`} onClick={() => setFiltersOpen((value) => !value)}>
            <Funnel size={17} /> Filters
          </button>
          <button className={`icon-button bordered ${panelOpen ? "is-active" : ""}`} onClick={() => setPanelOpen((value) => !value)}><SidebarSimple size={18} /></button>
        </div>
        {filtersOpen && (
          <div className="lineage-filter-bar">
            {[
              ["Source systems", "source"],
              ["Mappings", "mapping"],
              ["Canonical objects", "canonical"],
              ["Datasets", "target"],
              ["Gaps", "gap"],
              ["Decisions", "decision"],
              ["Proposals", "proposal"],
            ].map(([item, layer]) => (
              <label key={item}><input type="checkbox" checked={visibleLayers[layer]} onChange={() => setVisibleLayers((current) => ({ ...current, [layer]: !current[layer] }))} /><span>{item}</span></label>
            ))}
          </div>
        )}
      </div>
      <div className="lineage-workspace">
        {loading && <div className="empty-state"><CircleNotch className="spin" size={24} /> Loading lineage…</div>}
        {error && <div className="empty-state"><WarningCircle size={24} /> {error}</div>}
        {!loading && view === "graph" && (
          <div className="lineage-canvas">
            <div className="canvas-legend">
              <span><i className="legend-source" /> Source</span>
              <span><i className="legend-mapping" /> Transformation</span>
              <span><i className="legend-canonical" /> Canonical</span>
              <span><i className="legend-target" /> Target</span>
              <span><i className="legend-gap" /> Gap</span>
              <span><i className="legend-decision" /> Decision</span>
              <span><i className="legend-proposal" /> Proposal</span>
            </div>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodeClick={(_, node) => { setSelected(node.id); setPanelOpen(true); }}
              fitView
              minZoom={0.55}
              maxZoom={1.5}
            >
              <Background color="#dce4ef" gap={24} size={1} />
              <Controls showInteractive={false} />
              <MiniMap pannable zoomable nodeColor={(node) => node.data.tone === "canonical" ? "#2563eb" : "#cbd5e1"} />
            </ReactFlow>
          </div>
        )}
        {!loading && view === "path" && (
          <div className="lineage-path-view page-pad">
            <section className="surface">
              <div className="section-title"><div><h2>Root object</h2><p>Selected lineage starting point</p></div></div>
              <button className="result-row" onClick={() => navigate("object", { id: objectId })}>
                <IconTile type={objectTypeToTone(rootNode?.data?.tone || "canonical")} />
                <span className="result-copy">
                  <span className="result-name"><strong>{rootNode?.data?.label || objectId}</strong></span>
                  <span className="result-description">{rootNode?.data?.meta || objectId}</span>
                </span>
                <CaretRight size={18} />
              </button>
            </section>
            <section className="surface">
              <div className="section-title"><div><h2>Upstream</h2><p>Objects that feed into the root</p></div></div>
              {upstream.length ? upstream.map((node) => (
                <button className="result-row" key={node.object_id} onClick={() => navigate("object", { id: node.object_id })}>
                  <IconTile type={objectTypeToTone(node.object_type)} />
                  <span className="result-copy">
                    <span className="result-name"><strong>{node.object_name || node.object_id}</strong></span>
                    <span className="result-description">{node.object_type} · {node.object_id}</span>
                  </span>
                  <CaretRight size={18} />
                </button>
              )) : <p className="empty-state">No upstream objects visible.</p>}
            </section>
            <section className="surface">
              <div className="section-title"><div><h2>Downstream</h2><p>Objects affected by the root</p></div></div>
              {downstream.length ? downstream.map((node) => (
                <button className="result-row" key={node.object_id} onClick={() => navigate("object", { id: node.object_id })}>
                  <IconTile type={objectTypeToTone(node.object_type)} />
                  <span className="result-copy">
                    <span className="result-name"><strong>{node.object_name || node.object_id}</strong></span>
                    <span className="result-description">{node.object_type} · {node.object_id}</span>
                  </span>
                  <CaretRight size={18} />
                </button>
              )) : <p className="empty-state">No downstream objects visible.</p>}
            </section>
            {impact && (
              <section className="surface">
                <div className="section-title"><div><h2>Impact summary</h2><p>Deterministic downstream traversal</p></div></div>
                <div className="impact-grid">
                  <div className="surface"><strong>{impact.upstream.length}</strong><span>Upstream objects</span></div>
                  <div className="surface"><strong>{impact.downstream.length}</strong><span>Downstream objects</span></div>
                  <div className="surface"><strong>{impact.total_affected}</strong><span>Total affected</span></div>
                </div>
              </section>
            )}
          </div>
        )}
        {panelOpen && (
          <aside className="lineage-inspector">
            <div className="inspector-heading">
              <span><Badge tone={inspectorTone}>{selectedNode?.data?.meta || "Node"}</Badge><h2>{selectedNode?.data?.label || "Object"}</h2></span>
              <button className="icon-button" onClick={() => setPanelOpen(false)}><X size={18} /></button>
            </div>
            <p>Selected node details, validation context, and visible path evidence.</p>
            <div className="inspector-block">
              <small>Object ID</small>
              <code>{selectedObjectId}</code>
            </div>
            <div className="inspector-block">
              <small>Visible impact</small>
              <div className="metric-pair"><span><strong>{upstream.length}</strong> upstream</span><span><strong>{downstream.length}</strong> downstream</span></div>
            </div>
            <div className="inspector-block">
              <small>Path evidence</small>
              <ul className="path-list">
                {edges.slice(0, 6).map((edge) => (
                  <li key={edge.id}><CheckCircle size={16} /> {edge.source} → {edge.target} <small>({edge.label})</small></li>
                ))}
                {!edges.length && <li><CheckCircle size={16} /> No visible edges.</li>}
              </ul>
            </div>
            <button className="primary-button full-width" onClick={() => navigate("object", { id: selectedObjectId })}>Open object details</button>
            <button className="secondary-button full-width" onClick={() => navigate("gaps")}>Review related gaps</button>
          </aside>
        )}
      </div>
    </div>
  );
}

function GapsScreen({ navigate, params, onDraft }) {
  const liveFindings = useAssessmentFindings();
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("All severities");
  const [status, setStatus] = useState("All statuses");
  const [moreFilters, setMoreFilters] = useState(false);
  const [sort, setSort] = useState("Risk first");
  const [expandedId, setExpandedId] = useState(1);

  useEffect(() => {
    const gapParam = params.get("gap");
    if (!gapParam) {
      setExpandedId(1);
      return;
    }
    const id = Number(gapParam);
    if (!Number.isInteger(id) || !gaps.some((gap) => gap.id === id)) {
      setExpandedId(null);
    } else {
      setExpandedId(id);
    }
  }, [params]);
  const recommendedProposal = proposals.find((proposal) => proposal.status === "In review") || proposals[0];
  const shown = useMemo(() => {
    const filtered = gaps.filter((gap) => {
      const matchesQuery = `${gap.title} ${gap.object} ${gap.source}`.toLowerCase().includes(query.toLowerCase());
      const matchesStatus = status === "All statuses" || gap.status === status;
      return matchesQuery && matchesStatus && (severity === "All severities" || gap.severity === severity);
    });
    const list = [...filtered];
    if (sort === "Risk first") {
      list.sort((a, b) => severityWeight[b.severity] - severityWeight[a.severity]);
    } else if (sort === "Recently detected") {
      list.sort((a, b) => updatedMinutes(b.detected) - updatedMinutes(a.detected));
    } else if (sort === "Object name") {
      list.sort((a, b) => a.object.localeCompare(b.object));
    }
    return list;
  }, [query, severity, status, sort]);

  const selectedGap = gaps.find((gap) => gap.id === expandedId) || gaps[0];

  if (!liveFindings.demo) {
    return <LiveFindingsScreen navigate={navigate} {...liveFindings} />;
  }

  return (
    <div className="page-pad gaps-page">
      <PageHeader
        title="Open gaps"
        description="Review missing mappings, inconsistent types, and unresolved model coverage."
        actions={
          <button className="primary-button" onClick={onDraft}><Plus size={17} /> Draft proposal</button>
        }
      />
      <div className="gap-controls">
        <label className="inline-search wide"><MagnifyingGlass size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search gaps by field, object, or source…" /></label>
        <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
          <option>All severities</option><option>High</option><option>Medium</option><option>Low</option>
        </select>
        <select value={sort} onChange={(event) => setSort(event.target.value)}>
          <option>Risk first</option><option>Recently detected</option><option>Object name</option>
        </select>
        <button className={`secondary-button ${moreFilters ? "is-active" : ""}`} onClick={() => setMoreFilters((value) => !value)}><Funnel size={17} /> More filters</button>
      </div>
      {moreFilters && (
        <div className="gap-extra-filters">
          <label>Status<select value={status} onChange={(event) => setStatus(event.target.value)}><option>All statuses</option><option>In review</option><option>Draft</option><option>Needs proposal</option></select></label>
          <label>Object<select aria-label="Gap object"><option>All objects</option><option>Business Partner</option><option>Sales Order</option><option>Customer</option></select></label>
          <label>Source<select aria-label="Gap source"><option>All sources</option><option>SAP S/4HANA</option><option>Legacy CRM</option><option>Customer SQL</option></select></label>
          <button onClick={() => { setStatus("All statuses"); setSeverity("All severities"); setQuery(""); }}>Reset filters</button>
        </div>
      )}
      <div className="gaps-layout">
        <section className="gap-list">
          {shown.length === 0 ? (
            <div className="empty-state">
              <Warning size={30} />
              <h3>No gaps match the current filters</h3>
              <button onClick={() => { setQuery(""); setSeverity("All severities"); setStatus("All statuses"); }}>Clear filters</button>
            </div>
          ) : (
            shown.map((gap) => {
              const expanded = expandedId === gap.id;
              return (
                <article className={`gap-card ${expanded ? "is-expanded" : ""}`} key={gap.id}>
                  <button className="gap-card-main" onClick={() => setExpandedId(expanded ? null : gap.id)}>
                    <span className="gap-index">{gap.id}</span>
                    <span className="gap-title">
                      <span><strong>{gap.title}</strong><Badge tone={gap.severity.toLowerCase()}>{gap.severity}</Badge></span>
                      <small>{gap.note}</small>
                    </span>
                    <span className="gap-owner"><span className="avatar avatar-soft">{gap.initials}</span><span><small>Owner</small><strong>{gap.owner}</strong></span></span>
                    <CaretDown className={expanded ? "rotate" : ""} size={17} />
                  </button>
                  {expanded && (
                    <div className="gap-detail">
                      <div><small>Impacted object</small><strong><Cube size={15} /> {gap.object}</strong></div>
                      <div><small>Source → target</small><strong>{gap.source} <ArrowRight size={13} /> {gap.target}</strong></div>
                      <div><small>Proposal</small><strong>{gap.proposal}</strong></div>
                      <div className="gap-detail-actions">
                        <button className="primary-button" onClick={() => navigate(gap.proposalId ? "proposal" : "proposals", gap.proposalId ? { id: gap.proposalId } : undefined)}>
                          {gap.proposalId ? "Review proposal" : "Create proposal"}
                        </button>
                      </div>
                    </div>
                  )}
                  <footer>
                    <span>Proposal <Badge tone={gap.status === "In review" ? "violet" : "neutral"}>{gap.status}</Badge></span>
                    <span>{gap.proposal}</span>
                    <span>Detected {gap.detected}</span>
                  </footer>
                </article>
              );
            })
          )}
        </section>
        <aside className="gaps-rail">
          <section className="surface gap-summary">
            <div className="section-title">
              <div><h2>Gap summary</h2><p>Current model coverage</p></div>
              <button className="icon-button" onClick={() => setMoreFilters((value) => !value)} aria-label="Show gap filters"><Info size={17} /></button>
            </div>
            <strong className="summary-number">5</strong>
            <span className="summary-label">Total open gaps</span>
            <div className="severity-list">
              <span><i className="severity-high" /> High <strong>2</strong></span>
              <span><i className="severity-medium" /> Medium <strong>1</strong></span>
              <span><i className="severity-low" /> Low <strong>2</strong></span>
            </div>
            <div className="summary-stat"><span>Proposals linked</span><strong>60%</strong></div>
            <div className="summary-stat"><span>Validation risk</span><Badge tone="high">High</Badge></div>
          </section>
          <section className="surface gap-detail-panel">
            <div className="section-title">
              <div>
                <h2>{selectedGap.title}</h2>
                <p><Badge tone={selectedGap.severity.toLowerCase()}>{selectedGap.severity}</Badge></p>
              </div>
            </div>
            <p className="gap-detail-note">{selectedGap.note}</p>
            <div className="gap-detail-block">
              <small>Recommendation</small>
              <p>{selectedGap.recommendation}</p>
            </div>
            <div className="gap-detail-block">
              <small>Evidence</small>
              <ul className="gap-evidence-list">
                {selectedGap.evidence.map((item, index) => (
                  <li key={index}><CheckCircle size={14} /> {item}</li>
                ))}
              </ul>
            </div>
            <div className="gap-detail-actions">
              <button className="secondary-button full-width" onClick={() => navigate("object", { id: selectedGap.linkedObjectId })}>
                Open object
              </button>
              {selectedGap.linkedProposalId ? (
                <button className="primary-button full-width" onClick={() => navigate("proposal", { id: selectedGap.linkedProposalId })}>
                  Review proposal
                </button>
              ) : (
                <button className="primary-button full-width" onClick={onDraft}>Create proposal</button>
              )}
            </div>
          </section>
          <section className="surface assistant-suggestion">
            <span className="assistant-mark"><Sparkle size={17} weight="fill" /></span>
            <h2>Recommended next step</h2>
            <div>
              <strong>Review Proposal #{recommendedProposal.id}</strong>
              <p>It addresses the highest-risk gap and includes all required evidence.</p>
              <button className="primary-button full-width" onClick={() => navigate("proposal", { id: recommendedProposal.id })}>Review proposal</button>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

const DISPOSITION_OPTIONS = ["", "confirmed", "false_positive", "accepted_risk", "deferred", "resolved"];

function FindingReviewForm({ assessmentId, findingId, currentReview, onReviewed }) {
  const [disposition, setDisposition] = useState(currentReview?.disposition || "");
  const [note, setNote] = useState(currentReview?.note || "");
  const { reviewFinding, loading, error } = useFindingReview();

  const save = async () => {
    if (!disposition) return;
    try {
      await reviewFinding({
        assessment: assessmentId,
        finding_id: findingId,
        disposition,
        reviewer: "workbench",
        note,
      });
      onReviewed({ disposition, note });
    } catch {
      // error is surfaced below
    }
  };

  return (
    <div className="finding-review-form">
      <label>
        <span>Disposition</span>
        <select value={disposition} onChange={(event) => setDisposition(event.target.value)}>
          {DISPOSITION_OPTIONS.map((option) => <option key={option} value={option}>{option ? option.replaceAll("_", " ") : "— Select —"}</option>)}
        </select>
      </label>
      <label>
        <span>Note (optional)</span>
        <textarea value={note} onChange={(event) => setNote(event.target.value)} rows={2} placeholder="Add context for the disposition…" />
      </label>
      <button className="secondary-button" onClick={save} disabled={!disposition || loading}>
        {loading ? "Saving…" : "Save disposition"}
      </button>
      {error && <span className="inline-error">{error}</span>}
    </div>
  );
}

function LiveFindingsScreen({ navigate, findings, assessmentId, loading, error }) {
  const [localReviews, setLocalReviews] = useState({});
  return (
    <div className="page-pad gaps-page">
      <PageHeader
        title="Assessment findings"
        description="Typed local assessment evidence and separate human review state."
      />
      <div className="gaps-layout">
        <section className="gap-list">
          {loading && <div className="empty-state"><CircleNotch className="spin" size={24} /> Loading assessment findings…</div>}
          {error && <div className="empty-state"><WarningCircle size={24} /> {error}</div>}
          {!loading && !error && findings.length === 0 && <div className="empty-state"><Warning size={30} /><h3>No assessment findings are available</h3><p>Run a local assessment to create reviewable evidence. Canonical model files remain unchanged.</p></div>}
          {findings.map(({ finding, review, assessment_id: itemAssessmentId }) => {
            const localReview = localReviews[finding.id];
            const currentDisposition = localReview?.disposition || review?.disposition;
            return (
              <article className="gap-card is-expanded" key={finding.id}>
                <div className="gap-card-main">
                  <span className="gap-index">{finding.id}</span>
                  <span className="gap-title"><span><strong>{finding.message}</strong><Badge tone={finding.severity}>{finding.severity}</Badge></span><small>{finding.category} · {finding.provenance.source_kind}</small></span>
                </div>
                <div className="gap-detail">
                  <div><small>Assessment</small><strong>{itemAssessmentId}</strong></div>
                  <div><small>Detection</small><strong>{finding.provenance.source_kind}</strong></div>
                  <div><small>Review state</small><strong>{currentDisposition ? currentDisposition.replaceAll("_", " ") : "Unreviewed"}</strong></div>
                  <div><small>Evidence location</small><strong>{Object.entries(finding.provenance.location).map(([key, value]) => `${key}: ${value}`).join(" · ") || "Not recorded"}</strong></div>
                </div>
                <FindingReviewForm
                  assessmentId={itemAssessmentId}
                  findingId={finding.id}
                  currentReview={localReview || review}
                  onReviewed={(updated) => setLocalReviews((current) => ({ ...current, [finding.id]: updated }))}
                />
                {(localReview?.note || review?.note) && <footer><span>Reviewer note: {localReview?.note || review.note}</span></footer>}
              </article>
            );
          })}
        </section>
        <aside className="gaps-rail">
          <section className="surface gap-summary"><div className="section-title"><div><h2>Evidence boundary</h2><p>{assessmentId || "No local assessment package"}</p></div></div><p>Findings are derived local evidence. Human dispositions are shown separately and do not modify canonical model files.</p><button className="secondary-button full-width" onClick={() => navigate("reports")}>Open generated artifacts</button></section>
        </aside>
      </div>
    </div>
  );
}

function ProposalsScreen({ navigate, onDraft, refreshKey = 0 }) {
  const [tab, setTab] = useState("All");
  const [query, setQuery] = useState("");
  const { proposals, loading, error, demo } = useProposals(refreshKey);
  const tabs = ["All", "In review", "Approved", "Rejected"];
  const shown = proposals.filter((proposal) => {
    const matchesTab = tab === "All" || proposal.status === tab || (tab === "Rejected" && proposal.status === "Changes requested");
    const matchesQuery = `${proposal.title} ${proposal.summary} ${proposal.author}`.toLowerCase().includes(query.toLowerCase());
    return matchesTab && matchesQuery;
  });
  return (
    <div className="page-pad proposals-page">
      <PageHeader
        title="Proposals"
        description="Review AI-assisted model changes before they become canonical."
        actions={
          <button className="primary-button" onClick={onDraft}><Plus size={17} /> New proposal</button>
        }
      />
      <div className="proposal-toolbar">
        <div className="segmented-control">
          {tabs.map((item) => <button className={tab === item ? "is-active" : ""} key={item} onClick={() => setTab(item)}>{item}</button>)}
        </div>
        <label className="inline-search"><MagnifyingGlass size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search proposals" /></label>
      </div>
      <div className="proposal-list">
        {loading && <div className="empty-state"><CircleNotch className="spin" size={24} /> Loading proposals…</div>}
        {error && <div className="empty-state"><WarningCircle size={24} /> {error}</div>}
        {!loading && !error && shown.length === 0 ? (
          <div className="empty-state">
            <NotePencil size={30} />
            <h3>No proposals match</h3>
            <p>Try a different status tab or clear the search.</p>
            <button onClick={() => { setTab("All"); setQuery(""); }}>Clear filters</button>
          </div>
        ) : (
          shown.map((proposal) => {
            const pid = proposal.proposalId || proposal.id;
            return (
              <button className="proposal-row" key={pid} onClick={() => navigate("proposal", { id: pid })}>
                <span className="proposal-number">#{pid}</span>
                <span className="proposal-copy">
                  <span><Badge tone={proposal.status === "In review" ? "violet" : proposal.status === "Approved" ? "green" : "neutral"}>{proposal.status}</Badge><Badge tone={proposal.risk.toLowerCase()}>{proposal.risk} risk</Badge></span>
                  <strong>{proposal.title}</strong>
                  <p>{proposal.summary}</p>
                  <small>{proposal.changes} proposed changes · {proposal.author} · Updated {proposal.updated}</small>
                </span>
                <span className="proposal-review">Review <ArrowRight size={16} /></span>
              </button>
            );
          })
        )}
      </div>
      {demo && <p className="demo-note">Demo proposals shown. Connect the local API to review live proposals.</p>}
    </div>
  );
}

function ProposalScreen({ navigate, params, onToast, onRefreshProposals, refreshKey = 0 }) {
  const [tab, setTab] = useState("Changes");
  const [decision, setDecision] = useState(null);
  const [comment, setComment] = useState("");
  const [savedComment, setSavedComment] = useState("");
  const [reviewStatus, setReviewStatus] = useState("");
  const [applied, setApplied] = useState(false);
  const proposalId = params.get("id");
  const { demo } = useApi();
  const {
    proposal: liveProposal,
    loading,
    error,
  } = useProposalDetail(proposalId, refreshKey);
  const proposal = liveProposal || (proposalId ? proposals.find((item) => String(item.id) === String(proposalId)) : proposals[0]);
  const { reviewProposal, loading: reviewLoading } = useProposalReview();
  const { run: runValidate, loading: validateLoading, result: validateResult } = useProposalValidate();
  const { run: runDryRun, loading: dryRunLoading, result: dryRunResult } = useProposalDryRun();
  const { run: runApply, loading: applyLoading, error: applyError, result: applyResult } = useProposalApply();
  const { run: runDiff, loading: diffLoading, error: diffError, result: diffResult } = useProposalDiff();

  const pid = proposal?.proposalId || proposal?.id;
  const effectiveStatus = reviewStatus || proposal?.status || "";
  const isApproved = effectiveStatus === "Approved";
  const isApplied = applied || Boolean(proposal?.appliedAt);

  useEffect(() => {
    setReviewStatus("");
    setApplied(false);
  }, [proposalId]);

  useEffect(() => {
    const openApproval = () => setDecision("approve");
    window.addEventListener("martenweave:approve", openApproval);
    return () => window.removeEventListener("martenweave:approve", openApproval);
  }, []);

  useEffect(() => {
    if (tab === "Validation" && proposal && pid && !demo) {
      runValidate(pid).catch(() => {});
    }
  }, [tab, proposal, demo, runValidate, pid]);

  useEffect(() => {
    if (tab === "Impact" && proposal && pid && !demo) {
      runDryRun(pid).catch(() => {});
    }
  }, [tab, proposal, demo, runDryRun, pid]);

  useEffect(() => {
    if (tab === "Diff" && proposal && pid && !demo) {
      runDiff(pid).catch(() => {});
    }
  }, [tab, proposal, demo, runDiff, pid]);

  const handleConfirm = async (decisionType, reason) => {
    if (!proposal || !pid) return;
    const nextStatus = decisionType === "approve" ? "Approved" : "Changes requested";
    if (demo) {
      setReviewStatus(nextStatus);
      onToast(`${nextStatus}: Proposal #${pid}. Canonical files remain unchanged.`);
      return;
    }
    const status = decisionType === "approve" ? "accepted" : "rejected";
    const body = { status, reviewer: "workbench" };
    if (decisionType === "reject") body.rejection_reason = reason;
    else if (reason) body.reviewer_notes = reason;
    try {
      await reviewProposal(pid, body);
      setReviewStatus(nextStatus);
      onToast(`${nextStatus}: Proposal #${pid}. Canonical files remain unchanged.`);
    } catch {
      onToast(`Review failed for Proposal #${pid}.`);
    }
  };

  const handleApply = async () => {
    if (!proposal || !pid) return;
    if (demo) {
      setApplied(true);
      setReviewStatus("");
      onRefreshProposals();
      onToast(`Applied Proposal #${pid}: 1 file(s) changed.`);
      return;
    }
    try {
      const result = await runApply(pid);
      setApplied(true);
      setReviewStatus("");
      onRefreshProposals();
      const count = result?.changed_files?.length ?? 0;
      onToast(`Applied Proposal #${pid}: ${count} file(s) changed.`);
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : String(reason);
      onToast(`Apply failed: ${message}`);
    }
  };

  const handleReturnToDraft = async () => {
    if (!proposal || !pid) return;
    if (demo) {
      setReviewStatus("In review");
      onRefreshProposals();
      onToast(`Proposal #${pid} returned to draft.`);
      return;
    }
    try {
      await reviewProposal(pid, {
        status: "pending_review",
        reviewer: "workbench",
        reviewer_notes: "Returned to draft by reviewer",
      });
      setReviewStatus("In review");
      onRefreshProposals();
      onToast(`Proposal #${pid} returned to draft.`);
    } catch {
      onToast(`Return to draft failed for Proposal #${pid}.`);
    }
  };

  if (loading) {
    return (
      <div className="proposal-review-page page-pad">
        <div className="empty-state"><CircleNotch className="spin" size={24} /> Loading proposal…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="proposal-review-page page-pad">
        <div className="empty-state"><WarningCircle size={24} /> {error}</div>
      </div>
    );
  }

  if (!proposal) {
    return (
      <div className="proposal-review-page page-pad">
        <div className="empty-state"><NotePencil size={30} /><h3>Proposal not found</h3></div>
      </div>
    );
  }

  const linkedGapText = proposal.source_evidence?.[0] || proposal.linkedGap;
  const linkedGapId = proposal.linkedGapId;

  return (
    <div className="proposal-review-page">
      <div className="proposal-review-header page-pad">
        <button className="back-link" onClick={() => navigate("proposals")}><CaretLeft size={15} /> Back to proposals</button>
        <div className="proposal-title-row">
          <div>
            <div className="object-type-row"><Badge tone={isApproved ? "green" : "violet"}>{effectiveStatus}</Badge><Badge tone={proposal.risk.toLowerCase()}>{proposal.risk} impact</Badge></div>
            <h1>{proposal.title}</h1>
            <p>Proposal #{pid} · Created by {proposal.author} · Updated {proposal.updated}</p>
          </div>
          <div className="page-actions">
            <button className="danger-button" onClick={() => setDecision("reject")} disabled={Boolean(reviewStatus) || reviewLoading}><XCircle size={17} /> Request changes</button>
            <button className="approve-button" onClick={() => setDecision("approve")} disabled={Boolean(reviewStatus) || reviewLoading}><CheckCircle size={17} /> {reviewStatus || "Approve proposal"}</button>
            {isApproved && !isApplied && (
              <button className="primary-button" onClick={handleApply} disabled={applyLoading}>
                <CheckCircle size={17} /> {applyLoading ? "Applying…" : "Apply to canonical"}
              </button>
            )}
            {effectiveStatus && effectiveStatus !== "In review" && !isApplied && (
              <button className="secondary-button" onClick={handleReturnToDraft} disabled={reviewLoading}>
                Return to draft
              </button>
            )}
            {applyError && <span className="inline-error">{applyError}</span>}
          </div>
        </div>
      </div>
      <div className="proposal-review-body">
        <div className="review-main">
          <section className="proposal-summary-strip">
            <div><small>Risk classification</small><strong><WarningCircle size={16} /> {proposal.risk}</strong></div>
            <div><small>Canonical objects</small><strong>{(proposal.affected_objects?.length || proposal.impactObjects) || 0} affected</strong></div>
            <div><small>Proposed changes</small><strong>{(proposal.operations?.length || proposal.changes) || 0} changes</strong></div>
            <div><small>Validation</small><strong><CheckCircle size={16} /> {capitalize(proposal.validation_status || proposal.validationStatus)}</strong></div>
          </section>
          <div className="review-tabs">
            {["Changes", "Diff", "Impact", "Validation", "Activity"].map((item) => <button className={tab === item ? "is-active" : ""} key={item} onClick={() => setTab(item)}>{item}</button>)}
          </div>
          {tab === "Changes" && <ProposalChanges proposal={proposal} />}
          {tab === "Diff" && <ProposalDiff diffs={diffResult?.diffs} loading={diffLoading} error={diffError} demo={demo} />}
          {tab === "Impact" && <ProposalImpact navigate={navigate} proposal={proposal} dryRunResult={dryRunResult} dryRunLoading={dryRunLoading} />}
          {tab === "Validation" && <ProposalValidation proposal={proposal} validateResult={validateResult} validateLoading={validateLoading} />}
          {tab === "Activity" && <ProposalActivity proposalId={pid} refreshKey={refreshKey} />}
        </div>
        <aside className="review-sidebar">
          <section className="surface">
            <div className="section-title"><div><h2>Review context</h2><p>Why this change exists</p></div></div>
            <p className="review-context">
              {linkedGapText || "Assessment evidence"} is driving this proposal. The change adds or modifies canonical
              endpoints with deterministic transform evidence.
            </p>
            {linkedGapId && (
              <button className="linked-gap" onClick={() => navigate("gaps", { gap: linkedGapId })}>
                <WarningCircle size={18} />
                <span><small>Linked gap</small><strong>{linkedGapText || "Linked finding"}</strong></span>
                <CaretRight size={15} />
              </button>
            )}
          </section>
          <section className="surface">
            <div className="section-title"><div><h2>Reviewers</h2><p>{proposal.riskAssessment?.requires_approval ? "Requires approved ChangeRequest" : "No approval required"}</p></div></div>
            <div className="reviewer-row"><span className="avatar avatar-soft">PN</span><span><strong>Priya Nair</strong><small>Data steward</small></span><CheckCircle size={18} weight="fill" /></div>
            <div className="reviewer-row"><span className="avatar avatar-soft">AC</span><span><strong>Alex Chen</strong><small>Your review</small></span><Badge>{reviewStatus || "Pending"}</Badge></div>
          </section>
          <section className="surface comment-box">
            <div className="section-title"><div><h2>Review note</h2><p>Visible to proposal reviewers</p></div></div>
            <textarea value={comment} onChange={(event) => setComment(event.target.value)} placeholder="Add context or a review note…" rows={4} />
            <button className="secondary-button full-width" disabled={!comment.trim()} onClick={() => { setSavedComment(comment); setComment(""); }}>
              <ChatCircleText size={17} /> Add note
            </button>
            {savedComment && <div className="saved-note"><CheckCircle size={15} /> Note added: {savedComment}</div>}
          </section>
        </aside>
      </div>
      {decision && (
        <DecisionDialog
          type={decision}
          proposalId={pid}
          onClose={() => setDecision(null)}
          onConfirm={handleConfirm}
        />
      )}
    </div>
  );
}

function ProposalChanges({ proposal }) {
  const operations = proposal.operations || [];
  return (
    <section className="change-section">
      <div className="change-section-heading">
        <div><h2>Proposed canonical changes</h2><p>Review every mutation before approval.</p></div>
      </div>
      {operations.length === 0 ? (
        <div className="empty-state"><FileText size={24} /><p>No operation details available.</p></div>
      ) : (
        operations.map((operation, index) => (
          <article className="diff-card" key={index}>
            <header>
              <span><GitDiff size={18} /> {operation.object_type} · {operation.object_id}</span>
              <Badge tone={operation.op === "add" ? "green" : operation.op === "remove" ? "high" : "blue"}>{operation.op}</Badge>
            </header>
            <div className="field-diff">
              <div><small>Object</small><strong>{operation.object_id}</strong></div>
              {operation.target_path && (
                <div><small>Path</small><code>{operation.target_path.join(".")}</code></div>
              )}
            </div>
            {(operation.before !== undefined || operation.after !== undefined) && (
              <div className="field-diff">
                {operation.before !== undefined && (
                  <div className="removed-value"><small>Current</small><code>{JSON.stringify(operation.before)}</code></div>
                )}
                {operation.after !== undefined && (
                  <div className="added-value"><small>Proposed</small><code>{JSON.stringify(operation.after)}</code></div>
                )}
              </div>
            )}
          </article>
        ))
      )}
    </section>
  );
}

function ProposalDiff({ diffs, loading, error, demo }) {
  if (demo) {
    return (
      <section className="change-section">
        <div className="empty-state">
          <Info size={24} />
          <p>Diff preview requires a connected local API.</p>
        </div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="change-section">
        <div className="empty-state"><CircleNotch className="spin" size={24} /> Loading diff preview…</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="change-section">
        <div className="empty-state"><WarningCircle size={24} /> {error}</div>
      </section>
    );
  }

  if (!diffs || diffs.length === 0) {
    return (
      <section className="change-section">
        <div className="empty-state"><FileText size={24} /><p>No diff preview available.</p></div>
      </section>
    );
  }

  return (
    <section className="change-section">
      <div className="change-section-heading">
        <div><h2>Before / after diff</h2><p>Canonical values compared to the proposed changes.</p></div>
      </div>
      {diffs.map((diff, index) => (
        <article className="diff-card" key={index}>
          <header>
            <span><GitDiff size={18} /> {diff.object_id}</span>
            <Badge tone={diff.op === "create_object" || diff.op === "add_object" ? "green" : diff.op === "delete_object" ? "high" : "blue"}>{diff.op}</Badge>
          </header>
          <div className="field-diff">
            <div><small>Object</small><strong>{diff.object_id}</strong></div>
            {diff.target_path && (
              <div><small>Path</small><code>{String(diff.target_path)}</code></div>
            )}
          </div>
          {(diff.before !== undefined || diff.after !== undefined) && (
            <div className="field-diff">
              {diff.before !== undefined && (
                <div className="removed-value"><small>Before</small><code>{typeof diff.before === "object" ? JSON.stringify(diff.before) : String(diff.before)}</code></div>
              )}
              {diff.after !== undefined && (
                <div className="added-value"><small>After</small><code>{typeof diff.after === "object" ? JSON.stringify(diff.after) : String(diff.after)}</code></div>
              )}
            </div>
          )}
          {diff.status && (
            <div className="field-diff">
              <div><small>Status</small><strong>{diff.status}</strong></div>
              {diff.reason && <div><small>Reason</small><span>{diff.reason}</span></div>}
            </div>
          )}
        </article>
      ))}
    </section>
  );
}

function ProposalImpact({ navigate, proposal, dryRunResult, dryRunLoading }) {
  const risk = proposal.riskAssessment || {};
  const directObjects = proposal.affected_objects?.length || proposal.impactObjects || 0;
  const downstreamObjects = risk.affected_object_count ?? directObjects;
  const highRiskPaths = risk.risk_level === "high" ? 1 : 0;
  return (
    <section className="change-section">
      <div className="change-section-heading"><div><h2>Impact analysis</h2><p>Deterministic BFS traversal from changed objects.</p></div><button className="secondary-button" onClick={() => navigate("lineage")}><ShareNetwork size={17} /> Open lineage</button></div>
      {dryRunLoading && <div className="empty-state"><CircleNotch className="spin" size={24} /> Running impact analysis…</div>}
      <div className="impact-grid">
        {[["Directly changed", String(directObjects), FileText], ["Downstream objects", String(downstreamObjects), GitBranch], ["Source systems", "3", Database], ["High-risk paths", String(highRiskPaths), WarningCircle]].map(([label, value, Icon]) => (
          <div className="surface" key={label}><Icon size={20} /><strong>{value}</strong><span>{label}</span></div>
        ))}
      </div>
      {risk.risk_reasons?.length > 0 && (
        <section className="surface impact-paths">
          <h3>Risk reasons</h3>
          <ul>
            {risk.risk_reasons.map((reason, index) => <li key={index}><WarningCircle size={14} /> {reason}</li>)}
          </ul>
        </section>
      )}
      {dryRunResult?.changed_files && (
        <section className="surface impact-paths">
          <h3>Dry-run result</h3>
          <p>{dryRunResult.changed_files.length} file(s) would change · max depth {risk.max_impact_depth ?? "—"}</p>
        </section>
      )}
    </section>
  );
}

function ProposalValidation({ proposal, validateResult, validateLoading }) {
  const validationStatus = capitalize(proposal.validation_status || proposal.validationStatus);
  const passed = validationStatus.toLowerCase() === "passed";
  const results = validateResult?.validation_results || proposal.validation_results || [];
  return (
    <section className="change-section">
      <div className="change-section-heading"><div><h2>Validation evidence</h2><p>Deterministic checks executed before review.</p></div><Badge tone={passed ? "green" : "high"}><CheckCircle size={14} /> {passed ? "All checks passed" : "Checks failed"}</Badge></div>
      {validateLoading && <div className="empty-state"><CircleNotch className="spin" size={24} /> Running validation…</div>}
      <div className="validation-list">
        {results.length > 0 ? results.map((result, index) => (
          <div className="surface validation-row" key={index}><span className="validation-check"><Check size={16} weight="bold" /></span><span><strong>{result.check || result.rule || `Check ${index + 1}`}</strong><small>{result.message || result.description || ""}</small></span><Badge tone={result.status === "passed" || result.status === "Passed" ? "green" : "high"}>{capitalize(result.status)}</Badge></div>
        )) : (
          [
            ["Schema validation", "Object structure matches the registered Attribute and Mapping schemas."],
            ["Reference integrity", "All proposed object references resolve to valid canonical IDs."],
            ["SAP context", "Source endpoint context matches the registered domain pack rules."],
            ["ID uniqueness", "No duplicate stable IDs were found in the repository."],
          ].map(([title, description]) => (
            <div className="surface validation-row" key={title}><span className="validation-check"><Check size={16} weight="bold" /></span><span><strong>{title}</strong><small>{description}</small></span><Badge tone={passed ? "green" : "high"}>{validationStatus || "Passed"}</Badge></div>
          ))
        )}
      </div>
    </section>
  );
}

function ProposalActivity({ proposalId, refreshKey = 0 }) {
  const { events, loading, error, demo } = useWorkspaceActivity(refreshKey);
  const activity = demo
    ? [
      ["Proposal generated", "Martenweave AI created patch operations from gap evidence.", "18m ago", Sparkle],
      ["Validation completed", "All deterministic repository checks passed.", "16m ago", ShieldCheck],
      ["Impact analysis completed", "Six downstream objects and one high-risk path detected.", "15m ago", ShareNetwork],
      ["Priya Nair approved", "Data stewardship review completed.", "7m ago", CheckCircle],
    ]
    : events
      .filter((event) => event.proposal_id === proposalId)
      .map((event) => [
        event.event_type.replaceAll("_", " "),
        event.changed_object_ids?.join(", ") || event.proposal_id || "Proposal event",
        new Date(event.timestamp).toLocaleString(),
        CheckCircle,
      ]);
  return (
    <section className="change-section">
      <div className="change-section-heading"><div><h2>Proposal activity</h2><p>Immutable review and validation history.</p></div></div>
      {loading && <div className="empty-state"><CircleNotch className="spin" size={24} /> Loading activity…</div>}
      {error && <div className="empty-state"><WarningCircle size={24} /> {error}</div>}
      {!loading && !error && activity.length === 0 && <p className="empty-state">No activity recorded for this proposal.</p>}
      <div className="timeline">
        {activity.map(([title, description, time, Icon], index) => (
          <div key={index}><span className="timeline-icon"><Icon size={16} /></span><span><strong>{title}</strong><small>{description}</small></span><time>{time}</time></div>
        ))}
      </div>
    </section>
  );
}

function DecisionDialog({ type, proposalId, onClose, onConfirm }) {
  const approve = type === "approve";
  const [reason, setReason] = useState("");
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="decision-dialog" role="dialog" aria-modal="true" aria-labelledby="decision-title" onMouseDown={(event) => event.stopPropagation()}>
        <button className="icon-button dialog-close" onClick={onClose}><X size={18} /></button>
        <span className={`dialog-icon ${approve ? "approve" : "reject"}`}>{approve ? <SealCheck size={24} /> : <XCircle size={24} />}</span>
        <h2 id="decision-title">{approve ? `Approve Proposal #${proposalId}?` : "Request changes?"}</h2>
        <p>{approve ? "Approval creates a governed change request. Canonical files are not modified until that change request is applied." : "Send the proposal back with a clear reason for the author."}</p>
        <label><span>{approve ? "Approval note (optional)" : "Required changes"}</span><textarea rows={3} value={reason} onChange={(event) => setReason(event.target.value)} placeholder={approve ? "Add a short review note…" : "Explain what must change…"} /></label>
        <div className="dialog-actions">
          <button className="secondary-button" onClick={onClose}>Cancel</button>
          <button className={approve ? "approve-button" : "danger-button"} disabled={!approve && !reason.trim()} onClick={() => onConfirm(type, reason)}>{approve ? <><CheckCircle size={17} /> Approve</> : <><XCircle size={17} /> Request changes</>}</button>
        </div>
      </div>
    </div>
  );
}

export function App({ apiBaseUrl }) {
  const [route, params, navigate] = useRoute();
  const [overlay, setOverlay] = useState(null);
  const [toast, setToast] = useState("");
  const [proposalRefreshKey, setProposalRefreshKey] = useState(0);
  const pendingGo = useRef(false);
  const goTimer = useRef(null);
  const open = useCallback((next) => setOverlay(next), []);
  const close = useCallback(() => setOverlay(null), []);
  const dismissToast = useCallback(() => setToast(""), []);

  useEffect(() => {
    const onKey = (event) => {
      const target = event.target;
      const isTyping =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement ||
        target?.isContentEditable;
      if (event.key === "Escape") {
        setOverlay(null);
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOverlay((current) => current?.type === "commands" ? null : { type: "commands" });
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && route === "proposal") {
        event.preventDefault();
        window.dispatchEvent(new Event("martenweave:approve"));
        return;
      }
      if (isTyping || event.metaKey || event.ctrlKey || event.altKey) return;
      if (event.key === "/") {
        event.preventDefault();
        document.querySelector("[data-global-search]")?.focus();
        return;
      }
      if (event.key === "?") {
        setOverlay({ type: "shortcuts" });
        return;
      }
      if (event.key.toLowerCase() === "i") {
        setOverlay({ type: "import" });
        return;
      }
      if (event.key.toLowerCase() === "e") {
        setOverlay({ type: "export" });
        return;
      }
      if (pendingGo.current) {
        const destination = { m: "models", l: "lineage", g: "gaps", p: "proposals" }[event.key.toLowerCase()];
        pendingGo.current = false;
        window.clearTimeout(goTimer.current);
        if (destination) {
          event.preventDefault();
          navigate(destination);
        }
        return;
      }
      if (event.key.toLowerCase() === "g") {
        pendingGo.current = true;
        goTimer.current = window.setTimeout(() => { pendingGo.current = false; }, 900);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.clearTimeout(goTimer.current);
    };
  }, [navigate, route]);

  const refreshProposals = useCallback(() => {
    setProposalRefreshKey((key) => key + 1);
  }, []);

  const actions = {
    open,
    import: () => open({ type: "import" }),
    export: (exportType) => open({ type: "export", exportType }),
    commands: () => open({ type: "commands" }),
    shortcuts: () => open({ type: "shortcuts" }),
    draft: () => open({ type: "proposal-draft" }),
    toast: setToast,
    refreshProposals,
  };
  const routeTitle = (() => {
    if (route === "object") {
      const id = params.get("id");
      return modelObjects.find((item) => item.id === id)?.name || "Object detail";
    }
    if (route === "proposal") {
      const id = params.get("id");
      return proposals.find((item) => String(item.id) === String(id))?.title || "Proposal review";
    }
    return ROUTE_TITLES[route] || "Workspace";
  })();
  const screen = {
    home: <WorkspaceScreen navigate={navigate} onImport={actions.import} onExport={actions.export} onCommands={actions.commands} onShortcuts={actions.shortcuts} refreshKey={proposalRefreshKey} />,
    models: <ModelsScreen navigate={navigate} params={params} />,
    object: <ObjectScreen navigate={navigate} params={params} onExport={actions.export} onDraft={actions.draft} />,
    lineage: <LineageScreen navigate={navigate} params={params} onExport={actions.export} />,
    gaps: <GapsScreen navigate={navigate} params={params} onDraft={actions.draft} />,
    proposals: <ProposalsScreen navigate={navigate} onDraft={actions.draft} refreshKey={proposalRefreshKey} />,
    proposal: <ProposalScreen navigate={navigate} params={params} onToast={actions.toast} onRefreshProposals={actions.refreshProposals} refreshKey={proposalRefreshKey} />,
    reports: <ReportsScreen onExport={actions.export} />,
    changelog: <ChangelogScreen navigate={navigate} refreshKey={proposalRefreshKey} />,
    settings: <SettingsScreen onToast={actions.toast} onShortcuts={actions.shortcuts} />,
  }[route] || <WorkspaceScreen navigate={navigate} onImport={actions.import} onExport={actions.export} onCommands={actions.commands} onShortcuts={actions.shortcuts} refreshKey={proposalRefreshKey} />;

  return (
    <ApiProvider baseUrl={apiBaseUrl}>
      <ConnectionBanner />
      <AppShell route={route} navigate={navigate} title={routeTitle} actions={actions}>{screen}</AppShell>
      <WorkbenchOverlay overlay={overlay} onClose={close} navigate={navigate} onOpen={open} onToast={setToast} refreshKey={proposalRefreshKey} />
      <Toast message={toast} onClose={dismissToast} />
    </ApiProvider>
  );
}

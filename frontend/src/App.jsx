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
  Code,
  Columns,
  Copy,
  Cube,
  Database,
  DotsThreeVertical,
  Export,
  Eye,
  FileText,
  Funnel,
  GitBranch,
  GitDiff,
  House,
  Info,
  LinkSimple,
  List,
  LockKey,
  MagnifyingGlass,
  NotePencil,
  Paperclip,
  Plus,
  SealCheck,
  ShareNetwork,
  ShieldCheck,
  SidebarSimple,
  SlidersHorizontal,
  Sparkle,
  Table,
  Tag,
  Target,
  TreeStructure,
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
  fields,
  gaps,
  lineageEdges,
  lineageNodes,
  modelObjects,
  proposals,
  recentActivity,
} from "./data.js";

const NAV_ITEMS = [
  { id: "home", label: "Home", icon: House },
  { id: "models", label: "Models", icon: Cube },
  { id: "lineage", label: "Lineage", icon: ShareNetwork },
  { id: "gaps", label: "Gaps", icon: Warning },
  { id: "proposals", label: "Proposals", icon: NotePencil },
];

const ROUTE_TITLES = {
  home: "Model intelligence",
  models: "Global model search",
  object: "Business Partner",
  lineage: "Lineage",
  gaps: "Open gaps",
  proposals: "Proposals",
  proposal: "Proposal review",
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

function Sidebar({ route, navigate, open, onClose }) {
  const activeRoute = route === "object" ? "models" : route === "proposal" ? "proposals" : route;
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
                {id === "gaps" && <span className="nav-count">5</span>}
              </button>
            ))}
          </nav>
        </div>
        <div className="repo-switcher">
          <span className="status-dot" />
          <span>
            <strong>Customer migration</strong>
            <small>Production · v2.4.1</small>
          </span>
          <CaretDown size={16} />
        </div>
      </aside>
    </>
  );
}

function Topbar({ route, navigate, onMenu }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [query, setQuery] = useState("");
  const profileRef = useRef(null);

  useEffect(() => {
    if (!profileOpen) return;
    const onClick = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [profileOpen]);

  const submit = (event) => {
    event.preventDefault();
    const search = query.trim() ? `search=${encodeURIComponent(query.trim())}` : "";
    navigate("models", search);
    setSearchOpen(false);
  };

  return (
    <header className="topbar">
      <div className="topbar-leading">
        <button className="icon-button mobile-menu" onClick={onMenu} aria-label="Open navigation">
          <SidebarSimple size={21} />
        </button>
        <div className="breadcrumb">
          <span>Customer migration</span>
          <CaretRight size={13} />
          <strong>{ROUTE_TITLES[route] || "Workspace"}</strong>
        </div>
      </div>
      <div className="topbar-actions">
        <form className={`top-search ${searchOpen ? "is-open" : ""}`} onSubmit={submit}>
          <MagnifyingGlass size={18} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search model"
            aria-label="Search model"
            onFocus={() => setSearchOpen(true)}
          />
          {searchOpen && (
            <button type="button" aria-label="Close search" onClick={() => setSearchOpen(false)}>
              <X size={16} />
            </button>
          )}
        </form>
        <span className="environment-pill">
          <span className="status-dot" />
          Production
        </span>
        <button className="icon-button notification-button" aria-label="Notifications">
          <Bell size={19} />
          <span />
        </button>
        <div className="profile-wrap" ref={profileRef}>
          <button className="profile-button" onClick={() => setProfileOpen((value) => !value)}>
            <span className="avatar">AC</span>
            <span className="profile-copy">
              <strong>Alex Chen</strong>
              <small>Data Steward</small>
            </span>
            <CaretDown size={14} />
          </button>
          {profileOpen && (
            <div className="profile-menu">
              <button><UserCircle size={18} /> Profile</button>
              <button><SlidersHorizontal size={18} /> Preferences</button>
              <button><Archive size={18} /> Switch repository</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

function AppShell({ route, navigate, children }) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="app-shell">
      <Sidebar
        route={route}
        navigate={navigate}
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
      />
      <div className="app-stage">
        <Topbar route={route} navigate={navigate} onMenu={() => setMenuOpen(true)} />
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

function HomeScreen({ navigate }) {
  const [prompt, setPrompt] = useState("");
  const [submittedPrompt, setSubmittedPrompt] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const suggestions = [
    "Show high-risk gaps in Business Partner",
    "Trace TAX_NUMBER across source systems",
    "What changed in the model this week?",
  ];

  const submitPrompt = (event, suggestedPrompt) => {
    event?.preventDefault();
    const value = suggestedPrompt || prompt;
    if (!value.trim()) return;
    setIsThinking(true);
    setSubmittedPrompt("");
    window.setTimeout(() => {
      setSubmittedPrompt(value);
      setIsThinking(false);
    }, 650);
  };

  return (
    <div className="home-layout page-pad">
      <section className="home-primary">
        <div className="home-intro">
          <span className="ai-orb"><Sparkle size={22} weight="fill" /></span>
          <h1>Ask your model layer anything</h1>
          <p>Search, inspect, trace, validate, and review governed model knowledge.</p>
        </div>
        <form className="prompt-box" onSubmit={submitPrompt}>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Ask about models, fields, lineage, gaps, or proposals…"
            rows={2}
          />
          <div className="prompt-toolbar">
            <div>
              <button type="button" className="icon-button" aria-label="Attach context">
                <Paperclip size={19} />
              </button>
              <button type="button" className="context-button">
                <SlidersHorizontal size={18} />
                Context
              </button>
            </div>
            <button className="send-button" aria-label="Ask Martenweave" disabled={!prompt.trim()}>
              <ArrowUp size={18} weight="bold" />
            </button>
          </div>
        </form>
        <div className="suggestion-row" aria-label="Suggested questions">
          {suggestions.map((suggestion) => (
            <button key={suggestion} onClick={() => submitPrompt(null, suggestion)}>
              {suggestion}
              <ArrowRight size={14} />
            </button>
          ))}
        </div>

        <section className="answer-card" aria-live="polite">
          {!submittedPrompt && !isThinking ? (
            <div className="answer-empty">
              <ClockCounterClockwise size={21} />
              <span>Recent answer</span>
              <p>Ask a question to build an evidence-backed model view.</p>
            </div>
          ) : isThinking ? (
            <div className="thinking-state">
              <CircleNotch className="spin" size={22} />
              <span>Tracing canonical objects and validation evidence…</span>
            </div>
          ) : (
            <>
              <div className="question-row">
                <span className="avatar">AC</span>
                <div>
                  <strong>You</strong>
                  <p>{submittedPrompt}</p>
                </div>
              </div>
              <div className="assistant-row">
                <span className="assistant-mark"><Sparkle size={18} weight="fill" /></span>
                <div className="assistant-copy">
                  <div className="answer-byline">
                    <strong>Martenweave</strong>
                    <Badge tone="blue">Evidence-backed</Badge>
                  </div>
                  <p>
                    Business Partner has three unresolved field gaps. The highest-risk issue is
                    TAX_NUMBER because it affects migration validation, reporting, and two downstream
                    customer processes.
                  </p>
                  <div className="insight-grid">
                    <button onClick={() => navigate("gaps")}>
                      <span><WarningCircle size={19} /> Open gaps</span>
                      <strong>3 fields</strong>
                      <small>TAX_NUMBER, LANGUAGE, INDUSTRY</small>
                    </button>
                    <button onClick={() => navigate("lineage")}>
                      <span><ShareNetwork size={19} /> Impacted systems</span>
                      <strong>3 systems</strong>
                      <small>Sales Order, MDM, Analytics</small>
                    </button>
                    <button onClick={() => navigate("proposal")}>
                      <span><ShieldCheck size={19} /> Recommended action</span>
                      <strong>Review Proposal #27</strong>
                      <small>All required evidence is attached</small>
                    </button>
                  </div>
                  <div className="affected-table">
                    <div className="table-heading">
                      <strong>Affected fields</strong>
                      <button onClick={() => navigate("gaps")}>View all <ArrowRight size={14} /></button>
                    </div>
                    {gaps.slice(0, 3).map((gap) => (
                      <div className="affected-row" key={gap.id}>
                        <strong>{gap.title.replace(/.*: |Missing mapping for /, "")}</strong>
                        <span>{gap.source}</span>
                        <Badge tone={gap.severity.toLowerCase()}>{gap.severity}</Badge>
                        <span>{gap.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </section>
      </section>
      <aside className="home-rail">
        <RailSection title="Recent objects" action="View all" onAction={() => navigate("models")}>
          {modelObjects.slice(0, 4).map((item) => (
            <button className="rail-item" key={item.id} onClick={() => navigate("object")}>
              <IconTile type={item.label} size={34} />
              <span><strong>{item.name}</strong><small>{item.label}</small></span>
              <CaretRight size={14} />
            </button>
          ))}
        </RailSection>
        <RailSection title="Recent activity">
          {recentActivity.map(([action, subject, time], index) => (
            <div className="activity-item" key={action}>
              <span className={`activity-icon activity-${index}`}><CheckCircle size={16} /></span>
              <span><strong>{action}</strong><small>{subject}</small></span>
              <time>{time}</time>
            </div>
          ))}
        </RailSection>
      </aside>
    </div>
  );
}

function RailSection({ title, action, onAction, children }) {
  return (
    <section className="rail-section">
      <div className="rail-heading">
        <h2>{title}</h2>
        {action && <button onClick={onAction}>{action}</button>}
      </div>
      <div>{children}</div>
    </section>
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

function getHashSearchParam() {
  const hash = window.location.hash;
  const queryIndex = hash.indexOf("?");
  if (queryIndex === -1) return "";
  return new URLSearchParams(hash.slice(queryIndex + 1)).get("search") || "";
}

function ModelsScreen({ navigate }) {
  const [query, setQuery] = useState(() => getHashSearchParam() || "business partner");
  const [activeTab, setActiveTab] = useState("All");
  const [sort, setSort] = useState("Relevance");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedStatuses, setSelectedStatuses] = useState([]);
  const tabs = ["All", "Objects", "Fields", "Mappings", "Proposals"];
  const typeFilters = ["Domain", "Attribute", "Entity", "Mapping", "Proposal"];
  const statusFilters = ["Validated", "In review", "Draft"];

  const sortedResults = useMemo(() => {
    const filtered = modelObjects.filter((item) => {
      const matchesQuery =
        !query ||
        `${item.name} ${item.description} ${item.type}`.toLowerCase().includes(query.toLowerCase());
      const matchesTab =
        activeTab === "All" ||
        (activeTab === "Objects" && ["Domain", "Entity"].includes(item.label)) ||
        (activeTab === "Fields" && item.label === "Attribute") ||
        (activeTab === "Mappings" && item.label === "Mapping") ||
        (activeTab === "Proposals" && item.label === "Proposal");
      const matchesType = selectedTypes.length === 0 || selectedTypes.includes(item.label);
      const matchesStatus = selectedStatuses.length === 0 || selectedStatuses.includes(item.status);
      return matchesQuery && matchesTab && matchesType && matchesStatus;
    });
    const list = [...filtered];
    if (sort === "Name") {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sort === "Recently updated") {
      list.sort((a, b) => updatedMinutes(b.updated) - updatedMinutes(a.updated));
    }
    return list;
  }, [query, activeTab, selectedTypes, selectedStatuses, sort]);

  return (
    <div className="page-pad search-page">
      <PageHeader
        title="Global model search"
        description="Search across canonical objects, fields, mappings, datasets, and proposals."
      />
      <form className="global-search" onSubmit={(event) => event.preventDefault()}>
        <MagnifyingGlass size={21} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} />
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
        <span className="assistant-mark"><Sparkle size={17} weight="fill" /></span>
        <div>
          <span className="summary-title">AI answer <Badge tone="blue">Beta</Badge></span>
          <p>
            The canonical object is <strong>Business Partner</strong>. It is used by eight source
            systems, referenced by fourteen rules, and currently has three open field gaps.
          </p>
        </div>
        <button onClick={() => navigate("home")}>Ask follow-up <ArrowRight size={14} /></button>
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
          {sortedResults.length ? sortedResults.map((item) => (
            <button
              className="result-row"
              key={item.id}
              onClick={() => navigate(item.label === "Proposal" ? "proposal" : "object")}
            >
              <IconTile type={item.label} />
              <span className="result-copy">
                <span className="result-name"><Badge tone={item.label.toLowerCase()}>{item.label}</Badge><strong>{item.name}</strong></span>
                <span className="result-description">{item.description}</span>
                <span className="result-meta">
                  <span><Users size={14} /> {item.owners} owners</span>
                  <span><Database size={14} /> {item.systems} systems</span>
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

function ObjectScreen({ navigate }) {
  const [tab, setTab] = useState("Overview");
  const [copied, setCopied] = useState(false);
  const tabs = ["Overview", "Fields", "Relationships", "Governance"];
  const copyId = async () => {
    await navigator.clipboard?.writeText("DOMAIN-CUSTOMER-BP");
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="page-pad object-page">
      <button className="back-link" onClick={() => navigate("models")}>
        <CaretLeft size={15} /> Back to search
      </button>
      <div className="object-hero">
        <div className="object-identity">
          <IconTile type="Domain" size={58} />
          <div>
            <div className="object-type-row">
              <Badge tone="domain">Master data domain</Badge>
              <Badge tone="green"><CheckCircle size={13} /> Validated</Badge>
            </div>
            <h1>Business Partner</h1>
            <button className="copy-id" onClick={copyId}>
              DOMAIN-CUSTOMER-BP {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>
        <div className="page-actions">
          <button className="secondary-button"><Export size={17} /> Export</button>
          <button className="primary-button" onClick={() => navigate("lineage")}>
            <ShareNetwork size={17} /> Trace lineage
          </button>
          <button className="icon-button bordered"><DotsThreeVertical size={20} /></button>
        </div>
      </div>
      <p className="object-lead">
        Canonical representation of organizations and people that participate in commercial
        relationships. This domain connects SAP customer, vendor, CRM, MDM, and analytics models.
      </p>
      <div className="object-tabs">
        {tabs.map((item) => (
          <button className={tab === item ? "is-active" : ""} key={item} onClick={() => setTab(item)}>
            {item}
            {item === "Fields" && <span>{fields.length}</span>}
          </button>
        ))}
      </div>

      {tab === "Overview" && <ObjectOverview navigate={navigate} />}
      {tab === "Fields" && <FieldsTable />}
      {tab === "Relationships" && <Relationships navigate={navigate} />}
      {tab === "Governance" && <GovernancePanel />}
    </div>
  );
}

function ObjectOverview({ navigate }) {
  return (
    <div className="object-grid">
      <div className="object-main-column">
        <section className="surface overview-section">
          <div className="section-title"><div><h2>Model overview</h2><p>Canonical scope and operating context</p></div></div>
          <div className="definition-grid">
            <div><small>Business owner</small><strong>Customer Data Office</strong></div>
            <div><small>Technical steward</small><strong>Priya Nair</strong></div>
            <div><small>Lifecycle</small><strong>Active</strong></div>
            <div><small>Last validated</small><strong>Today, 10:18</strong></div>
          </div>
          <div className="narrative-block">
            <h3>Business definition</h3>
            <p>
              Business Partner is the canonical master record for any organization or person with
              whom the enterprise conducts business. It provides a stable semantic layer above
              source-system-specific customer and vendor structures.
            </p>
          </div>
          <div className="tag-row">
            <Tag size={16} />
            <Badge>SAP migration</Badge><Badge>MDM</Badge><Badge>Customer</Badge><Badge>Vendor</Badge>
          </div>
        </section>
        <section className="surface">
          <div className="section-title">
            <div><h2>Key fields</h2><p>Frequently referenced canonical attributes</p></div>
            <button>View all {fields.length} <ArrowRight size={14} /></button>
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
            <strong>93%</strong>
            <span>Validated</span>
          </div>
          <div className="progress-track"><span style={{ width: "93%" }} /></div>
          <ul>
            <li><CheckCircle size={17} /> 24 valid objects <strong>100%</strong></li>
            <li><WarningCircle size={17} /> 3 open field gaps <strong>Review</strong></li>
            <li><ShieldCheck size={17} /> Ownership coverage <strong>96%</strong></li>
          </ul>
          <button className="secondary-button full-width" onClick={() => navigate("gaps")}>
            Review open gaps
          </button>
        </section>
        <section className="surface">
          <div className="section-title"><div><h2>Connected systems</h2><p>8 upstream and downstream</p></div></div>
          {["SAP S/4HANA", "Salesforce CRM", "Informatica MDM", "Customer analytics"].map((system, index) => (
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
          <button className="data-table-row" key={field.id}>
            <span><strong>{field.name}</strong><small>{field.id}</small></span>
            <code>{field.type}</code>
            <span>{field.required ? "Required" : "Optional"}</span>
            <span>{field.usage}</span>
            <Badge tone={field.status === "Gap" ? "high" : field.status === "In review" ? "violet" : "green"}>{field.status}</Badge>
          </button>
        ))}
      </div>
    </section>
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
  return (
    <div className={`flow-node flow-node-${data.tone} ${selected ? "is-selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <span className="flow-node-icon"><Database size={19} weight="duotone" /></span>
      <span><strong>{data.label}</strong><small>{data.meta}</small></span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const nodeTypes = { model: ModelNode };

function LineageScreen({ navigate }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(lineageNodes);
  const [edges, , onEdgesChange] = useEdgesState(lineageEdges);
  const [depth, setDepth] = useState("2 levels");
  const [selected, setSelected] = useState("canonical");
  const [panelOpen, setPanelOpen] = useState(false);

  useEffect(() => {
    setNodes((current) => current.map((node) => ({ ...node, selected: node.id === selected })));
  }, [selected, setNodes]);

  return (
    <div className="lineage-page">
      <div className="lineage-header page-pad">
        <PageHeader
          title="Business Partner lineage"
          description="Trace systems, transformations, canonical objects, and downstream impact."
          actions={
            <>
              <button className="secondary-button"><Export size={17} /> Export</button>
              <button className="primary-button" onClick={() => navigate("object")}><Eye size={17} /> View object</button>
            </>
          }
        />
        <div className="lineage-toolbar">
          <label className="inline-search wide"><MagnifyingGlass size={17} /><input placeholder="Find a node or field…" /></label>
          <label className="select-control"><span>Depth</span><select value={depth} onChange={(event) => setDepth(event.target.value)}><option>1 level</option><option>2 levels</option><option>All levels</option></select></label>
          <button className="secondary-button"><Funnel size={17} /> Filters</button>
          <button className={`icon-button bordered ${panelOpen ? "is-active" : ""}`} onClick={() => setPanelOpen((value) => !value)}><SidebarSimple size={18} /></button>
        </div>
      </div>
      <div className="lineage-workspace">
        <div className="lineage-canvas">
          <div className="canvas-legend">
            <span><i className="legend-source" /> Source</span>
            <span><i className="legend-mapping" /> Transformation</span>
            <span><i className="legend-canonical" /> Canonical</span>
            <span><i className="legend-target" /> Target</span>
          </div>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
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
        {panelOpen && (
          <aside className="lineage-inspector">
            <div className="inspector-heading">
              <span><Badge tone="domain">Canonical model</Badge><h2>Business Partner</h2></span>
              <button className="icon-button" onClick={() => setPanelOpen(false)}><X size={18} /></button>
            </div>
            <p>Selected node details, validation context, and visible path evidence.</p>
            <div className="inspector-block">
              <small>Object ID</small>
              <code>DOMAIN-CUSTOMER-BP</code>
            </div>
            <div className="inspector-block">
              <small>Visible impact</small>
              <div className="metric-pair"><span><strong>2</strong> upstream</span><span><strong>2</strong> downstream</span></div>
            </div>
            <div className="inspector-block">
              <small>Path evidence</small>
              <ul className="path-list">
                <li><CheckCircle size={16} /> Salesforce → BP staging</li>
                <li><CheckCircle size={16} /> SAP S/4HANA → BP staging</li>
                <li><CheckCircle size={16} /> BP staging → Canonical</li>
              </ul>
            </div>
            <button className="primary-button full-width" onClick={() => navigate("object")}>Open object details</button>
            <button className="secondary-button full-width" onClick={() => navigate("gaps")}>Review related gaps</button>
          </aside>
        )}
      </div>
    </div>
  );
}

function GapsScreen({ navigate }) {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("All severities");
  const [sort, setSort] = useState("Risk first");
  const [expandedId, setExpandedId] = useState(1);
  const shown = gaps.filter((gap) => {
    const matchesQuery = `${gap.title} ${gap.object} ${gap.source}`.toLowerCase().includes(query.toLowerCase());
    return matchesQuery && (severity === "All severities" || gap.severity === severity);
  });

  return (
    <div className="page-pad gaps-page">
      <PageHeader
        title="Open gaps"
        description="Review missing mappings, inconsistent types, and unresolved model coverage."
        actions={<button className="primary-button"><Plus size={17} /> Create issue</button>}
      />
      <div className="gap-controls">
        <label className="inline-search wide"><MagnifyingGlass size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search gaps by field, object, or source…" /></label>
        <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
          <option>All severities</option><option>High</option><option>Medium</option><option>Low</option>
        </select>
        <select value={sort} onChange={(event) => setSort(event.target.value)}>
          <option>Risk first</option><option>Recently detected</option><option>Object name</option>
        </select>
        <button className="secondary-button"><Funnel size={17} /> More filters</button>
      </div>
      <div className="gaps-layout">
        <section className="gap-list">
          {shown.map((gap) => {
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
                      <button className="secondary-button">View details</button>
                      <button className="primary-button" onClick={() => navigate(gap.proposal === "—" ? "proposals" : "proposal")}>
                        {gap.proposal === "—" ? "Create proposal" : "Review proposal"}
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
          })}
        </section>
        <aside className="gaps-rail">
          <section className="surface gap-summary">
            <div className="section-title"><div><h2>Gap summary</h2><p>Current model coverage</p></div><Info size={17} /></div>
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
          <section className="surface assistant-suggestion">
            <span className="assistant-mark"><Sparkle size={17} weight="fill" /></span>
            <h2>Recommended next step</h2>
            <div>
              <strong>Review Proposal #27</strong>
              <p>It addresses the highest-risk gap and includes all required evidence.</p>
              <button className="primary-button full-width" onClick={() => navigate("proposal")}>Review proposal</button>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function ProposalsScreen({ navigate }) {
  const [tab, setTab] = useState("All");
  const [query, setQuery] = useState("");
  const shown = proposals.filter((proposal) => {
    const matchesTab = tab === "All" || proposal.status === tab;
    const matchesQuery = `${proposal.title} ${proposal.summary}`.toLowerCase().includes(query.toLowerCase());
    return matchesTab && matchesQuery;
  });
  return (
    <div className="page-pad proposals-page">
      <PageHeader
        title="Proposals"
        description="Review AI-assisted model changes before they become canonical."
        actions={<button className="primary-button"><Plus size={17} /> New proposal</button>}
      />
      <div className="proposal-toolbar">
        <div className="segmented-control">
          {["All", "In review", "Draft", "Approved"].map((item) => <button className={tab === item ? "is-active" : ""} key={item} onClick={() => setTab(item)}>{item}</button>)}
        </div>
        <label className="inline-search"><MagnifyingGlass size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search proposals" /></label>
      </div>
      <div className="proposal-list">
        {shown.map((proposal) => (
          <button className="proposal-row" key={proposal.id} onClick={() => navigate("proposal")}>
            <span className="proposal-number">#{proposal.id}</span>
            <span className="proposal-copy">
              <span><Badge tone={proposal.status === "In review" ? "violet" : "neutral"}>{proposal.status}</Badge><Badge tone={proposal.risk.toLowerCase()}>{proposal.risk} risk</Badge></span>
              <strong>{proposal.title}</strong>
              <p>{proposal.summary}</p>
              <small>{proposal.changes} proposed changes · {proposal.author} · Updated {proposal.updated}</small>
            </span>
            <span className="proposal-review">Review <ArrowRight size={16} /></span>
          </button>
        ))}
      </div>
    </div>
  );
}

function ProposalScreen({ navigate }) {
  const [tab, setTab] = useState("Changes");
  const [decision, setDecision] = useState(null);
  const [comment, setComment] = useState("");
  const [savedComment, setSavedComment] = useState("");

  return (
    <div className="proposal-review-page">
      <div className="proposal-review-header page-pad">
        <button className="back-link" onClick={() => navigate("proposals")}><CaretLeft size={15} /> Back to proposals</button>
        <div className="proposal-title-row">
          <div>
            <div className="object-type-row"><Badge tone="violet">In review</Badge><Badge tone="high">High impact</Badge></div>
            <h1>Customer alternative key mapping</h1>
            <p>Proposal #27 · Created by Martenweave AI · Updated 18 minutes ago</p>
          </div>
          <div className="page-actions">
            <button className="danger-button" onClick={() => setDecision("reject")}><XCircle size={17} /> Request changes</button>
            <button className="approve-button" onClick={() => setDecision("approve")}><CheckCircle size={17} /> Approve proposal</button>
          </div>
        </div>
      </div>
      <div className="proposal-review-body">
        <div className="review-main">
          <section className="proposal-summary-strip">
            <div><small>Risk classification</small><strong><WarningCircle size={16} /> High</strong></div>
            <div><small>Canonical objects</small><strong>2 affected</strong></div>
            <div><small>Proposed changes</small><strong>4 changes</strong></div>
            <div><small>Validation</small><strong><CheckCircle size={16} /> Passed</strong></div>
          </section>
          <div className="review-tabs">
            {["Changes", "Impact", "Validation", "Activity"].map((item) => <button className={tab === item ? "is-active" : ""} key={item} onClick={() => setTab(item)}>{item}</button>)}
          </div>
          {tab === "Changes" && <ProposalChanges />}
          {tab === "Impact" && <ProposalImpact navigate={navigate} />}
          {tab === "Validation" && <ProposalValidation />}
          {tab === "Activity" && <ProposalActivity />}
        </div>
        <aside className="review-sidebar">
          <section className="surface">
            <div className="section-title"><div><h2>Review context</h2><p>Why this change exists</p></div></div>
            <p className="review-context">
              TAX_NUMBER is missing from the Business Partner mapping. The proposal adds a canonical
              endpoint and links SAP field KNVV.STCD1 with deterministic transform evidence.
            </p>
            <button className="linked-gap" onClick={() => navigate("gaps")}>
              <WarningCircle size={18} />
              <span><small>Linked gap</small><strong>Missing mapping for TAX_NUMBER</strong></span>
              <CaretRight size={15} />
            </button>
          </section>
          <section className="surface">
            <div className="section-title"><div><h2>Reviewers</h2><p>1 of 2 approvals received</p></div></div>
            <div className="reviewer-row"><span className="avatar avatar-soft">PN</span><span><strong>Priya Nair</strong><small>Data steward</small></span><CheckCircle size={18} weight="fill" /></div>
            <div className="reviewer-row"><span className="avatar avatar-soft">AC</span><span><strong>Alex Chen</strong><small>Your review</small></span><Badge>Pending</Badge></div>
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
        <DecisionDialog type={decision} onClose={() => setDecision(null)} onConfirm={() => { setDecision(null); navigate("proposals"); }} />
      )}
    </div>
  );
}

function ProposalChanges() {
  const [view, setView] = useState("Side by side");
  return (
    <section className="change-section">
      <div className="change-section-heading">
        <div><h2>Proposed canonical changes</h2><p>Review every mutation before approval.</p></div>
        <div className="view-toggle"><button className={view === "Side by side" ? "is-active" : ""} onClick={() => setView("Side by side")}><Columns size={16} /> Side by side</button><button className={view === "Unified" ? "is-active" : ""} onClick={() => setView("Unified")}><List size={16} /> Unified</button></div>
      </div>
      <article className="diff-card">
        <header>
          <span><FileText size={18} /> model/ATTR-BP-TAX-NUMBER.md</span>
          <Badge tone="green">New object</Badge>
        </header>
        <div className={`diff-body ${view === "Unified" ? "is-unified" : ""}`}>
          {view === "Side by side" && (
            <div className="diff-pane before">
              <div className="diff-pane-label">Current</div>
              <div className="diff-empty"><FileText size={23} /><span>Object does not exist</span></div>
            </div>
          )}
          <div className="diff-pane after">
            <div className="diff-pane-label">Proposed</div>
            <pre>{`---
id: ATTR-BP-TAX-NUMBER
type: Attribute
status: draft
name: Tax Number
domain: DOMAIN-CUSTOMER-BP
---

# Tax Number

Tax identification number used for
reporting and partner matching.`}</pre>
          </div>
        </div>
      </article>
      <article className="diff-card">
        <header>
          <span><GitDiff size={18} /> model/MAP-SAP-BP-TAX-NUMBER.md</span>
          <Badge tone="blue">Modified</Badge>
        </header>
        <div className="field-diff">
          <div><small>Field</small><strong>target_endpoint</strong></div>
          <div className="removed-value"><small>Current</small><code>—</code></div>
          <ArrowRight size={16} />
          <div className="added-value"><small>Proposed</small><code>ATTR-BP-TAX-NUMBER</code></div>
        </div>
        <div className="field-diff">
          <div><small>Field</small><strong>transform</strong></div>
          <div className="removed-value"><small>Current</small><code>—</code></div>
          <ArrowRight size={16} />
          <div className="added-value"><small>Proposed</small><code>trim · uppercase · validate</code></div>
        </div>
      </article>
    </section>
  );
}

function ProposalImpact({ navigate }) {
  return (
    <section className="change-section">
      <div className="change-section-heading"><div><h2>Impact analysis</h2><p>Deterministic BFS traversal from changed objects.</p></div><button className="secondary-button" onClick={() => navigate("lineage")}><ShareNetwork size={17} /> Open lineage</button></div>
      <div className="impact-grid">
        {[["Directly changed", "2", FileText], ["Downstream objects", "6", GitBranch], ["Source systems", "3", Database], ["High-risk paths", "1", WarningCircle]].map(([label, value, Icon]) => (
          <div className="surface" key={label}><Icon size={20} /><strong>{value}</strong><span>{label}</span></div>
        ))}
      </div>
      <section className="surface impact-paths">
        <h3>Highest-risk path</h3>
        <div><span>SAP S/4HANA</span><ArrowRight size={15} /><span>KNVV.STCD1</span><ArrowRight size={15} /><span>Tax Number</span><ArrowRight size={15} /><span>Customer analytics</span></div>
      </section>
    </section>
  );
}

function ProposalValidation() {
  return (
    <section className="change-section">
      <div className="change-section-heading"><div><h2>Validation evidence</h2><p>Deterministic checks executed before review.</p></div><Badge tone="green"><CheckCircle size={14} /> All checks passed</Badge></div>
      <div className="validation-list">
        {[
          ["Schema validation", "Object structure matches the registered Attribute and Mapping schemas."],
          ["Reference integrity", "All proposed object references resolve to valid canonical IDs."],
          ["SAP context", "KNVV source endpoint matches the customer_sales_area context."],
          ["ID uniqueness", "No duplicate stable IDs were found in the repository."],
        ].map(([title, description]) => (
          <div className="surface validation-row" key={title}><span className="validation-check"><Check size={16} weight="bold" /></span><span><strong>{title}</strong><small>{description}</small></span><Badge tone="green">Passed</Badge></div>
        ))}
      </div>
    </section>
  );
}

function ProposalActivity() {
  return (
    <section className="change-section">
      <div className="change-section-heading"><div><h2>Proposal activity</h2><p>Immutable review and validation history.</p></div></div>
      <div className="timeline">
        {[
          ["Proposal generated", "Martenweave AI created four patch operations from gap evidence.", "18m ago", Sparkle],
          ["Validation completed", "All deterministic repository checks passed.", "16m ago", ShieldCheck],
          ["Impact analysis completed", "Six downstream objects and one high-risk path detected.", "15m ago", ShareNetwork],
          ["Priya Nair approved", "Data stewardship review completed.", "7m ago", CheckCircle],
        ].map(([title, description, time, Icon]) => (
          <div key={title}><span className="timeline-icon"><Icon size={16} /></span><span><strong>{title}</strong><small>{description}</small></span><time>{time}</time></div>
        ))}
      </div>
    </section>
  );
}

function DecisionDialog({ type, onClose, onConfirm }) {
  const approve = type === "approve";
  const [reason, setReason] = useState("");
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="decision-dialog" role="dialog" aria-modal="true" aria-labelledby="decision-title" onMouseDown={(event) => event.stopPropagation()}>
        <button className="icon-button dialog-close" onClick={onClose}><X size={18} /></button>
        <span className={`dialog-icon ${approve ? "approve" : "reject"}`}>{approve ? <SealCheck size={24} /> : <XCircle size={24} />}</span>
        <h2 id="decision-title">{approve ? "Approve Proposal #27?" : "Request changes?"}</h2>
        <p>{approve ? "Approval creates a governed change request. Canonical files are not modified until that change request is applied." : "Send the proposal back with a clear reason for the author."}</p>
        <label><span>{approve ? "Approval note (optional)" : "Required changes"}</span><textarea rows={3} value={reason} onChange={(event) => setReason(event.target.value)} placeholder={approve ? "Add a short review note…" : "Explain what must change…"} /></label>
        <div className="dialog-actions">
          <button className="secondary-button" onClick={onClose}>Cancel</button>
          <button className={approve ? "approve-button" : "danger-button"} disabled={!approve && !reason.trim()} onClick={onConfirm}>{approve ? <><CheckCircle size={17} /> Approve</> : <><XCircle size={17} /> Request changes</>}</button>
        </div>
      </div>
    </div>
  );
}

export function App() {
  const [route, params, navigate] = useRoute();
  const [notice, setNotice] = useState("");
  const utilityActions = {
    Export: "Export prepared for the current workspace.",
    "Create issue": "Issue draft opened with the current gap context.",
    "More filters": "Additional source, owner, and status filters are ready.",
    "New proposal": "New proposal workspace opened in draft mode.",
    Context: "Model, lineage, and validation context are attached.",
    "Attach context": "Choose model evidence to attach to this question.",
  };
  const screen = {
    home: <HomeScreen navigate={navigate} />,
    models: <ModelsScreen navigate={navigate} />,
    object: <ObjectScreen navigate={navigate} params={params} />,
    lineage: <LineageScreen navigate={navigate} params={params} />,
    gaps: <GapsScreen navigate={navigate} params={params} />,
    proposals: <ProposalsScreen navigate={navigate} />,
    proposal: <ProposalScreen navigate={navigate} params={params} />,
  }[route] || <HomeScreen navigate={navigate} />;

  return (
    <div
      onClickCapture={(event) => {
        const button = event.target.closest("button");
        if (!button) return;
        const label = button.getAttribute("aria-label") || button.textContent.trim();
        const message = utilityActions[label];
        if (!message) return;
        setNotice(message);
        window.setTimeout(() => setNotice(""), 2400);
      }}
    >
      <AppShell route={route} navigate={navigate}>{screen}</AppShell>
      {notice && <div className="app-toast" role="status"><CheckCircle size={18} /> {notice}</div>}
    </div>
  );
}

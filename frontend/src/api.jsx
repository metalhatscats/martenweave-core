/**
 * Typed local API client and connection state for the Martenweave workbench.
 *
 * The client talks to the versioned `/api/v1` namespace exposed by
 * `martenweave serve`. When the API is unreachable, incompatible, or missing an
 * index, components fall back to the static demo fixtures in `data.js` and
 * surface the connection state visibly.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { lineageEdges, lineageNodes, modelObjects } from "./data.js";

/**
 * @typedef {object} Capability
 * @property {string} name
 * @property {string} method
 * @property {string} href
 * @property {string} description
 */

/**
 * @typedef {object} CapabilitiesResponse
 * @property {string} version
 * @property {string} api_version
 * @property {string} repository
 * @property {boolean} indexed
 * @property {number} canonical_files
 * @property {boolean} read_only
 * @property {Capability[]} read
 * @property {Capability[]} mutations
 * @property {RecoveryAction[]} recovery
 */

/**
 * @typedef {object} RecoveryAction
 * @property {string} code
 * @property {string} label
 * @property {string|null} command
 * @property {boolean} requires_confirmation
 */

/**
 * @typedef {object} SearchResult
 * @property {string} object_id
 * @property {string} object_type
 * @property {string} status
 * @property {string|null} name
 * @property {string|null} title
 * @property {string|null} domain
 * @property {string|null} description
 * @property {string} source_file
 * @property {number} score
 * @property {string[]} matched_fields
 */

/**
 * @typedef {object} SearchResponse
 * @property {number} total_count
 * @property {SearchResult[]} results
 */

/**
 * @typedef {object} RelatedObject
 * @property {string} to_object_id
 * @property {string} relationship_type
 * @property {string} relationship_class
 */

/**
 * @typedef {object} ObjectDetailResponse
 * @property {Record<string, any>} object
 * @property {RelatedObject[]} relationships
 */

/**
 * @typedef {object} TraceNode
 * @property {string} object_id
 * @property {string} object_type
 * @property {string} object_name
 * @property {string} source_file
 * @property {number} depth
 */

/**
 * @typedef {object} TraceEdge
 * @property {string} from_object_id
 * @property {string} to_object_id
 * @property {string} relationship_type
 * @property {string} direction
 */

/**
 * @typedef {object} TraceResponse
 * @property {string} root_object_id
 * @property {string} root_object_type
 * @property {string} root_object_name
 * @property {TraceNode[]} nodes
 * @property {TraceEdge[]} edges
 */

/**
 * @typedef {object} ImpactObject
 * @property {string} object_id
 * @property {string} object_type
 * @property {string} object_name
 * @property {string} relationship_type
 * @property {number} depth
 */

/**
 * @typedef {object} ImpactResponse
 * @property {string} object_id
 * @property {string} root_object_type
 * @property {string} root_object_name
 * @property {ImpactObject[]} upstream
 * @property {ImpactObject[]} downstream
 * @property {number} total_affected
 */

/**
 * @typedef {object} ApiClient
 * @property {(params?: {q?: string, type?: string, status?: string, domain?: string, limit?: number, offset?: number}) => Promise<SearchResponse>} search
 * @property {(id: string) => Promise<ObjectDetailResponse>} object
 * @property {(id: string, opts?: {direction?: string, max_depth?: number}) => Promise<TraceResponse>} trace
 * @property {(id: string) => Promise<ImpactResponse>} impact
 * @property {() => Promise<CapabilitiesResponse>} capabilities
 * @property {(limit?: number) => Promise<ActivityResponse>} activity
 */

/**
 * @typedef {object} ActivityEvent
 * @property {string} event_id
 * @property {string} event_type
 * @property {string} timestamp
 * @property {string|null} actor
 * @property {string} status
 * @property {string|null} proposal_id
 * @property {string[]} changed_object_ids
 * @property {string|null} validation_status
 * @property {"canonical"|"generated"} source_state
 * @property {boolean} canonical_change
 */

/**
 * @typedef {object} ActivityResponse
 * @property {number} total_count
 * @property {ActivityEvent[]} events
 */

export const API_STATE = {
  UNKNOWN: "unknown",
  CONNECTED: "connected",
  UNAVAILABLE: "unavailable",
  STALE_INDEX: "stale_index",
  INCOMPATIBLE: "incompatible",
};

const EXPECTED_API_VERSION = "v1";

const DEFAULT_API_BASE_URL =
  import.meta.env?.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Map a canonical object type to the short label used by the workbench UI.
 *
 * @param {string} type
 * @returns {string}
 */
function typeToLabel(type) {
  switch (type) {
    case "MasterDataDomain":
      return "Domain";
    case "Attribute":
      return "Attribute";
    case "BusinessEntity":
      return "Entity";
    case "Mapping":
      return "Mapping";
    case "PatchProposal":
      return "Proposal";
    case "FieldEndpoint":
      return "Endpoint";
    case "EntityContext":
      return "Context";
    case "ValueList":
      return "ValueList";
    case "Decision":
      return "Decision";
    case "Issue":
      return "Issue";
    default:
      return type;
  }
}

/**
 * Convert an API object frontmatter into the view model shape used by the
 * workbench screens.
 *
 * @param {Record<string, any>} obj
 * @returns {import("./data.js").ModelObject}
 */
export function apiObjectToViewModel(obj) {
  const type = obj.type || "Unknown";
  const label = typeToLabel(type);
  const tags = Array.isArray(obj.tags)
    ? obj.tags
    : obj.tags
      ? [String(obj.tags)]
      : [];
  const systems = Array.isArray(obj.systems)
    ? obj.systems
    : obj.source_systems
      ? [String(obj.source_systems)]
      : [];
  const ownerCount = [obj.business_owner, obj.technical_owner, obj.data_steward].filter(
    Boolean
  ).length;

  return {
    id: obj.id,
    type,
    label,
    name: obj.name || obj.title || obj.id,
    description: obj.description || "",
    fullDescription: obj.description || "",
    status: obj.status || "Draft",
    owners: ownerCount,
    updated: "Live",
    businessOwner: obj.business_owner || "—",
    technicalSteward: obj.technical_owner || "—",
    lifecycle: obj.status || "Draft",
    lastValidated: "—",
    tags,
    health: obj.health || 0,
    systems,
  };
}

/**
 * Create an API client bound to a base URL.
 *
 * @param {string} baseUrl
 * @returns {ApiClient}
 */
export function createApiClient(baseUrl) {
  const root = baseUrl.replace(/\/$/, "");

  async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
      const text = await response.text().catch(() => "Unknown error");
      throw new Error(`${response.status}: ${text}`);
    }
    return response.json();
  }

  return {
    capabilities: () => fetchJson(`${root}/api/v1/capabilities`),
    activity: (limit = 50) => fetchJson(`${root}/api/v1/activity?limit=${encodeURIComponent(limit)}`),
    reports: (limit = 100) => fetchJson(`${root}/api/v1/reports?limit=${encodeURIComponent(limit)}`),
    reportDownloadUrl: (artifactId) => `${root}/api/v1/reports/${artifactId.split("/").map(encodeURIComponent).join("/")}`,
    findings: () => fetchJson(`${root}/api/v1/findings`),
    assessmentManifests: () => fetchJson(`${root}/api/v1/assessment-manifests`),
    compareAssessments: (base, head) => fetchJson(`${root}/api/v1/assessment-comparisons?${new URLSearchParams({ base_manifest: base, head_manifest: head })}`),
    search: ({ q, type, status, domain, limit = 50, offset = 0 } = {}) => {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (type) params.set("type", type);
      if (status) params.set("status", status);
      if (domain) params.set("domain", domain);
      params.set("limit", String(limit));
      params.set("offset", String(offset));
      return fetchJson(`${root}/api/v1/search?${params.toString()}`);
    },
    object: (id) => fetchJson(`${root}/api/v1/objects/${encodeURIComponent(id)}`),
    trace: (id, { direction = "both", max_depth = 5 } = {}) => {
      const params = new URLSearchParams();
      params.set("direction", direction);
      params.set("max_depth", String(max_depth));
      return fetchJson(`${root}/trace/${encodeURIComponent(id)}?${params.toString()}`);
    },
    impact: (id) => fetchJson(`${root}/impact/${encodeURIComponent(id)}`),
  };
}

/**
 * @typedef {object} ApiContextValue
 * @property {string} state
 * @property {boolean} demo
 * @property {ApiClient|null} client
 * @property {string|null} error
 * @property {CapabilitiesResponse|null} capabilities
 * @property {RecoveryAction|null} recovery
 */

/**
 * @type {React.Context<ApiContextValue>}
 */
export const ApiContext = createContext({
  state: API_STATE.UNKNOWN,
  demo: true,
  client: null,
  error: null,
  capabilities: null,
  recovery: null,
});

/**
 * Provide the API connection state to the workbench.
 *
 * @param {{ children: React.ReactNode, baseUrl?: string }} props
 */
export function ApiProvider({ children, baseUrl = DEFAULT_API_BASE_URL }) {
  const client = useMemo(() => createApiClient(baseUrl), [baseUrl]);
  const [value, setValue] = useState(() => ({
    state: API_STATE.UNKNOWN,
    demo: true,
    client,
    error: null,
    capabilities: null,
    recovery: null,
  }));

  const probe = useCallback(async () => {
    try {
      const capabilities = await client.capabilities();
      if (capabilities.api_version !== EXPECTED_API_VERSION) {
        setValue({ state: API_STATE.INCOMPATIBLE, demo: true, client, error: `API version ${capabilities.api_version} is not supported`, capabilities, recovery: null, retry: probe });
        return;
      }
      if (!capabilities.indexed) {
        setValue({ state: API_STATE.STALE_INDEX, demo: true, client, error: "Index is missing. Run build-index first.", capabilities, recovery: capabilities.recovery?.find((action) => action.code === "BUILD_INDEX") || null, retry: probe });
        return;
      }
      setValue({ state: API_STATE.CONNECTED, demo: false, client, error: null, capabilities, recovery: null, retry: probe });
    } catch (err) {
      setValue({ state: API_STATE.UNAVAILABLE, demo: true, client, error: err instanceof Error ? err.message : String(err), capabilities: null, recovery: null, retry: probe });
    }
  }, [client]);

  useEffect(() => {
    probe();
    return undefined;
  }, [probe]);

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
}

/**
 * Access the current API connection state.
 *
 * @returns {ApiContextValue}
 */
export function useApi() {
  return useContext(ApiContext);
}

/**
 * Filter the static demo objects by query and type/status filters.
 *
 * @param {string} query
 * @param {import("./data.js").ModelObject[]} objects
 * @param {string} activeTab
 * @param {string[]} selectedTypes
 * @param {string[]} selectedStatuses
 * @returns {import("./data.js").ModelObject[]}
 */
function filterDemoObjects(query, objects, activeTab, selectedTypes, selectedStatuses, applyQuery = true) {
  const q = query.trim().toLowerCase();
  return objects.filter((item) => {
    const text = `${item.name} ${item.description} ${item.type}`.toLowerCase();
    const matchesQuery = !applyQuery || !q || text.includes(q);
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
}

/**
 * Search canonical objects through the live API, falling back to demo data.
 *
 * @param {string} query
 * @param {string} activeTab
 * @param {string[]} selectedTypes
 * @param {string[]} selectedStatuses
 * @param {string} sort
 * @returns {{ results: import("./data.js").ModelObject[], loading: boolean, error: string|null }}
 */
export function useObjectSearch(query, activeTab, selectedTypes, selectedStatuses, sort) {
  const { state, client, demo } = useApi();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (demo || !client) {
      setResults(
        filterDemoObjects(query, modelObjects, activeTab, selectedTypes, selectedStatuses)
      );
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    async function load() {
      try {
        const response = await client.search({ q: query });
        if (cancelled) return;
        const mapped = response.results.map((r) =>
          apiObjectToViewModel({
            id: r.object_id,
            type: r.object_type,
            status: r.status,
            name: r.name,
            title: r.title,
            description: r.description,
            domain: r.domain,
          })
        );
        setResults(
          filterDemoObjects(query, mapped, activeTab, selectedTypes, selectedStatuses, false)
        );
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : String(err));
        setResults([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [query, activeTab, selectedTypes.join(","), selectedStatuses.join(","), sort, demo, client]);

  const sortedResults = useMemo(() => {
    const list = [...results];
    const q = query.trim().toLowerCase();
    if (sort === "Relevance") {
      if (!q) {
        list.sort((a, b) => a.name.localeCompare(b.name));
      } else {
        list.sort((a, b) => {
          const aName = a.name.toLowerCase().includes(q);
          const bName = b.name.toLowerCase().includes(q);
          if (aName !== bName) return bName - aName;
          const aDesc = a.description.toLowerCase().includes(q);
          const bDesc = b.description.toLowerCase().includes(q);
          return bDesc - aDesc;
        });
      }
    } else if (sort === "Name") {
      list.sort((a, b) => a.name.localeCompare(b.name));
    }
    return list;
  }, [results, sort, query]);

  return { results: sortedResults, loading, error };
}

/**
 * Fetch a single canonical object through the live API, falling back to demo data.
 *
 * @param {string|null} objectId
 * @returns {{ object: import("./data.js").ModelObject|null, loading: boolean, error: string|null }}
 */
export function useObjectDetail(objectId) {
  const { client, demo } = useApi();
  const [object, setObject] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!objectId) {
      setObject(null);
      return;
    }

    if (demo || !client) {
      setObject(modelObjects.find((item) => item.id === objectId) || modelObjects[0]);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    async function load() {
      try {
        const response = await client.object(objectId);
        if (cancelled) return;
        setObject(apiObjectToViewModel(response.object));
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : String(err));
        setObject(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [objectId, demo, client]);

  return { object, loading, error };
}

/**
 * Read real, append-only workspace activity while retaining a clearly demo-only fallback offline.
 *
 * @returns {{ events: ActivityEvent[], loading: boolean, error: string|null, demo: boolean }}
 */
export function useWorkspaceActivity() {
  const { client, demo } = useApi();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (demo || !client) {
      setEvents([]);
      setLoading(false);
      setError(null);
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    client.activity()
      .then((response) => {
        if (!cancelled) {
          setEvents(response.events);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setEvents([]);
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [client, demo]);

  return { events, loading, error, demo };
}

/** Read typed assessment findings with review state from the active local workspace. */
export function useAssessmentFindings() {
  const { client, demo } = useApi();
  const [findings, setFindings] = useState([]);
  const [assessmentId, setAssessmentId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (demo || !client) {
      setFindings([]);
      setAssessmentId(null);
      setLoading(false);
      setError(null);
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    client.findings()
      .then((response) => {
        if (!cancelled) {
          setFindings(response.findings);
          setAssessmentId(response.assessment_id);
          setError(null);
        }
      })
      .catch((reason) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : String(reason));
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [client, demo]);

  return { findings, assessmentId, loading, error, demo };
}


/**
 * Map a canonical object type to a lineage layer tone.
 *
 * @param {string} type
 * @returns {string}
 */
export function objectTypeToTone(type) {
  switch (type) {
    case "MasterDataDomain":
    case "BusinessEntity":
      return "canonical";
    case "Mapping":
      return "mapping";
    case "Attribute":
    case "ValueList":
      return "target";
    case "FieldEndpoint":
      return "source";
    case "PatchProposal":
      return "proposal";
    case "Decision":
      return "decision";
    case "Issue":
      return "gap";
    default:
      return "target";
  }
}

/**
 * Build ReactFlow nodes from a trace response.
 *
 * @param {TraceResponse} trace
 * @returns {Array<{id: string, position: {x: number, y: number}, data: {label: string, meta: string, tone: string}, type: string}>}
 */
export function traceResponseToFlowNodes(trace) {
  const rootId = trace.root_object_id;
  const upstreamIds = new Set(
    trace.edges
      .filter((e) => e.direction === "upstream")
      .map((e) => e.from_object_id)
  );

  const upstreamNodes = trace.nodes.filter((n) => upstreamIds.has(n.object_id));
  const downstreamNodes = trace.nodes.filter((n) => !upstreamIds.has(n.object_id));

  const layoutGroup = (list, sign) =>
    list.map((node, index) => {
      const count = list.length;
      const yOffset = (index - (count - 1) / 2) * 90;
      return {
        id: node.object_id,
        position: { x: sign * node.depth * 260, y: yOffset },
        data: {
          label: node.object_name || node.object_id,
          meta: `${node.object_type} · ${node.object_id}`,
          tone: objectTypeToTone(node.object_type),
        },
        type: "model",
      };
    });

  return [
    {
      id: rootId,
      position: { x: 0, y: 0 },
      data: {
        label: trace.root_object_name || rootId,
        meta: `${trace.root_object_type || "Object"} · ${rootId}`,
        tone: "canonical",
      },
      type: "model",
    },
    ...layoutGroup(upstreamNodes, -1),
    ...layoutGroup(downstreamNodes, 1),
  ];
}

/**
 * Build ReactFlow edges from a trace response.
 *
 * @param {TraceResponse} trace
 * @returns {Array<{id: string, source: string, target: string, label?: string, animated?: boolean}>}
 */
export function traceResponseToFlowEdges(trace) {
  return trace.edges.map((edge, index) => ({
    id: `e-${index}`,
    source: edge.from_object_id,
    target: edge.to_object_id,
    label: edge.relationship_type,
    animated: edge.direction === "downstream",
  }));
}

/**
 * Fetch trace and impact data for an object, falling back to demo lineage fixtures.
 *
 * @param {string|null} objectId
 * @param {string} direction
 * @param {number} maxDepth
 * @returns {{
 *   nodes: ReturnType<typeof traceResponseToFlowNodes>,
 *   edges: ReturnType<typeof traceResponseToFlowEdges>,
 *   upstream: TraceNode[],
 *   downstream: TraceNode[],
 *   impact: ImpactResponse|null,
 *   loading: boolean,
 *   error: string|null
 * }}
 */
export function useLineage(objectId, direction, maxDepth) {
  const { client, demo } = useApi();
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [upstream, setUpstream] = useState([]);
  const [downstream, setDownstream] = useState([]);
  const [impact, setImpact] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!objectId) {
      setNodes([]);
      setEdges([]);
      return;
    }

    if (demo || !client) {
      setNodes(lineageNodes);
      setEdges(lineageEdges);
      setUpstream([]);
      setDownstream([]);
      setImpact(null);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    async function load() {
      try {
        const [trace, impactData] = await Promise.all([
          client.trace(objectId, { direction, max_depth: maxDepth }),
          client.impact(objectId),
        ]);
        if (cancelled) return;
        setNodes(traceResponseToFlowNodes(trace));
        setEdges(traceResponseToFlowEdges(trace));
        const upstreamIds = new Set(
          trace.edges.filter((e) => e.direction === "upstream").map((e) => e.from_object_id)
        );
        setUpstream(trace.nodes.filter((n) => upstreamIds.has(n.object_id)));
        setDownstream(trace.nodes.filter((n) => !upstreamIds.has(n.object_id)));
        setImpact(impactData);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : String(err));
        setNodes([]);
        setEdges([]);
        setUpstream([]);
        setDownstream([]);
        setImpact(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [objectId, direction, maxDepth, demo, client]);

  return { nodes, edges, upstream, downstream, impact, loading, error };
}

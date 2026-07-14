/**
 * Typed local API client and connection state for the Martenweave workbench.
 *
 * The client talks to the versioned `/api/v1` namespace exposed by
 * `martenweave serve`. When the API is unreachable, incompatible, or missing an
 * index, components fall back to the static demo fixtures in `data.js` and
 * surface the connection state visibly.
 */

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { modelObjects } from "./data.js";

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
 * @typedef {object} ApiClient
 * @property {(params?: {q?: string, type?: string, status?: string, domain?: string, limit?: number, offset?: number}) => Promise<SearchResponse>} search
 * @property {(id: string) => Promise<ObjectDetailResponse>} object
 * @property {() => Promise<CapabilitiesResponse>} capabilities
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
  };
}

/**
 * @typedef {object} ApiContextValue
 * @property {string} state
 * @property {boolean} demo
 * @property {ApiClient|null} client
 * @property {string|null} error
 * @property {CapabilitiesResponse|null} capabilities
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
  }));

  useEffect(() => {
    let cancelled = false;

    async function probe() {
      try {
        const capabilities = await client.capabilities();
        if (cancelled) return;

        if (capabilities.api_version !== EXPECTED_API_VERSION) {
          setValue({
            state: API_STATE.INCOMPATIBLE,
            demo: true,
            client,
            error: `API version ${capabilities.api_version} is not supported`,
            capabilities,
          });
          return;
        }

        if (!capabilities.indexed) {
          setValue({
            state: API_STATE.STALE_INDEX,
            demo: true,
            client,
            error: "Index is missing. Run build-index first.",
            capabilities,
          });
          return;
        }

        setValue({
          state: API_STATE.CONNECTED,
          demo: false,
          client,
          error: null,
          capabilities,
        });
      } catch (err) {
        if (cancelled) return;
        setValue({
          state: API_STATE.UNAVAILABLE,
          demo: true,
          client,
          error: err instanceof Error ? err.message : String(err),
          capabilities: null,
        });
      }
    }

    probe();
    return () => {
      cancelled = true;
    };
  }, [client]);

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

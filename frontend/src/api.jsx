/**
 * Typed local API client and connection state for the Martenweave workbench.
 *
 * The client talks to the versioned `/api/v1` namespace exposed by
 * `martenweave serve`. When the API is unreachable, incompatible, or missing an
 * index, components fall back to the static demo fixtures in `data.js` and
 * surface the connection state visibly.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { gaps as demoGaps, lineageEdges, lineageNodes, modelObjects, proposals as demoProposals, recentActivity as demoActivity } from "./data.js";

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
 * @typedef {object} RecoveryState
 * @property {string} code
 * @property {"critical"|"warning"|"info"} severity
 * @property {string} label
 * @property {string} message
 * @property {RecoveryAction[]} actions
 * @property {string|null} [more_info]
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
 * @property {() => Promise<{states: RecoveryState[]}>} recovery
 * @property {(params?: {q?: string, type?: string, status?: string, domain?: string, limit?: number, offset?: number}) => Promise<SearchResponse>} search
 * @property {(id: string) => Promise<ObjectDetailResponse>} object
 * @property {(id: string, opts?: {direction?: string, max_depth?: number}) => Promise<TraceResponse>} trace
 * @property {(id: string) => Promise<ImpactResponse>} impact
 * @property {() => Promise<CapabilitiesResponse>} capabilities
 * @property {(limit?: number) => Promise<ActivityResponse>} activity
 * @property {() => Promise<{total_count: number, proposals: ProposalResponse[]}>} proposals
 * @property {(id: string) => Promise<ProposalResponse>} proposal
 * @property {(id: string, body: {status: string, reviewer?: string, reviewer_notes?: string, rejection_reason?: string}) => Promise<any>} reviewProposal
 * @property {(id: string) => Promise<any>} validateProposal
 * @property {(id: string) => Promise<any>} dryRunProposal
 * @property {(id: string) => Promise<any>} applyProposal
 * @property {(id: string) => Promise<ProposalDiffResponse>} proposalDiff
 * @property {() => Promise<{total_count: number, change_requests: ChangeRequestResponse[]}>} changeRequests
 * @property {(data: ChangeRequestCreateData) => Promise<ChangeRequestResponse>} createChangeRequest
 * @property {(body: FindingReviewRequest) => Promise<any>} reviewFinding
 * @property {(body: {assessment: string, finding_id: string, created_by?: string}) => Promise<{finding_id: string, proposal_id: string, proposal_path: string}>} promoteFinding
 * @property {(basePath: string, headPath: string) => Promise<DiffResultResponse>} diffRepositories
 * @property {(file: File, dataset_id?: string) => Promise<ProfileResponse>} importProfile
 * @property {(file: File) => Promise<PreviewResponse>} importPreview
 * @property {(file: File) => Promise<ImportValidateResponse>} importValidate
 * @property {(file: File) => Promise<ImportProposeResponse>} importPropose
 * @property {(format: string, business_review?: boolean) => Promise<ExportModelResponse>} exportModel
 * @property {(reportType: string, format?: string | null) => Promise<{artifact_id: string, name: string, format: string, created_at: string}>} generateReport
 * @property {(limit?: number) => Promise<{total_count: number, artifacts: any[]}>} reports
 * @property {(artifactId: string) => string} reportDownloadUrl
 * @property {() => Promise<WorkspaceSummary>} workspace
 * @property {(path: string) => Promise<WorkspaceValidateResponse>} validateWorkspace
 * @property {(path: string) => Promise<WorkspaceValidateResponse>} openWorkspace
 * @property {(data: {path: string, name: string, template?: string | null}) => Promise<WorkspaceValidateResponse>} createWorkspace
 * @property {() => Promise<any>} findings
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


/**
 * @typedef {object} ProposalOperation
 * @property {string} op
 * @property {string} object_id
 * @property {string} object_type
 * @property {string[]} [target_path]
 * @property {any} [before]
 * @property {any} [after]
 */

/**
 * @typedef {object} ProposalDiffItem
 * @property {string} op
 * @property {string} object_id
 * @property {string|null} target_path
 * @property {any} [before]
 * @property {any} [after]
 * @property {string|null} [status]
 * @property {string|null} [reason]
 */

/**
 * @typedef {object} ProposalDiffResponse
 * @property {string} proposal_id
 * @property {ProposalDiffItem[]} diffs
 */

/**
 * @typedef {object} ProposalRiskAssessment
 * @property {string} risk_level
 * @property {string[]} risk_reasons
 * @property {number} affected_object_count
 * @property {number} max_impact_depth
 * @property {boolean} requires_approval
 */

/**
 * @typedef {object} ProposalValidationResult
 * @property {string} check
 * @property {string} status
 * @property {string} [message]
 */

/**
 * @typedef {object} ProposalResponse
 * @property {string} id
 * @property {string} name
 * @property {string} title
 * @property {string} status
 * @property {string} risk_level
 * @property {string} created_by
 * @property {number} operations_count
 * @property {number} affected_objects_count
 * @property {string} validation_status
 * @property {ProposalOperation[]} operations
 * @property {ProposalRiskAssessment} risk_assessment
 * @property {string[]} affected_objects
 * @property {string[]} source_evidence
 * @property {ProposalValidationResult[]} validation_results
 */

/**
 * @typedef {object} ProposalViewModel
 * @property {string} proposalId
 * @property {string} id
 * @property {string} title
 * @property {string} summary
 * @property {string} status
 * @property {string} risk
 * @property {string} author
 * @property {string} updated
 * @property {number} changes
 * @property {number} impactObjects
 * @property {string} validationStatus
 * @property {string} [linkedGap]
 * @property {string|number|null} [linkedGapId]
 * @property {ProposalOperation[]} [operations]
 * @property {ProposalRiskAssessment} [riskAssessment]
 * @property {string[]} [affected_objects]
 * @property {string[]} [source_evidence]
 * @property {string} [validation_status]
 * @property {ProposalValidationResult[]} [validation_results]
 */

/**
 * @typedef {object} ChangeRequestCreateData
 * @property {string} id
 * @property {string} title
 * @property {string} status
 * @property {string} requester
 * @property {string} reason
 * @property {string} requested_change
 * @property {string} expected_impact
 * @property {string[]} affected_objects
 * @property {string[]} linked_proposals
 * @property {string[]} related_issues
 * @property {string[]} related_decisions
 * @property {string[]} approvers
 * @property {string} priority
 * @property {string[]} source_evidence
 */

/**
 * @typedef {object} ChangeRequestResponse
 * @property {string} id
 * @property {string} title
 * @property {string} status
 */

/**
 * @typedef {object} FindingReviewRequest
 * @property {string} assessment
 * @property {string} finding_id
 * @property {string} disposition
 * @property {string} reviewer
 * @property {string} [note]
 */

/**
 * @typedef {object} ProfileResponse
 * @property {number} row_count
 * @property {number} column_count
 * @property {string[]} columns
 * @property {{success: boolean, messages: string[]}} status
 */

/**
 * @typedef {object} PreviewResponse
 * @property {ProposalResponse} proposal
 * @property {string[]} warnings
 */

/**
 * @typedef {object} ImportValidateResponse
 * @property {boolean} valid
 * @property {string[]} errors
 * @property {string[]} warnings
 * @property {number} workbook_object_count
 * @property {number} existing_object_count
 * @property {number} overlap_count
 */

/**
 * @typedef {object} ImportProposeResponse
 * @property {string} proposal_id
 * @property {string} proposal_path
 * @property {number} operations_count
 * @property {string[]} warnings
 */

/**
 * @typedef {object} WorkspaceSummary
 * @property {string} repository_label
 * @property {string} version
 * @property {string} api_version
 * @property {boolean} indexed
 * @property {number} canonical_files
 * @property {boolean} read_only
 */

/**
 * @typedef {object} WorkspaceValidateResponse
 * @property {boolean} valid
 * @property {string[]} errors
 * @property {string[]} warnings
 * @property {string} repository_label
 * @property {string} version
 * @property {string} api_version
 * @property {boolean} indexed
 * @property {number} canonical_files
 * @property {boolean} read_only
 */

/**
 * @typedef {object} ExportModelResponse
 * @property {string} status
 * @property {string} [message]
 * @property {string} [artifact_id]
 */

export const API_STATE = {
  UNKNOWN: "unknown",
  CONNECTED: "connected",
  UNAVAILABLE: "unavailable",
  STALE_INDEX: "stale_index",
  INCOMPATIBLE: "incompatible",
  INVALID_REPO: "invalid_repo",
  READ_ONLY_REPO: "read_only_repo",
  AI_UNAVAILABLE: "ai_unavailable",
  BLOCKED_IMPORT: "blocked_import",
  PARTIAL_ASSESSMENT: "partial_assessment",
  INVALID_PROPOSAL: "invalid_proposal",
  FAILED_APPLY: "failed_apply",
  MUTATION_AUTH_REQUIRED: "mutation_auth_required",
};

/**
 * Check whether a capability by name is advertised by the local API.
 *
 * @param {CapabilitiesResponse|null} capabilities
 * @param {string} name
 * @returns {boolean}
 */
export function hasCapability(capabilities, name) {
  if (!capabilities) return false;
  const all = [
    ...(capabilities.read || []),
    ...(capabilities.mutations || []),
  ];
  return all.some((capability) => capability.name === name);
}

/**
 * Return a human-readable reason why a mutation is unavailable.
 *
 * @param {ApiContextValue} api
 * @returns {string|null}
 */
export function mutationBlockReason(api) {
  if (api.demo) return "Connect the local API to use this action.";
  if (api.state === API_STATE.STALE_INDEX) return "Build the disposable local index before this action.";
  if (api.capabilities?.read_only) return "This local workspace is read-only.";
  return null;
}

const EXPECTED_API_VERSION = "v1";

export function resolveDefaultApiBaseUrl({ configured, development, origin }) {
  if (configured) return configured;
  if (development) return "http://127.0.0.1:8000";
  return origin || "http://127.0.0.1:8000";
}

export function defaultApiBaseUrl() {
  return resolveDefaultApiBaseUrl({
    configured: import.meta.env?.VITE_API_BASE_URL,
    development: import.meta.env?.DEV,
    origin: globalThis.location?.origin,
  });
}

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
    businessOwner: obj.business_owner_name || obj.business_owner || "—",
    technicalSteward: obj.technical_owner_name || obj.technical_owner || "—",
    lifecycle: obj.status || "Draft",
    lastValidated: "—",
    domain: obj.domain || null,
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

  async function fetchJson(url, options) {
    const response = options !== undefined ? await fetch(url, options) : await fetch(url);
    if (!response.ok) {
      const text = await response.text().catch(() => "Unknown error");
      throw new Error(`${response.status}: ${text}`);
    }
    return response.json();
  }

  async function postJson(url, body) {
    return fetchJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  async function postMultipart(url, file, extra) {
    const formData = new FormData();
    formData.append("file", file);
    if (extra) {
      Object.entries(extra).forEach(([key, value]) => {
        if (value !== undefined && value !== null) formData.append(key, String(value));
      });
    }
    return fetchJson(url, { method: "POST", body: formData });
  }

  return {
    capabilities: () => fetchJson(`${root}/api/v1/capabilities`),
    recovery: () => fetchJson(`${root}/api/v1/recovery`),
    activity: (limit = 50) => fetchJson(`${root}/api/v1/activity?limit=${encodeURIComponent(limit)}`),
    reports: (limit = 100) => fetchJson(`${root}/api/v1/reports?limit=${encodeURIComponent(limit)}`),
    reportDownloadUrl: (artifactId) => `${root}/api/v1/reports/${artifactId.split("/").map(encodeURIComponent).join("/")}`,
    findings: () => fetchJson(`${root}/api/v1/findings`),
    assessmentManifests: () => fetchJson(`${root}/api/v1/assessment-manifests`),
    compareAssessments: (base, head) => fetchJson(`${root}/api/v1/assessment-comparisons?${new URLSearchParams({ base_manifest: base, head_manifest: head })}`),
    diffRepositories: (basePath, headPath) => fetchJson(`${root}/api/v1/diff?${new URLSearchParams({ base_path: basePath, head_path: headPath })}`),
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
    proposals: () => fetchJson(`${root}/proposals`),
    proposal: (id) => fetchJson(`${root}/proposals/${encodeURIComponent(id)}`),
    reviewProposal: (id, body) => postJson(`${root}/proposals/${encodeURIComponent(id)}/review`, body),
    validateProposal: (id) => postJson(`${root}/proposals/${encodeURIComponent(id)}/validate`, {}),
    dryRunProposal: (id) => postJson(`${root}/proposals/${encodeURIComponent(id)}/dry-run`, {}),
    applyProposal: (id) => postJson(`${root}/proposals/${encodeURIComponent(id)}/apply`, {}),
    proposalDiff: (id) => fetchJson(`${root}/proposals/${encodeURIComponent(id)}/diff`),
    changeRequests: () => fetchJson(`${root}/change-requests`),
    createChangeRequest: (data) => postJson(`${root}/change-requests`, data),
    reviewFinding: (body) => postJson(`${root}/api/v1/findings/review`, body),
    promoteFinding: (body) => postJson(`${root}/api/v1/findings/promote`, body),
    importProfile: (file, dataset_id) => postMultipart(`${root}/api/v1/imports/profile`, file, { dataset_id }),
    importPreview: (file) => postMultipart(`${root}/api/v1/imports/preview`, file),
    importValidate: (file) => postMultipart(`${root}/api/v1/imports/validate`, file),
    importPropose: (file) => postMultipart(`${root}/api/v1/imports/propose`, file),
    exportModel: (format, business_review = false) => postJson(
      `${root}/api/v1/exports?format=${encodeURIComponent(format)}&business_review=${encodeURIComponent(business_review)}`,
      {}
    ),
    generateReport: (reportType, format = null) => postJson(
      `${root}/api/v1/reports/generate`,
      { report_type: reportType, format }
    ),
    workspace: () => fetchJson(`${root}/api/v1/workspace`),
    validateWorkspace: (path) => postJson(`${root}/api/v1/workspace/validate`, { path }),
    openWorkspace: (path) => postJson(`${root}/api/v1/workspace/open`, { path }),
    createWorkspace: (data) => postJson(`${root}/api/v1/workspace/create`, data),
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
 * @property {RecoveryState[]} recoveryStates
 * @property {() => void} refresh
 */

/**
 * @type {React.Context<ApiContextValue>}
 */
export const ApiContext = createContext({
  state: API_STATE.UNKNOWN,
  demo: false,
  client: null,
  error: null,
  capabilities: null,
  recovery: null,
  recoveryStates: [],
  refresh: () => {},
});

/**
 * Provide the API connection state to the workbench.
 *
 * @param {{ children: React.ReactNode, baseUrl?: string }} props
 */
export function ApiProvider({ children, baseUrl = defaultApiBaseUrl() }) {
  const client = useMemo(() => createApiClient(baseUrl), [baseUrl]);
  const [value, setValue] = useState(() => ({
    state: API_STATE.UNKNOWN,
    demo: false,
    client,
    error: null,
    capabilities: null,
    recovery: null,
    recoveryStates: [],
    retry: () => {},
    refresh: () => {},
  }));

  const normalizeRecoveryStates = useCallback((response) => {
    if (response && Array.isArray(response.states)) return response.states;
    return [];
  }, []);

  const pickPrimaryRecoveryAction = useCallback((states, capabilities) => {
    if (capabilities?.recovery?.length) return capabilities.recovery[0];
    if (!states.length) return null;
    const prioritized =
      states.find((s) => s.severity === "critical") ||
      states.find((s) => s.severity === "warning") ||
      states[0];
    return prioritized.actions?.[0] || null;
  }, []);

  const probe = useCallback(async () => {
    try {
      const capabilities = await client.capabilities();
      const degraded =
        capabilities.api_version !== EXPECTED_API_VERSION ||
        !capabilities.indexed ||
        capabilities.read_only;
      let recoveryStates = [];
      if (degraded) {
        try {
          recoveryStates = normalizeRecoveryStates(await client.recovery());
        } catch {
          recoveryStates = [];
        }
      }
      const primaryRecovery = pickPrimaryRecoveryAction(recoveryStates, capabilities);
      if (capabilities.api_version !== EXPECTED_API_VERSION) {
        setValue({
          state: API_STATE.INCOMPATIBLE,
          demo: true,
          client,
          error: `API version ${capabilities.api_version} is not supported`,
          capabilities,
          recovery: primaryRecovery,
          recoveryStates,
          retry: probe,
          refresh: probe,
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
          recovery: primaryRecovery,
          recoveryStates,
          retry: probe,
          refresh: probe,
        });
        return;
      }
      setValue({
        state: API_STATE.CONNECTED,
        demo: false,
        client,
        error: null,
        capabilities,
        recovery: primaryRecovery,
        recoveryStates,
        retry: probe,
        refresh: probe,
      });
    } catch (err) {
      setValue({
        state: API_STATE.UNAVAILABLE,
        demo: true,
        client,
        error: err instanceof Error ? err.message : String(err),
        capabilities: null,
        recovery: null,
        recoveryStates: [],
        retry: probe,
        refresh: probe,
      });
    }
  }, [client, normalizeRecoveryStates, pickPrimaryRecoveryAction]);

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
    if (state === API_STATE.UNKNOWN) {
      // Capabilities probe still in flight: stay in a neutral loading state
      // instead of painting demo fixtures or firing a premature request.
      setResults([]);
      setLoading(true);
      setError(null);
      return;
    }

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
            business_owner: r.business_owner,
            technical_owner: r.technical_owner,
            data_steward: r.data_steward,
            business_owner_name: r.business_owner_name,
            technical_owner_name: r.technical_owner_name,
            data_steward_name: r.data_steward_name,
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
  }, [query, activeTab, selectedTypes.join(","), selectedStatuses.join(","), sort, state, demo, client]);

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
  const { client, demo, state } = useApi();
  const [object, setObject] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!objectId) {
      setObject(null);
      return;
    }

    if (state === API_STATE.UNKNOWN) {
      // Capabilities probe still in flight: stay in a neutral loading state
      // instead of painting demo fixtures or firing a premature request.
      setObject(null);
      setLoading(true);
      setError(null);
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
  }, [objectId, state, demo, client]);

  return { object, loading, error };
}

/**
 * Read real, append-only workspace activity while retaining a clearly demo-only fallback offline.
 *
 * @returns {{ events: ActivityEvent[], loading: boolean, error: string|null, demo: boolean }}
 */
export function useWorkspaceActivity(refreshKey = 0) {
  const { client, demo, state } = useApi();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (state === API_STATE.UNKNOWN) {
      // Capabilities probe still in flight: stay in a neutral loading state
      // instead of painting demo fixtures or firing a premature request.
      setEvents([]);
      setLoading(true);
      setError(null);
      return undefined;
    }
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
  }, [client, demo, state, refreshKey]);

  return { events, loading, error, demo };
}

/** Read typed assessment findings with review state from the active local workspace. */
export function useAssessmentFindings() {
  const { client, demo, state } = useApi();
  const [findings, setFindings] = useState([]);
  const [assessmentId, setAssessmentId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (state === API_STATE.UNKNOWN) {
      // Capabilities probe still in flight: stay in a neutral loading state
      // instead of painting demo fixtures or firing a premature request.
      setFindings([]);
      setAssessmentId(null);
      setLoading(true);
      setError(null);
      return undefined;
    }
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
  }, [client, demo, state]);

  return { findings, assessmentId, loading, error, demo };
}

/**
 * Map a backend proposal status to the workbench UI label.
 *
 * @param {string} status
 * @returns {string}
 */
function proposalStatusLabel(status) {
  switch (status) {
    case "pending_review":
      return "In review";
    case "accepted":
      return "Approved";
    case "rejected":
      return "Changes requested";
    default:
      return status;
  }
}

/**
 * Capitalize the first letter of a value.
 *
 * @param {string} [value]
 * @returns {string}
 */
function capitalize(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

/**
 * Map a backend proposal response to the workbench view model shape.
 *
 * @param {ProposalResponse} data
 * @returns {ProposalViewModel}
 */
function mapProposalToViewModel(data) {
  return {
    proposalId: String(data.id),
    id: String(data.id),
    title: data.title || data.name || "",
    summary: data.title || data.name || "",
    status: proposalStatusLabel(data.status),
    risk: capitalize(data.risk_level),
    author: data.created_by || "Martenweave AI",
    updated: "Live",
    changes: data.operations_count ?? (data.operations ? data.operations.length : 0),
    impactObjects: data.affected_objects_count ?? (data.affected_objects ? data.affected_objects.length : 0),
    validationStatus: capitalize(data.validation_status),
    operations: data.operations,
    riskAssessment: data.risk_assessment,
    affected_objects: data.affected_objects,
    source_evidence: data.source_evidence,
    validation_status: data.validation_status,
    validation_results: data.validation_results,
    appliedAt: data.applied_at || null,
  };
}

/**
 * Find a demo proposal by id, supporting both numeric and string ids.
 *
 * @param {string|number|null} id
 * @returns {import("./data.js").ProposalViewModel|undefined}
 */
function findDemoProposal(id) {
  if (id === null || id === undefined) return undefined;
  return demoProposals.find((item) => String(item.id) === String(id));
}

/**
 * Format a workspace activity timestamp for display.
 *
 * @param {string} timestamp
 * @returns {string}
 */
function formatActivityTime(timestamp) {
  const time = new Date(timestamp);
  return Number.isNaN(time.valueOf()) ? timestamp : time.toLocaleString();
}

/**
 * Format a workspace activity event type for display.
 *
 * @param {{event_type: string}} event
 * @returns {string}
 */
function formatActivityLabel(event) {
  return event.event_type.replaceAll("_", " ");
}

/**
 * Deterministic intent router for the home assistant.
 *
 * Parses a free-form prompt into one of a small set of supported intents and
 * extracts any target term. No generative model is used; the router is
 * fully deterministic and works with AI disabled.
 *
 * @param {string} query
 * @returns {{intent: string, term: string}}
 */
function classifyHomeIntent(query) {
  const q = query.trim().toLowerCase();
  if (!q) return { intent: "unsupported", term: "" };

  if (/\b(recent|latest|changed|activity|history|what changed|updates)\b/.test(q)) {
    return { intent: "recent", term: "" };
  }
  if (/\b(gaps?|missing|high.risk|risk|issues?|findings?)\b/.test(q)) {
    return { intent: "gaps", term: "" };
  }
  if (/\b(proposals?|pending|review|approve|approval)\b/.test(q)) {
    return { intent: "proposals", term: "" };
  }
  if (/\b(impact|affected|what happens|who uses|depend|depends on)\b/.test(q)) {
    const term = q
      .replace(/^.*?\b(impact|affected by|depends on|who uses|what happens if i change)\b\s*(of|by|if i change)?\s*/, "")
      .trim();
    return { intent: "impact", term: term || q };
  }
  if (/\b(trace|lineage|upstream|downstream|where does|comes from|flows to)\b/.test(q)) {
    const term = q
      .replace(/^.*?\b(trace|lineage of|where does)\b\s*/, "")
      .trim()
      .replace(/\b(come from|flow|go|goes)\b.*$/, "")
      .trim();
    return { intent: "trace", term: term || q };
  }
  if (/\b(find|search|show|lookup|where is|object|field|attribute|mapping|endpoint)\b/.test(q)) {
    const term = q.replace(/^.*?\b(find|search|show|lookup|where is)\b\s*/, "").trim();
    return { intent: "search", term: term || q };
  }
  return { intent: "unsupported", term: q };
}

/**
 * Build a result card for a canonical object.
 *
 * @param {Record<string, any>} object
 * @param {"live"|"demo"} source
 * @returns {Record<string, any>}
 */
function makeObjectResultCard(object, source) {
  const isProposal = object.type === "PatchProposal" || object.label === "Proposal";
  return {
    intent: "search",
    title: object.name || object.title || object.id,
    subtitle: object.id,
    id: object.id,
    description: object.description || "",
    meta: `${object.type || object.label} · ${object.status}`,
    route: isProposal ? "proposal" : "object",
    params: isProposal ? { id: object.proposalId || object.id } : { id: object.id },
    evidence: [object.source_file || "Canonical model file"],
    source,
  };
}

/**
 * Resolve a user-provided term to a canonical object id through search.
 *
 * @param {ApiClient|null} client
 * @param {string} term
 * @param {boolean} demo
 * @returns {Promise<string|null>}
 */
async function resolveHomeObjectId(client, term, demo) {
  if (demo || !client) {
    const match = modelObjects.find((item) =>
      `${item.name} ${item.id}`.toLowerCase().includes(term.toLowerCase())
    );
    return match?.id || null;
  }
  const response = await client.search({ q: term, limit: 1 });
  return response.results[0]?.object_id || null;
}

/**
 * Execute a home-assistant search intent.
 *
 * @param {ApiClient|null} client
 * @param {string} term
 * @param {boolean} demo
 * @returns {Promise<Record<string, any>[]>}
 */
async function executeHomeSearch(client, term, demo) {
  if (demo || !client) {
    const q = term.toLowerCase();
    const matches = modelObjects.filter((item) =>
      `${item.name} ${item.id} ${item.description} ${item.type}`.toLowerCase().includes(q)
    );
    return matches.map((item) => makeObjectResultCard(item, "demo"));
  }
  const response = await client.search({ q: term, limit: 10 });
  return response.results.map((r) =>
    makeObjectResultCard(
      {
        id: r.object_id,
        name: r.name || r.title || r.object_id,
        description: r.description || "",
        type: r.object_type,
        label: typeToLabel(r.object_type),
        status: r.status,
        source_file: r.source_file,
        proposalId: r.object_type === "PatchProposal" ? r.object_id : undefined,
      },
      "live"
    )
  );
}

/**
 * Execute a home-assistant gaps intent.
 *
 * @param {ApiClient|null} client
 * @param {boolean} demo
 * @returns {Promise<Record<string, any>[]>}
 */
async function executeHomeGaps(client, demo) {
  if (demo || !client) {
    return demoGaps.map((gap) => ({
      intent: "gaps",
      title: gap.title,
      subtitle: `GAP-${gap.id}`,
      id: `GAP-${gap.id}`,
      description: gap.note,
      meta: `${gap.severity} severity · ${gap.status}`,
      route: "gaps",
      params: { gap: gap.id },
      evidence: gap.evidence || [],
      source: "demo",
    }));
  }
  const response = await client.findings();
  return (response.findings || []).map((finding) => ({
    intent: "gaps",
    title: finding.finding?.message || finding.finding?.id || "Finding",
    subtitle: finding.finding?.id || "",
    id: finding.finding?.id || "",
    description: finding.finding?.category?.replaceAll("_", " ") || "",
    meta: `${finding.finding?.severity || "unknown"} severity · ${finding.finding?.lifecycle_state || "open"}`,
    route: "gaps",
    params: {},
    evidence: [
      finding.provenance?.assessment_run_id || "Local assessment run",
      finding.provenance?.source_kind?.replaceAll("_", " ") || "",
    ].filter(Boolean),
    source: "live",
  }));
}

/**
 * Execute a home-assistant recent-activity intent.
 *
 * @param {ApiClient|null} client
 * @param {boolean} demo
 * @returns {Promise<Record<string, any>[]>}
 */
async function executeHomeRecent(client, demo) {
  if (demo || !client) {
    return demoActivity.map(([action, subject, time], index) => ({
      intent: "recent",
      title: action,
      subtitle: subject,
      id: `demo-activity-${index}`,
      description: `Workspace event for ${subject}`,
      meta: time,
      route: "changelog",
      params: {},
      evidence: ["Demo workspace activity"],
      source: "demo",
    }));
  }
  const response = await client.activity(10);
  return (response.events || []).map((event) => ({
    intent: "recent",
    title: formatActivityLabel(event),
    subtitle: event.changed_object_ids?.join(", ") || event.proposal_id || "Workspace event",
    id: event.event_id,
    description: `Event type: ${event.event_type}`,
    meta: formatActivityTime(event.timestamp),
    route: event.proposal_id
      ? "proposals"
      : event.changed_object_ids?.[0]
        ? "object"
        : "changelog",
    params: event.proposal_id
      ? {}
      : event.changed_object_ids?.[0]
        ? { id: event.changed_object_ids[0] }
        : {},
    evidence: [
      event.source_state === "generated"
        ? "Generated local artifact"
        : "Canonical model change",
    ],
    source: "live",
  }));
}

/**
 * Execute a home-assistant proposals intent.
 *
 * @param {ApiClient|null} client
 * @param {boolean} demo
 * @returns {Promise<Record<string, any>[]>}
 */
async function executeHomeProposals(client, demo) {
  if (demo || !client) {
    return demoProposals.map((proposal) => ({
      intent: "proposals",
      title: proposal.title,
      subtitle: `Proposal #${proposal.id}`,
      id: `PROPOSAL-${proposal.id}`,
      description: proposal.summary,
      meta: `${proposal.status} · ${proposal.risk} risk`,
      route: "proposal",
      params: { id: proposal.id },
      evidence: [`${proposal.changes} changes · ${proposal.impactObjects} affected objects`],
      source: "demo",
    }));
  }
  const response = await client.proposals();
  const list = Array.isArray(response) ? response : response.proposals || [];
  return list.map((p) => {
    const view = mapProposalToViewModel(p);
    return {
      intent: "proposals",
      title: view.title,
      subtitle: `Proposal #${view.id}`,
      id: `PROPOSAL-${view.id}`,
      description: view.summary,
      meta: `${view.status} · ${view.risk} risk`,
      route: "proposal",
      params: { id: view.id },
      evidence: [
        `${view.changes} changes · ${view.impactObjects} affected objects`,
        view.validationStatus,
      ].filter(Boolean),
      source: "live",
    };
  });
}

/**
 * Execute a home-assistant trace intent.
 *
 * @param {ApiClient|null} client
 * @param {string} term
 * @param {boolean} demo
 * @returns {Promise<Record<string, any>[]>}
 */
async function executeHomeTrace(client, term, demo) {
  const id = await resolveHomeObjectId(client, term, demo);
  if (!id) return [];
  if (demo || !client) {
    return [{
      intent: "trace",
      title: `Trace: ${term}`,
      subtitle: id,
      id,
      description: "Lineage traversal from the selected object across source, mapping, and target layers.",
      meta: "Lineage snapshot",
      route: "lineage",
      params: { id },
      evidence: ["Demo lineage data"],
      source: "demo",
    }];
  }
  const trace = await client.trace(id, { direction: "both", max_depth: 3 });
  return [{
    intent: "trace",
    title: `Trace: ${trace.root_object_name || id}`,
    subtitle: trace.root_object_id,
    id: trace.root_object_id,
    description: `${trace.nodes.length} related objects across upstream and downstream lineage.`,
    meta: `${trace.nodes.length} nodes · ${trace.edges.length} edges`,
    route: "lineage",
    params: { id: trace.root_object_id },
    evidence: trace.edges
      .slice(0, 3)
      .map((e) => `${e.from_object_id} → ${e.to_object_id} (${e.relationship_type})`),
    source: "live",
  }];
}

/**
 * Execute a home-assistant impact intent.
 *
 * @param {ApiClient|null} client
 * @param {string} term
 * @param {boolean} demo
 * @returns {Promise<Record<string, any>[]>}
 */
async function executeHomeImpact(client, term, demo) {
  const id = await resolveHomeObjectId(client, term, demo);
  if (!id) return [];
  if (demo || !client) {
    return [{
      intent: "impact",
      title: `Impact: ${term}`,
      subtitle: id,
      id,
      description: "Downstream impact analysis from the selected canonical object.",
      meta: "Impact snapshot",
      route: "lineage",
      params: { id },
      evidence: ["Demo impact data"],
      source: "demo",
    }];
  }
  const impact = await client.impact(id);
  return [{
    intent: "impact",
    title: `Impact: ${impact.root_object_name || id}`,
    subtitle: impact.object_id,
    id: impact.object_id,
    description: `${impact.total_affected} total affected objects across upstream and downstream dependencies.`,
    meta: `${impact.total_affected} affected · downstream ${impact.downstream?.length || 0}`,
    route: "lineage",
    params: { id: impact.object_id },
    evidence: (impact.downstream || [])
      .slice(0, 3)
      .map((item) => `${item.object_id} · ${item.relationship_type}`),
    source: "live",
  }];
}

/**
 * Turn a natural-language prompt into structured, evidence-backed actions.
 *
 * The assistant is fully deterministic: it classifies the prompt into a small
 * set of intents, fetches data from the local API when connected, and falls
 * back to clearly labelled demo data when the API is unavailable. An optional
 * AI provider may later summarise the retrieved cards, but every citation and
 * link works without AI.
 *
 * @returns {{
 *   query: string,
 *   intent: string | null,
 *   results: Record<string, any>[],
 *   loading: boolean,
 *   error: string | null,
 *   run: (query: string) => Promise<void>,
 *   reset: () => void
 * }}
 */
export function useHomeAssistant() {
  const { client, demo, state: apiState } = useApi();
  const [state, setState] = useState({
    query: "",
    intent: null,
    results: [],
    loading: false,
    error: null,
  });
  const pendingQueryRef = useRef(null);

  const run = useCallback(
    async (query) => {
      const trimmed = query.trim();
      if (!trimmed) {
        pendingQueryRef.current = null;
        setState({ query: "", intent: null, results: [], loading: false, error: null });
        return;
      }
      setState((current) => ({
        ...current,
        query: trimmed,
        loading: true,
        error: null,
        results: [],
      }));
      try {
        const { intent, term } = classifyHomeIntent(trimmed);
        if (apiState === API_STATE.UNKNOWN && intent !== "unsupported") {
          // Capabilities probe still in flight: hold the query in a neutral
          // loading state and run it once the probe settles, instead of
          // painting demo fixtures or firing a premature request.
          pendingQueryRef.current = trimmed;
          setState({ query: trimmed, intent: null, results: [], loading: true, error: null });
          return;
        }
        let results = [];
        switch (intent) {
          case "search":
            results = await executeHomeSearch(client, term, demo);
            break;
          case "gaps":
            results = await executeHomeGaps(client, demo);
            break;
          case "recent":
            results = await executeHomeRecent(client, demo);
            break;
          case "proposals":
            results = await executeHomeProposals(client, demo);
            break;
          case "trace":
            results = await executeHomeTrace(client, term, demo);
            break;
          case "impact":
            results = await executeHomeImpact(client, term, demo);
            break;
          default:
            results = [];
        }
        setState({ query: trimmed, intent, results, loading: false, error: null });
      } catch (err) {
        setState({
          query: trimmed,
          intent: "unsupported",
          results: [],
          loading: false,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    },
    [client, demo, apiState]
  );

  useEffect(() => {
    if (apiState === API_STATE.UNKNOWN) return;
    const pending = pendingQueryRef.current;
    if (!pending) return;
    pendingQueryRef.current = null;
    run(pending);
  }, [apiState, run]);

  const reset = useCallback(() => {
    pendingQueryRef.current = null;
    setState({ query: "", intent: null, results: [], loading: false, error: null });
  }, []);

  return { ...state, run, reset };
}

/**
 * Compare two repository model directories.
 *
 * @param {string} basePath
 * @param {string} headPath
 * @returns {{ result: DiffResultResponse|null, loading: boolean, error: string|null }}
 */
export function useRepositoryDiff(basePath, headPath) {
  const { client, demo } = useApi();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!basePath || !headPath) {
      setResult(null);
      setLoading(false);
      setError(null);
      return undefined;
    }
    if (demo || !client) {
      setResult(null);
      setLoading(false);
      setError("Connect the local API to compare repository states.");
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    client.diffRepositories(basePath, headPath)
      .then((data) => {
        if (!cancelled) {
          setResult(data);
          setError(null);
        }
      })
      .catch((reason) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : String(reason));
          setResult(null);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [basePath, headPath, demo, client]);

  return { result, loading, error };
}

/**
 * List proposals through the live API, falling back to demo fixtures.
 *
 * @returns {{ proposals: ProposalViewModel[], loading: boolean, error: string|null, demo: boolean }}
 */
export function useProposals(refreshKey = 0) {
  const { client, demo, state } = useApi();
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (state === API_STATE.UNKNOWN) {
      // Capabilities probe still in flight: stay in a neutral loading state
      // instead of painting demo fixtures or firing a premature request.
      setProposals([]);
      setLoading(true);
      setError(null);
      return undefined;
    }
    if (demo || !client) {
      setProposals(demoProposals);
      setLoading(false);
      setError(null);
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    client.proposals()
      .then((response) => {
        if (cancelled) return;
        const list = Array.isArray(response) ? response : response.proposals || [];
        setProposals(list.map(mapProposalToViewModel));
        setError(null);
      })
      .catch((reason) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : String(reason));
          setProposals([]);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [client, demo, state, refreshKey]);

  return { proposals, loading, error, demo };
}

/**
 * Fetch a single proposal through the live API, falling back to demo fixtures.
 *
 * @param {string|number|null} proposalId
 * @returns {{ proposal: ProposalViewModel|null, loading: boolean, error: string|null, demo: boolean }}
 */
export function useProposalDetail(proposalId, refreshKey = 0) {
  const { client, demo, state } = useApi();
  const [proposal, setProposal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!proposalId) {
      setProposal(null);
      setLoading(false);
      setError(null);
      return undefined;
    }

    if (state === API_STATE.UNKNOWN) {
      // Capabilities probe still in flight: stay in a neutral loading state
      // instead of painting demo fixtures or firing a premature request.
      setProposal(null);
      setLoading(true);
      setError(null);
      return undefined;
    }

    if (demo || !client) {
      const found = findDemoProposal(proposalId);
      setProposal(found || null);
      setLoading(false);
      setError(null);
      return undefined;
    }

    let cancelled = false;
    setLoading(true);
    client.proposal(String(proposalId))
      .then((response) => {
        if (cancelled) return;
        setProposal(mapProposalToViewModel(response));
        setError(null);
      })
      .catch((reason) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : String(reason));
          setProposal(null);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [proposalId, state, demo, client, refreshKey]);

  return { proposal, loading, error, demo };
}

/**
 * Mutation hook for reviewing a proposal.
 *
 * @returns {{ reviewProposal: (id: string, body: {status: string, reviewer?: string, reviewer_notes?: string, rejection_reason?: string}) => Promise<any>, loading: boolean, error: string|null }}
 */
export function useProposalReview() {
  const { client } = useApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const reviewProposal = useCallback(async (id, body) => {
    if (!client) throw new Error("API client is not available");
    setLoading(true);
    setError(null);
    try {
      const result = await client.reviewProposal(id, body);
      return result;
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : String(reason);
      setError(message);
      throw reason;
    } finally {
      setLoading(false);
    }
  }, [client]);

  return { reviewProposal, loading, error };
}

/**
 * @param {(client: ApiClient, id: string) => Promise<any>} runFn
 * @returns {{ run: (id: string) => Promise<any>, loading: boolean, error: string|null, result: any }}
 */
function useProposalMutation(runFn) {
  const { client } = useApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const run = useCallback(async (id) => {
    if (!client) throw new Error("API client is not available");
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await runFn(client, id);
      setResult(data);
      return data;
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : String(reason);
      setError(message);
      throw reason;
    } finally {
      setLoading(false);
    }
  }, [client, runFn]);

  return { run, loading, error, result };
}

/**
 * Mutation hook for validating a proposal.
 *
 * @returns {{ run: (id: string) => Promise<any>, loading: boolean, error: string|null, result: any }}
 */
export function useProposalValidate() {
  return useProposalMutation((client, id) => client.validateProposal(id));
}

/**
 * Mutation hook for dry-running a proposal.
 *
 * @returns {{ run: (id: string) => Promise<any>, loading: boolean, error: string|null, result: any }}
 */
export function useProposalDryRun() {
  return useProposalMutation((client, id) => client.dryRunProposal(id));
}

/**
 * Mutation hook for applying a proposal.
 *
 * @returns {{ run: (id: string) => Promise<any>, loading: boolean, error: string|null, result: any }}
 */
export function useProposalApply() {
  return useProposalMutation((client, id) => client.applyProposal(id));
}

/**
 * Mutation hook for fetching a proposal diff preview.
 *
 * @returns {{ run: (id: string) => Promise<ProposalDiffResponse>, loading: boolean, error: string|null, result: ProposalDiffResponse|null }}
 */
export function useProposalDiff() {
  return useProposalMutation((client, id) => client.proposalDiff(id));
}

/**
 * Mutation hook for reviewing an assessment finding.
 *
 * @returns {{ reviewFinding: (body: FindingReviewRequest) => Promise<any>, loading: boolean, error: string|null }}
 */
export function useFindingReview() {
  const { client } = useApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const reviewFinding = useCallback(async (body) => {
    if (!client) throw new Error("API client is not available");
    setLoading(true);
    setError(null);
    try {
      const result = await client.reviewFinding(body);
      return result;
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : String(reason);
      setError(message);
      throw reason;
    } finally {
      setLoading(false);
    }
  }, [client]);

  return { reviewFinding, loading, error };
}

/**
 * Mutation hook for promoting a confirmed finding to a PatchProposal.
 *
 * @returns {{ promoteFinding: (body: {assessment: string, finding_id: string, created_by?: string}) => Promise<any>, loading: boolean, error: string|null }}
 */
export function useFindingPromote() {
  const { client } = useApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const promoteFinding = useCallback(async (body) => {
    if (!client) throw new Error("API client is not available");
    setLoading(true);
    setError(null);
    try {
      const result = await client.promoteFinding(body);
      return result;
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : String(reason);
      setError(message);
      throw reason;
    } finally {
      setLoading(false);
    }
  }, [client]);

  return { promoteFinding, loading, error };
}

/**
 * @param {(client: ApiClient, file: File, extra?: any) => Promise<any>} runFn
 * @returns {{ run: (file: File, extra?: any) => Promise<any>, loading: boolean, error: string|null, result: any }}
 */
function useImportMutation(runFn) {
  const { client } = useApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const run = useCallback(async (file, extra) => {
    if (!client) throw new Error("API client is not available");
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await runFn(client, file, extra);
      setResult(data);
      return data;
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : String(reason);
      setError(message);
      throw reason;
    } finally {
      setLoading(false);
    }
  }, [client, runFn]);

  return { run, loading, error, result };
}

/**
 * Mutation hook for profiling a dataset file.
 *
 * @returns {{ run: (file: File, dataset_id?: string) => Promise<ProfileResponse>, loading: boolean, error: string|null, result: ProfileResponse|null }}
 */
export function useImportProfile() {
  return useImportMutation((client, file, dataset_id) => client.importProfile(file, dataset_id));
}

/**
 * Mutation hook for previewing a canonical/import file.
 *
 * @returns {{ run: (file: File) => Promise<PreviewResponse>, loading: boolean, error: string|null, result: PreviewResponse|null }}
 */
export function useImportPreview() {
  return useImportMutation((client, file) => client.importPreview(file));
}

/**
 * Mutation hook for validating a returned review workbook.
 *
 * @returns {{ run: (file: File) => Promise<ImportValidateResponse>, loading: boolean, error: string|null, result: ImportValidateResponse|null }}
 */
export function useImportValidate() {
  return useImportMutation((client, file) => client.importValidate(file));
}

/**
 * Mutation hook for turning a validated review workbook into a PatchProposal.
 *
 * @returns {{ run: (file: File) => Promise<ImportProposeResponse>, loading: boolean, error: string|null, result: ImportProposeResponse|null }}
 */
export function useImportPropose() {
  return useImportMutation((client, file) => client.importPropose(file));
}

/**
 * Mutation hook for generating a local report.
 *
 * @returns {{ run: (reportType: string, format?: string | null) => Promise<any>, loading: boolean, error: string|null, result: any }}
 */
export function useReportGenerate() {
  const { client } = useApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const run = useCallback(async (reportType, format = null) => {
    if (!client) throw new Error("API client is not available");
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await client.generateReport(reportType, format);
      setResult(data);
      return data;
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : String(reason);
      setError(message);
      throw reason;
    } finally {
      setLoading(false);
    }
  }, [client]);

  return { run, loading, error, result };
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
  const { client, demo, state } = useApi();
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

    if (state === API_STATE.UNKNOWN) {
      // Capabilities probe still in flight: stay in a neutral loading state
      // instead of painting demo fixtures or firing a premature request.
      setNodes([]);
      setEdges([]);
      setUpstream([]);
      setDownstream([]);
      setImpact(null);
      setLoading(true);
      setError(null);
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
  }, [objectId, direction, maxDepth, state, demo, client]);

  return { nodes, edges, upstream, downstream, impact, loading, error };
}

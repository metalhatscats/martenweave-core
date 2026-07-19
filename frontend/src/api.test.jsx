import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useEffect, useState } from "react";

import {
  API_STATE,
  ApiProvider,
  apiObjectToViewModel,
  createApiClient,
  objectTypeToTone,
  resolveDefaultApiBaseUrl,
  traceResponseToFlowEdges,
  traceResponseToFlowNodes,
  useApi,
  useHomeAssistant,
  useLineage,
  useObjectDetail,
  useObjectSearch,
} from "./api.jsx";
import { LineageScreen } from "./App.jsx";
import { modelObjects } from "./data.js";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock;

function mockFetch(response, status = 200) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(response),
    text: () => Promise.resolve(JSON.stringify(response)),
  });
}

function mockFetchSequence(...responses) {
  globalThis.fetch = vi.fn((url) => {
    const index = globalThis.fetch.mock.calls.length - 1;
    const response = responses[Math.min(index, responses.length - 1)];
    const body = typeof response === "function" ? response(url) : response;
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(body),
      text: () => Promise.resolve(JSON.stringify(body)),
    });
  });
}

function mockFetchRoutes(routeMap) {
  const capabilities = {
    api_version: "v1",
    version: "0.6.0",
    indexed: true,
    canonical_files: 3,
  };
  globalThis.fetch = vi.fn((url) => {
    if (url.includes("/api/v1/capabilities")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(capabilities),
        text: () => Promise.resolve(JSON.stringify(capabilities)),
      });
    }
    for (const [match, response] of Object.entries(routeMap)) {
      if (url.includes(match)) {
        const body = typeof response === "function" ? response(url) : response;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(body),
          text: () => Promise.resolve(JSON.stringify(body)),
        });
      }
    }
    return Promise.resolve({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ detail: "Not found" }),
      text: () => Promise.resolve("Not found"),
    });
  });
}

function TestWrapper({ children, baseUrl = "http://localhost:8000" }) {
  return <ApiProvider baseUrl={baseUrl}>{children}</ApiProvider>;
}

function Probe() {
  const { state, demo, capabilities, recovery } = useApi();
  return (
    <div>
      <span data-testid="state">{state}</span>
      <span data-testid="demo">{demo ? "demo" : "live"}</span>
      <span data-testid="version">{capabilities?.version || "none"}</span>
      <span data-testid="recovery">{recovery?.code || "none"}</span>
    </div>
  );
}

describe("createApiClient", () => {
  it("uses the current origin for packaged Workbench builds", () => {
    expect(
      resolveDefaultApiBaseUrl({
        configured: undefined,
        development: false,
        origin: "http://127.0.0.1:8765",
      }),
    ).toBe("http://127.0.0.1:8765");
  });

  it("fetches capabilities", async () => {
    mockFetch({ api_version: "v1", version: "0.6.0", indexed: true });
    const client = createApiClient("http://localhost:8000");
    const caps = await client.capabilities();
    expect(caps.version).toBe("0.6.0");
    expect(globalThis.fetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/capabilities");
  });

  it("fetches append-only workspace activity", async () => {
    mockFetch({ total_count: 0, events: [] });
    const client = createApiClient("http://localhost:8000");
    const result = await client.activity();
    expect(result.events).toEqual([]);
    expect(globalThis.fetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/activity?limit=50");
  });

  it("lists generated reports and builds an encoded local download URL", async () => {
    mockFetch({ total_count: 1, artifacts: [{ artifact_id: "assessment/review pack.md" }] });
    const client = createApiClient("http://localhost:8000");
    const result = await client.reports();
    expect(result.total_count).toBe(1);
    expect(globalThis.fetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/reports?limit=100");
    expect(client.reportDownloadUrl("assessment/review pack.md")).toBe(
      "http://localhost:8000/api/v1/reports/assessment/review%20pack.md",
    );
  });

  it("fetches typed assessment findings", async () => {
    mockFetch({ total_count: 0, findings: [] });
    const client = createApiClient("http://localhost:8000");
    await expect(client.findings()).resolves.toEqual({ total_count: 0, findings: [] });
    expect(globalThis.fetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/findings");
  });

  it("searches with query parameters", async () => {
    mockFetch({ total_count: 1, results: [{ object_id: "DOMAIN-TEST", object_type: "MasterDataDomain", status: "draft", name: "Test", title: null, domain: null, description: null, source_file: "DOMAIN-TEST.md", score: 1, matched_fields: ["name"] }] });
    const client = createApiClient("http://localhost:8000");
    const result = await client.search({ q: "test", type: "MasterDataDomain" });
    expect(result.total_count).toBe(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/search?q=test&type=MasterDataDomain")
    );
  });

  it("fetches object detail", async () => {
    mockFetch({ object: { id: "DOMAIN-TEST", type: "MasterDataDomain", name: "Test" }, relationships: [] });
    const client = createApiClient("http://localhost:8000");
    const result = await client.object("DOMAIN-TEST");
    expect(result.object.id).toBe("DOMAIN-TEST");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/objects/DOMAIN-TEST"
    );
  });

  it("fetches trace with direction and depth", async () => {
    mockFetch({
      root_object_id: "DOMAIN-TEST",
      root_object_type: "MasterDataDomain",
      root_object_name: "Test",
      nodes: [],
      edges: [],
    });
    const client = createApiClient("http://localhost:8000");
    const result = await client.trace("DOMAIN-TEST", { direction: "upstream", max_depth: 2 });
    expect(result.root_object_id).toBe("DOMAIN-TEST");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/trace/DOMAIN-TEST?direction=upstream&max_depth=2")
    );
  });

  it("fetches impact for an object", async () => {
    mockFetch({
      object_id: "DOMAIN-TEST",
      root_object_type: "MasterDataDomain",
      root_object_name: "Test",
      upstream: [],
      downstream: [],
      total_affected: 0,
    });
    const client = createApiClient("http://localhost:8000");
    const result = await client.impact("DOMAIN-TEST");
    expect(result.object_id).toBe("DOMAIN-TEST");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/impact/DOMAIN-TEST"
    );
  });
});

describe("lineage helpers", () => {
  it("maps canonical types to lineage tones", () => {
    expect(objectTypeToTone("MasterDataDomain")).toBe("canonical");
    expect(objectTypeToTone("BusinessEntity")).toBe("canonical");
    expect(objectTypeToTone("FieldEndpoint")).toBe("source");
    expect(objectTypeToTone("Attribute")).toBe("target");
    expect(objectTypeToTone("Mapping")).toBe("mapping");
    expect(objectTypeToTone("PatchProposal")).toBe("proposal");
    expect(objectTypeToTone("Decision")).toBe("decision");
    expect(objectTypeToTone("Issue")).toBe("gap");
    expect(objectTypeToTone("Unknown")).toBe("target");
  });

  it("builds ReactFlow nodes from a trace response", () => {
    const trace = {
      root_object_id: "DOMAIN-ROOT",
      root_object_type: "MasterDataDomain",
      root_object_name: "Root",
      nodes: [
        { object_id: "FEP-UP", object_type: "FieldEndpoint", object_name: "Upstream", source_file: "x.md", depth: 1 },
        { object_id: "ATTR-DOWN", object_type: "Attribute", object_name: "Downstream", source_file: "y.md", depth: 1 },
      ],
      edges: [
        { from_object_id: "FEP-UP", to_object_id: "DOMAIN-ROOT", relationship_type: "feeds", direction: "upstream" },
        { from_object_id: "DOMAIN-ROOT", to_object_id: "ATTR-DOWN", relationship_type: "defines", direction: "downstream" },
      ],
    };
    const nodes = traceResponseToFlowNodes(trace);
    expect(nodes.find((n) => n.id === "DOMAIN-ROOT")).toBeTruthy();
    expect(nodes.find((n) => n.id === "FEP-UP").position.x).toBeLessThan(0);
    expect(nodes.find((n) => n.id === "ATTR-DOWN").position.x).toBeGreaterThan(0);
  });

  it("builds ReactFlow edges from a trace response", () => {
    const trace = {
      root_object_id: "DOMAIN-ROOT",
      root_object_type: "MasterDataDomain",
      root_object_name: "Root",
      nodes: [],
      edges: [
        { from_object_id: "A", to_object_id: "B", relationship_type: "maps", direction: "downstream" },
      ],
    };
    const edges = traceResponseToFlowEdges(trace);
    expect(edges).toHaveLength(1);
    expect(edges[0].source).toBe("A");
    expect(edges[0].target).toBe("B");
    expect(edges[0].animated).toBe(true);
  });
});

describe("apiObjectToViewModel", () => {
  it("maps a canonical domain to the workbench view shape", () => {
    const view = apiObjectToViewModel({
      id: "DOMAIN-CUSTOMER-BP",
      type: "MasterDataDomain",
      status: "active",
      name: "Business Partner",
      description: "Canonical domain for business partners.",
      business_owner: "Customer Data Office",
      technical_owner: "Priya Nair",
    });
    expect(view.id).toBe("DOMAIN-CUSTOMER-BP");
    expect(view.label).toBe("Domain");
    expect(view.owners).toBe(2);
    expect(view.businessOwner).toBe("Customer Data Office");
  });
});

describe("ApiProvider", () => {
  it("marks the connection as live when capabilities are compatible", async () => {
    mockFetch({ api_version: "v1", version: "0.6.0", indexed: true, canonical_files: 24 });
    render(<Probe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("state").textContent).toBe(API_STATE.CONNECTED));
    expect(screen.getByTestId("demo").textContent).toBe("live");
    expect(screen.getByTestId("version").textContent).toBe("0.6.0");
  });

  it("falls back to demo mode when the API is unreachable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));
    render(<Probe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("state").textContent).toBe(API_STATE.UNAVAILABLE));
    expect(screen.getByTestId("demo").textContent).toBe("demo");
  });

  it("falls back to demo mode when the index is stale", async () => {
    mockFetch({ api_version: "v1", version: "0.6.0", indexed: false, canonical_files: 0, recovery: [{ code: "BUILD_INDEX", label: "Build the disposable local index", command: "martenweave build-index --repo .", requires_confirmation: false }] });
    render(<Probe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("state").textContent).toBe(API_STATE.STALE_INDEX));
    expect(screen.getByTestId("demo").textContent).toBe("demo");
    expect(screen.getByTestId("recovery").textContent).toBe("BUILD_INDEX");
  });

  it("falls back to demo mode for an incompatible contract version", async () => {
    mockFetch({ api_version: "v0", version: "0.1.0", indexed: true });
    render(<Probe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("state").textContent).toBe(API_STATE.INCOMPATIBLE));
    expect(screen.getByTestId("demo").textContent).toBe("demo");
  });
});

function SearchProbe() {
  const [mounted, setMounted] = useState(false);
  const { results, loading, error } = useObjectSearch("customer", "All", [], [], "Relevance");
  useEffect(() => setMounted(true), []);
  return (
    <div>
      <span data-testid="loading">{loading ? "loading" : "ready"}</span>
      <span data-testid="error">{error || "none"}</span>
      <span data-testid="count">{results.length}</span>
      {mounted && results.map((r) => (
        <span key={r.id} data-testid="result">{r.name}</span>
      ))}
      {mounted && results.map((r) => (
        <span key={`${r.id}-owner`} data-testid="owner">{r.businessOwner}</span>
      ))}
    </div>
  );
}

describe("useObjectSearch", () => {
  it("returns live API results when connected", async () => {
    mockFetchSequence(
      { api_version: "v1", version: "0.6.0", indexed: true, canonical_files: 1 },
      { total_count: 1, results: [{ object_id: "DOMAIN-LIVE", object_type: "MasterDataDomain", status: "active", name: "Live Domain", title: null, domain: null, description: "Live", source_file: "x.md", score: 1, matched_fields: [] }] }
    );
    render(<SearchProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByTestId("result").textContent).toBe("Live Domain");
  });

  it("maps live search ownership fields into the view model", async () => {
    mockFetchSequence(
      { api_version: "v1", version: "0.6.0", indexed: true, canonical_files: 1 },
      { total_count: 1, results: [{ object_id: "ATTR-LIVE", object_type: "Attribute", status: "active", name: "Live Attribute", title: null, domain: null, description: "Live", source_file: "x.md", score: 1, matched_fields: [], business_owner: "PERSON-BUSINESS-OWNER", technical_owner: null, data_steward: "PERSON-DATA-STEWARD" }] }
    );
    render(<SearchProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByTestId("owner").textContent).toBe("PERSON-BUSINESS-OWNER");
  });

  it("falls back to demo data when the API is unavailable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));
    render(<SearchProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    expect(screen.queryAllByTestId("result").length).toBeGreaterThan(0);
  });
});

function ObjectProbe({ id }) {
  const { object, loading, error } = useObjectDetail(id);
  return (
    <div>
      <span data-testid="loading">{loading ? "loading" : "ready"}</span>
      <span data-testid="error">{error || "none"}</span>
      <span data-testid="name">{object?.name || "none"}</span>
    </div>
  );
}

describe("useObjectDetail", () => {
  it("returns a live object when connected", async () => {
    mockFetchSequence(
      { api_version: "v1", version: "0.6.0", indexed: true, canonical_files: 1 },
      { object: { id: "DOMAIN-LIVE", type: "MasterDataDomain", name: "Live Object" }, relationships: [] }
    );
    render(<ObjectProbe id="DOMAIN-LIVE" />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    await waitFor(() => expect(screen.getByTestId("name").textContent).toBe("Live Object"));
  });

  it("falls back to demo data when the API is unavailable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));
    render(<ObjectProbe id="DOMAIN-CUSTOMER-BP" />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    expect(screen.getByTestId("name").textContent).toBe("Business Partner");
  });
});

function LineageProbe({ objectId }) {
  const { nodes, edges, upstream, downstream, impact, loading, error } = useLineage(
    objectId,
    "both",
    5
  );
  return (
    <div>
      <span data-testid="loading">{loading ? "loading" : "ready"}</span>
      <span data-testid="error">{error || "none"}</span>
      <span data-testid="nodes">{nodes.length}</span>
      <span data-testid="edges">{edges.length}</span>
      <span data-testid="upstream">{upstream.length}</span>
      <span data-testid="downstream">{downstream.length}</span>
      <span data-testid="impact">{impact ? impact.total_affected : "none"}</span>
    </div>
  );
}

describe("useLineage", () => {
  it("returns live trace and impact data when connected", async () => {
    mockFetchRoutes({
      "/trace/DOMAIN-LINEAGE": {
        root_object_id: "DOMAIN-LINEAGE",
        root_object_type: "MasterDataDomain",
        root_object_name: "Lineage Root",
        nodes: [
          { object_id: "FEP-UP", object_type: "FieldEndpoint", object_name: "Upstream", source_file: "x.md", depth: 1 },
          { object_id: "ATTR-DOWN", object_type: "Attribute", object_name: "Downstream", source_file: "y.md", depth: 1 },
        ],
        edges: [
          { from_object_id: "FEP-UP", to_object_id: "DOMAIN-LINEAGE", relationship_type: "feeds", direction: "upstream" },
          { from_object_id: "DOMAIN-LINEAGE", to_object_id: "ATTR-DOWN", relationship_type: "defines", direction: "downstream" },
        ],
      },
      "/impact/DOMAIN-LINEAGE": {
        object_id: "DOMAIN-LINEAGE",
        root_object_type: "MasterDataDomain",
        root_object_name: "Lineage Root",
        upstream: [{ object_id: "FEP-UP", object_type: "FieldEndpoint", object_name: "Upstream", relationship_type: "feeds", depth: 1 }],
        downstream: [{ object_id: "ATTR-DOWN", object_type: "Attribute", object_name: "Downstream", relationship_type: "defines", depth: 1 }],
        total_affected: 2,
      },
    });
    render(<LineageProbe objectId="DOMAIN-LINEAGE" />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("nodes").textContent).toBe("3"));
    expect(screen.getByTestId("loading").textContent).toBe("ready");
    expect(screen.getByTestId("error").textContent).toBe("none");
    expect(screen.getByTestId("edges").textContent).toBe("2");
    expect(screen.getByTestId("upstream").textContent).toBe("1");
    expect(screen.getByTestId("downstream").textContent).toBe("1");
    expect(screen.getByTestId("impact").textContent).toBe("2");
  });

  it("falls back to static demo lineage when the API is unavailable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));
    render(<LineageProbe objectId="DOMAIN-CUSTOMER-BP" />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    expect(screen.getByTestId("error").textContent).toBe("none");
    expect(screen.getByTestId("nodes").textContent).toBe("9");
    expect(screen.getByTestId("edges").textContent).toBe("8");
    expect(screen.getByTestId("impact").textContent).toBe("none");
  });
});

describe("LineageScreen", () => {
  it("renders the path view with live upstream, downstream, and impact summary", async () => {
    mockFetchRoutes({
      "/trace/DOMAIN-LINEAGE": {
        root_object_id: "DOMAIN-LINEAGE",
        root_object_type: "MasterDataDomain",
        root_object_name: "Lineage Root",
        nodes: [
          { object_id: "FEP-UP", object_type: "FieldEndpoint", object_name: "Upstream Field", source_file: "x.md", depth: 1 },
          { object_id: "ATTR-DOWN", object_type: "Attribute", object_name: "Downstream Attribute", source_file: "y.md", depth: 1 },
        ],
        edges: [
          { from_object_id: "FEP-UP", to_object_id: "DOMAIN-LINEAGE", relationship_type: "feeds", direction: "upstream" },
          { from_object_id: "DOMAIN-LINEAGE", to_object_id: "ATTR-DOWN", relationship_type: "defines", direction: "downstream" },
        ],
      },
      "/impact/DOMAIN-LINEAGE": {
        object_id: "DOMAIN-LINEAGE",
        root_object_type: "MasterDataDomain",
        root_object_name: "Lineage Root",
        upstream: [{ object_id: "FEP-UP", object_type: "FieldEndpoint", object_name: "Upstream Field", relationship_type: "feeds", depth: 1 }],
        downstream: [{ object_id: "ATTR-DOWN", object_type: "Attribute", object_name: "Downstream Attribute", relationship_type: "defines", depth: 1 }],
        total_affected: 2,
      },
    });

    const navigate = vi.fn();
    const params = new URLSearchParams({ id: "DOMAIN-LINEAGE" });
    render(
      <TestWrapper>
        <LineageScreen navigate={navigate} params={params} onExport={() => {}} />
      </TestWrapper>
    );

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Lineage Root lineage" })).toBeInTheDocument()
    );

    fireEvent.click(screen.getByRole("button", { name: "Path list view" }));

    await waitFor(() => expect(screen.getByText("Upstream Field")).toBeInTheDocument());
    expect(screen.getByText("Downstream Attribute")).toBeInTheDocument();
    expect(screen.getByText("Total affected")).toBeInTheDocument();
  });
});

function HomeAssistantProbe() {
  const { query, intent, results, loading, error, run, reset } = useHomeAssistant();
  return (
    <div>
      <span data-testid="loading">{loading ? "loading" : "ready"}</span>
      <span data-testid="error">{error || "none"}</span>
      <span data-testid="intent">{intent || "none"}</span>
      <span data-testid="count">{results.length}</span>
      <button data-testid="run" onClick={() => run(query)}>Run</button>
      <button data-testid="reset" onClick={reset}>Reset</button>
      <input
        data-testid="query"
        value={query}
        onChange={(event) => run(event.target.value)}
      />
      {results.map((r) => (
        <span key={r.id} data-testid="result">{r.title}</span>
      ))}
    </div>
  );
}

describe("useHomeAssistant", () => {
  it("classifies and executes a search intent against live API data", async () => {
    mockFetchRoutes({
      "/api/v1/search": {
        total_count: 1,
        results: [{
          object_id: "DOMAIN-LIVE",
          object_type: "MasterDataDomain",
          status: "active",
          name: "Live Domain",
          title: null,
          description: "Live description",
          source_file: "DOMAIN-LIVE.md",
          score: 1,
          matched_fields: ["name"],
        }],
      },
    });
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "find live domain" } });
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("search"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByTestId("result").textContent).toBe("Live Domain");
  });

  it("executes a gaps intent against live findings", async () => {
    mockFetchRoutes({
      "/api/v1/findings": {
        total_count: 1,
        findings: [{
          assessment_id: "ASSESSMENT-TEST",
          finding: {
            id: "FINDING-TEST",
            category: "missing_mapping",
            severity: "high",
            message: "Customer Group is missing a target mapping.",
            lifecycle_state: "open",
          },
          provenance: {
            assessment_run_id: "ASSESSMENT-TEST",
            source_kind: "mapping_profile",
          },
        }],
      },
    });
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "show open high-risk gaps" } });
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("gaps"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByText("Customer Group is missing a target mapping.")).toBeInTheDocument();
  });

  it("executes a recent activity intent against live events", async () => {
    mockFetchRoutes({
      "/api/v1/activity": {
        total_count: 1,
        events: [{
          event_id: "EVT-001",
          event_type: "proposal_applied",
          timestamp: "2026-07-15T12:00:00Z",
          proposal_id: "PP-001",
          changed_object_ids: ["ATTR-CUSTOMER-GROUP"],
          source_state: "canonical",
          canonical_change: true,
        }],
      },
    });
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "what changed recently" } });
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("recent"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByText("proposal applied")).toBeInTheDocument();
  });

  it("executes a proposals intent against live proposals", async () => {
    mockFetchRoutes({
      "/proposals": {
        total_count: 1,
        proposals: [{
          id: "PP-001",
          title: "Add customer group mapping",
          name: "Add customer group mapping",
          status: "pending_review",
          risk_level: "high",
          created_by: "Martenweave AI",
          operations_count: 3,
          affected_objects_count: 2,
          validation_status: "passed",
          operations: [],
          affected_objects: ["ATTR-CUSTOMER-GROUP"],
          source_evidence: [],
          validation_results: [],
        }],
      },
    });
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "open pending proposals" } });
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("proposals"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByText("Add customer group mapping")).toBeInTheDocument();
  });

  it("executes a trace intent by resolving the object id and calling the trace API", async () => {
    mockFetchRoutes({
      "/api/v1/search": {
        total_count: 1,
        results: [{
          object_id: "DOMAIN-TRACE",
          object_type: "MasterDataDomain",
          status: "active",
          name: "Trace Root",
          title: null,
          description: "",
          source_file: "DOMAIN-TRACE.md",
          score: 1,
          matched_fields: ["name"],
        }],
      },
      "/trace/DOMAIN-TRACE": {
        root_object_id: "DOMAIN-TRACE",
        root_object_type: "MasterDataDomain",
        root_object_name: "Trace Root",
        nodes: [
          { object_id: "FEP-UP", object_type: "FieldEndpoint", object_name: "Upstream", source_file: "x.md", depth: 1 },
        ],
        edges: [
          { from_object_id: "FEP-UP", to_object_id: "DOMAIN-TRACE", relationship_type: "feeds", direction: "upstream" },
        ],
      },
      "/impact/DOMAIN-TRACE": {
        object_id: "DOMAIN-TRACE",
        root_object_type: "MasterDataDomain",
        root_object_name: "Trace Root",
        upstream: [],
        downstream: [],
        total_affected: 0,
      },
    });
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "trace Trace Root" } });
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("trace"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByText("Trace: Trace Root")).toBeInTheDocument();
  });

  it("executes an impact intent by resolving the object id and calling the impact API", async () => {
    mockFetchRoutes({
      "/api/v1/search": {
        total_count: 1,
        results: [{
          object_id: "DOMAIN-IMPACT",
          object_type: "MasterDataDomain",
          status: "active",
          name: "Impact Root",
          title: null,
          description: "",
          source_file: "DOMAIN-IMPACT.md",
          score: 1,
          matched_fields: ["name"],
        }],
      },
      "/impact/DOMAIN-IMPACT": {
        object_id: "DOMAIN-IMPACT",
        root_object_type: "MasterDataDomain",
        root_object_name: "Impact Root",
        upstream: [],
        downstream: [{ object_id: "ATTR-DOWN", object_type: "Attribute", object_name: "Downstream", relationship_type: "defines", depth: 1 }],
        total_affected: 1,
      },
    });
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "impact of changing Impact Root" } });
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("impact"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByText("Impact: Impact Root")).toBeInTheDocument();
  });

  it("falls back to demo data when the API is unavailable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "find Business Partner" } });
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("search"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("4"));
    expect(screen.getByText("Business Partner")).toBeInTheDocument();
  });

  it("labels unsupported questions without fabricating an answer", async () => {
    mockFetchRoutes({});
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "what is the weather today" } });
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("unsupported"));
    expect(screen.getByTestId("count").textContent).toBe("0");
  });

  it("clears state on reset", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));
    render(<HomeAssistantProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    fireEvent.change(screen.getByTestId("query"), { target: { value: "find Business Partner" } });
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("4"));
    fireEvent.click(screen.getByTestId("reset"));
    await waitFor(() => expect(screen.getByTestId("intent").textContent).toBe("none"));
    expect(screen.getByTestId("count").textContent).toBe("0");
  });
});

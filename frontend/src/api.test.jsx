import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { useEffect, useState } from "react";

import {
  API_STATE,
  ApiProvider,
  apiObjectToViewModel,
  createApiClient,
  useApi,
  useObjectDetail,
  useObjectSearch,
} from "./api.jsx";
import { modelObjects } from "./data.js";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

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

function TestWrapper({ children, baseUrl = "http://localhost:8000" }) {
  return <ApiProvider baseUrl={baseUrl}>{children}</ApiProvider>;
}

function Probe() {
  const { state, demo, capabilities } = useApi();
  return (
    <div>
      <span data-testid="state">{state}</span>
      <span data-testid="demo">{demo ? "demo" : "live"}</span>
      <span data-testid="version">{capabilities?.version || "none"}</span>
    </div>
  );
}

describe("createApiClient", () => {
  it("fetches capabilities", async () => {
    mockFetch({ api_version: "v1", version: "0.5.0", indexed: true });
    const client = createApiClient("http://localhost:8000");
    const caps = await client.capabilities();
    expect(caps.version).toBe("0.5.0");
    expect(globalThis.fetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/capabilities");
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
    mockFetch({ api_version: "v1", version: "0.5.0", indexed: true, canonical_files: 24 });
    render(<Probe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("state").textContent).toBe(API_STATE.CONNECTED));
    expect(screen.getByTestId("demo").textContent).toBe("live");
    expect(screen.getByTestId("version").textContent).toBe("0.5.0");
  });

  it("falls back to demo mode when the API is unreachable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));
    render(<Probe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("state").textContent).toBe(API_STATE.UNAVAILABLE));
    expect(screen.getByTestId("demo").textContent).toBe("demo");
  });

  it("falls back to demo mode when the index is stale", async () => {
    mockFetch({ api_version: "v1", version: "0.5.0", indexed: false, canonical_files: 0 });
    render(<Probe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("state").textContent).toBe(API_STATE.STALE_INDEX));
    expect(screen.getByTestId("demo").textContent).toBe("demo");
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
    </div>
  );
}

describe("useObjectSearch", () => {
  it("returns live API results when connected", async () => {
    mockFetchSequence(
      { api_version: "v1", version: "0.5.0", indexed: true, canonical_files: 1 },
      { total_count: 1, results: [{ object_id: "DOMAIN-LIVE", object_type: "MasterDataDomain", status: "active", name: "Live Domain", title: null, domain: null, description: "Live", source_file: "x.md", score: 1, matched_fields: [] }] }
    );
    render(<SearchProbe />, { wrapper: TestWrapper });
    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("ready"));
    await waitFor(() => expect(screen.getByTestId("count").textContent).toBe("1"));
    expect(screen.getByTestId("result").textContent).toBe("Live Domain");
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
      { api_version: "v1", version: "0.5.0", indexed: true, canonical_files: 1 },
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

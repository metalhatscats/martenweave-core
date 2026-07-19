import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.location.hash = "#/";
});

describe("Martenweave workbench", () => {
  it("renders the canonical model ledger by default", async () => {
    window.location.hash = "#/";
    render(<App />);
    expect(screen.getByRole("heading", { name: "Canonical model ledger" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText("ATTR-BP-TAX-NUMBER").length).toBeGreaterThan(0));
    expect(screen.getByText("AI proposes. Validators verify. Humans approve.")).toBeInTheDocument();
  });

  it("shows a connecting state instead of sample data while the API probe is pending", () => {
    window.location.hash = "#/home";
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));
    render(<App />);
    expect(screen.getByText(/Connecting to local Martenweave API/)).toBeInTheDocument();
    expect(screen.getByText("Loading canonical objects")).toBeInTheDocument();
    expect(screen.queryByText("ATTR-BP-TAX-NUMBER")).not.toBeInTheDocument();
    expect(screen.queryByText("Demo workspace")).not.toBeInTheDocument();
    expect(screen.queryByText("Demo mode")).not.toBeInTheDocument();
  });

  it("labels an unavailable local backend as demo data without fictional identity", async () => {
    window.location.hash = "#/home";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);

    await waitFor(() => expect(screen.getAllByText("Demo workspace").length).toBeGreaterThan(0));
    expect(screen.getAllByText("Demo mode").length).toBeGreaterThan(0);
    fireEvent.click(document.querySelector(".profile-button"));
    expect(screen.getByText("Sample data")).toBeInTheDocument();
    expect(screen.queryByText("Production")).not.toBeInTheDocument();
  });

  it("derives the workspace label and version from the local API", async () => {
    window.location.hash = "#/home";
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        api_version: "v1",
        version: "0.6.0",
        indexed: true,
        canonical_files: 24,
        read_only: true,
      }),
      text: () => Promise.resolve(""),
    }));
    render(<App />);

    await waitFor(() => expect(screen.getByText("Read-only")).toBeInTheDocument());
    expect(screen.getAllByText("Local workspace").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /Import — This local workspace is read-only/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Export — This local workspace is read-only/ })).toBeDisabled();
  });

  it("uses live canonical objects instead of the sample ledger when connected", async () => {
    window.location.hash = "#/home";
    vi.stubGlobal("fetch", vi.fn((url) => {
      const address = String(url);
      const payload = address.includes("/api/v1/search")
        ? {
          total_count: 1,
          results: [{
            object_id: "DOMAIN-NORTHSTAR",
            object_type: "MasterDataDomain",
            status: "active",
            name: "Northstar Mobility Group",
            title: null,
            domain: "DOMAIN-NORTHSTAR",
            description: "Fictional pilot domain",
            source_file: "model/DOMAIN-NORTHSTAR.md",
            score: 1,
            matched_fields: ["name"],
          }],
        }
        : address.includes("/api/v1/proposals")
          ? { total_count: 0, proposals: [] }
          : address.includes("/api/v1/findings")
            ? { total_count: 0, findings: [] }
            : { api_version: "v1", version: "0.6.1", indexed: true, canonical_files: 187, read_only: true };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload), text: () => Promise.resolve("") });
    }));
    render(<App />);

    await waitFor(() => expect(screen.getAllByText("Northstar Mobility Group").length).toBeGreaterThan(0));
    expect(screen.getByText(/187 objects/)).toBeInTheDocument();
    expect(screen.getByText("Ledger entries loaded")).toBeInTheDocument();
  });

  it("loads generated report metadata from the local API", async () => {
    window.location.hash = "#/reports";
    vi.stubGlobal("fetch", vi.fn((url) => {
      const payload = String(url).includes("/api/v1/reports")
        ? {
          total_count: 1,
          artifacts: [{
            artifact_id: "assessment/review.md",
            name: "review.md",
            format: "MD",
            created_at: "2026-07-15T12:00:00+00:00",
            size_bytes: 20,
            source_state: "generated",
            safety_classification: "local_only",
          }],
        }
        : { api_version: "v1", version: "0.6.0", indexed: true, canonical_files: 24 };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload), text: () => Promise.resolve("") });
    }));
    render(<App />);

    await waitFor(() => expect(screen.getByText("review.md")).toBeInTheDocument());
    expect(screen.getByText("assessment/review.md")).toBeInTheDocument();
    expect(screen.getByText("MD · Local only — review before sharing")).toBeInTheDocument();
    expect(screen.queryByText("customer-migration-model-index-2026-07-03.csv")).not.toBeInTheDocument();
  });

  it("separates live local model history from product release notes", async () => {
    window.location.hash = "#/changelog";
    vi.stubGlobal("fetch", vi.fn((url) => {
      const payload = String(url).includes("/api/v1/activity")
        ? { total_count: 1, events: [{ event_id: "EVT-001", event_type: "proposal_applied", timestamp: "2026-07-15T12:00:00Z", proposal_id: "PP-001", changed_object_ids: ["ATTR-CUSTOMER-GROUP"], source_state: "canonical", canonical_change: true }] }
        : { api_version: "v1", version: "0.6.0", indexed: true, canonical_files: 24 };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload), text: () => Promise.resolve("") });
    }));
    render(<App />);

    await waitFor(() => expect(screen.getByText("Local model history")).toBeInTheDocument());
    expect(screen.getByText("proposal applied")).toBeInTheDocument();
    expect(screen.getByText("ATTR-CUSTOMER-GROUP")).toBeInTheDocument();
    expect(screen.getByText("Product updates")).toBeInTheDocument();
  });

  it("renders typed local assessment findings without static gap claims", async () => {
    window.location.hash = "#/gaps";
    vi.stubGlobal("fetch", vi.fn((url) => {
      const payload = String(url).includes("/api/v1/findings")
        ? { assessment_id: "assessment-run", total_count: 1, findings: [{ assessment_id: "assessment-run", review: { disposition: "confirmed", note: "Verified by stewardship." }, finding: { id: "FINDING-TEST", category: "missing_mapping", severity: "high", message: "Customer Group is missing a target mapping.", lifecycle_state: "open", provenance: { assessment_run_id: "ASSESSMENT-TEST", source_kind: "mapping_profile", location: { sheet: "Mapping", row: 2 } } } }] }
        : { api_version: "v1", version: "0.6.0", indexed: true, canonical_files: 24 };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload), text: () => Promise.resolve("") });
    }));
    render(<App />);

    await waitFor(() => expect(screen.getByText("FINDING-TEST")).toBeInTheDocument());
    expect(screen.getByText("Customer Group is missing a target mapping.")).toBeInTheDocument();
    expect(screen.getAllByText("confirmed").length).toBeGreaterThan(0);
    expect(screen.queryByText("Missing mapping for TAX_NUMBER")).not.toBeInTheDocument();
  });

  it("navigates to models and filters by query", async () => {
    window.location.hash = "#/models";
    render(<App />);
    expect(screen.getByText("Canonical search")).toBeInTheDocument();
    expect(screen.getByText("Local evidence")).toBeInTheDocument();
    expect(screen.queryByText("AI answer")).not.toBeInTheDocument();
    const pageInput = screen.getByRole("main").querySelector(".global-search input");
    fireEvent.change(pageInput, { target: { value: "TAX_NUMBER" } });
    await waitFor(() => {
      expect(screen.queryByText("Customer alternative key mapping")).not.toBeInTheDocument();
    });
  });

  it("opens workspace activity from the top bar", async () => {
    window.location.hash = "#/home";
    render(<App />);
    fireEvent.click(screen.getByLabelText("Workspace activity"));
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    expect(screen.getByText(/Recent local validation, evidence, and review events/)).toBeInTheDocument();
  });

  it("completes the sample import flow", async () => {
    window.location.hash = "#/home";
    render(<App />);
    fireEvent.click(screen.getByText("Load model"));
    fireEvent.click(screen.getByText("Use sample files"));
    await waitFor(() => expect(screen.getByText("Detected model knowledge")).toBeInTheDocument(), {
      timeout: 2500,
    });
    fireEvent.click(screen.getByText("Load into workspace"));
    await waitFor(() =>
      expect(screen.getByText(/Model loaded: 24 objects indexed/)).toBeInTheDocument(),
    );
  });

  it("generates a model export", async () => {
    window.location.hash = "#/home";
    render(<App />);
    await waitFor(() => expect(screen.getAllByText("Demo workspace").length).toBeGreaterThan(0));
    fireEvent.click(await screen.findByText("Export ledger"));
    fireEvent.click(screen.getByText("Generate export"));
    await waitFor(() => expect(screen.getByText("Model index is ready")).toBeInTheDocument());
    expect(screen.getByText("customer-migration-index-2026-07-03.csv")).toBeInTheDocument();
  });

  it("opens the command palette with the keyboard shortcut", async () => {
    window.location.hash = "#/home";
    render(<App />);
    fireEvent.keyDown(window, { key: "k", metaKey: true });
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    expect(screen.getByPlaceholderText("Search commands or model objects…")).toBeInTheDocument();
    expect(screen.getByText("Open import flow")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "ArrowDown" });
    fireEvent.keyDown(window, { key: "Enter" });
    await waitFor(() => expect(screen.getByText("Load model knowledge")).toBeInTheDocument());
  });

  it("supports global navigation and selected-row shortcuts", async () => {
    window.location.hash = "#/home";
    render(<App />);
    fireEvent.keyDown(window, { key: "/" });
    expect(screen.getByLabelText("Search model")).toHaveFocus();
    fireEvent.keyDown(screen.getByLabelText("Search model"), { key: "Escape" });
    screen.getByLabelText("Search model").blur();
    await waitFor(() => expect(screen.getAllByText("ATTR-BP-TAX-NUMBER").length).toBeGreaterThan(0));
    fireEvent.keyDown(window, { key: "Enter" });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Business Partner" })).toBeInTheDocument());
    fireEvent.keyDown(window, { key: "g" });
    fireEvent.keyDown(window, { key: "m" });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Global model search" })).toBeInTheDocument());
  });

  it("opens proposal decision dialog and records approval", async () => {
    window.location.hash = "#/proposal?id=27";
    render(<App />);
    await waitFor(() => expect(screen.getAllByText("Demo workspace").length).toBeGreaterThan(0));
    fireEvent.click(await screen.findByText(/Approve proposal/));
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    await waitFor(() => expect(screen.getByText(/Approved: Proposal #27/)).toBeInTheDocument());
  });

  it("returns an approved proposal to draft", async () => {
    window.location.hash = "#/proposal?id=27";
    render(<App />);
    await waitFor(() => expect(screen.getAllByText("Demo workspace").length).toBeGreaterThan(0));
    fireEvent.click(await screen.findByText(/Approve proposal/));
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    await waitFor(() => expect(screen.getByText(/Approved: Proposal #27/)).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Return to draft" }));
    await waitFor(() => expect(screen.getByText(/Proposal #27 returned to draft/)).toBeInTheDocument());
  });

  it("filters proposals by status tab", async () => {
    window.location.hash = "#/proposals";
    render(<App />);
    fireEvent.click(screen.getByText("Approved"));
    await waitFor(() => expect(screen.getByText("No proposals match")).toBeInTheDocument());
  });

  it("shows the website changelog", () => {
    window.location.hash = "#/changelog";
    render(<App />);
    expect(screen.getByRole("heading", { name: "Changelog" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Model Ledger workbench" })).toBeInTheDocument();
    expect(screen.getByText("Synced with CHANGELOG.md")).toBeInTheDocument();
  });

  it("renders the evidence-backed model assistant on the home screen", () => {
    window.location.hash = "#/home";
    render(<App />);
    expect(screen.getByRole("heading", { name: "Ask about your model" })).toBeInTheDocument();
    expect(screen.getByLabelText("Ask a model question")).toBeInTheDocument();
    expect(screen.getByText("Deterministic · works offline")).toBeInTheDocument();
  });

  it("runs a suggested question and renders evidence-backed result cards", async () => {
    window.location.hash = "#/home";
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Find Business Partner" }));
    await waitFor(() => expect(screen.getByText("Search results")).toBeInTheDocument());
    expect(screen.getByText(/results? · Demo data/)).toBeInTheDocument();
    expect(screen.getAllByText("Business Partner").length).toBeGreaterThan(0);
  });

  it("labels unsupported prompts and offers relevant actions instead of invented answers", async () => {
    window.location.hash = "#/home";
    render(<App />);
    const input = screen.getByLabelText("Ask a model question");
    fireEvent.change(input, { target: { value: "what is the weather today" } });
    fireEvent.click(screen.getByRole("button", { name: "Run query" }));
    await waitFor(() => expect(screen.getByText("Not supported yet")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /Search objects/ })).toBeInTheDocument();
  });

  it("navigates from an assistant result card to the object screen", async () => {
    window.location.hash = "#/home";
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Find Business Partner" }));
    await waitFor(() => expect(screen.getByText("Search results")).toBeInTheDocument());
    const resultCards = screen.getAllByText("Business Partner").filter((element) =>
      element.closest(".result-card")
    );
    expect(resultCards.length).toBeGreaterThan(0);
    fireEvent.click(resultCards[0]);
    await waitFor(() => expect(screen.getByRole("heading", { name: "Business Partner" })).toBeInTheDocument());
  });
});

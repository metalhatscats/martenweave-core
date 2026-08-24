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
  it("renders the decision-first readiness workspace by default", async () => {
    window.location.hash = "#/";
    render(<App />);
    expect(screen.getByRole("heading", { name: "Opening local evidence…" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Readiness" })).toBeInTheDocument();
  });

  it("shows a connecting state instead of sample data while the API probe is pending", () => {
    window.location.hash = "#/home";
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));
    render(<App />);
    expect(screen.getByText(/Connecting to local Martenweave API/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Opening local evidence…" })).toBeInTheDocument();
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

  it("uses local API readiness findings instead of demo signals when connected", async () => {
    window.location.hash = "#/home";
    vi.stubGlobal("fetch", vi.fn((url) => {
      const address = String(url);
      const payload = address.includes("/api/v1/findings")
        ? {
          total_count: 1, findings: [{ finding: { id: "FINDING-NORTHSTAR", severity: "high", message: "Northstar mapping needs review.", affected_objects: ["DOMAIN-NORTHSTAR"], provenance: { location: { file: "model/DOMAIN-NORTHSTAR.md" } } } }],
        }
        : address.includes("/api/v1/proposals")
          ? { total_count: 0, proposals: [] }
          : { api_version: "v1", version: "0.6.1", indexed: true, canonical_files: 187, read_only: true };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload), text: () => Promise.resolve("") });
    }));
    render(<App />);

    await waitFor(() => expect(screen.getAllByText("Northstar mapping needs review.").length).toBeGreaterThan(0));
    expect(screen.getByRole("heading", { name: /evidence decision remains before change review/ })).toBeInTheDocument();
  });

  const START_BLOCKED_RESULT = {
    available: true,
    verdict: "blocked",
    total_findings: 2,
    dataset_gaps: 2,
    model_gaps: 0,
    validation_errors: 0,
    validation_warnings: 0,
    recommended_next_action: "Review finding `GAP-CUSTOMER-ID` (customer_id): create a FieldEndpoint. Then re-run readiness.",
    findings: [
      { id: "GAP-CUSTOMER-ID", severity: "high", message: "Dataset column 'customer_id' has no matching FieldEndpoint.", affected_objects: ["customer_id"], evidence_refs: ["readiness.json"], recommended_action: "Create a FieldEndpoint for customer_id.", provenance: { assessment_run_id: "READINESS-CUSTOMER_SAMPLE", location: { column_name: "customer_id" } } },
      { id: "GAP-CUSTOMER-GROUP", severity: "medium", message: "Dataset column 'customer_group' has no matching FieldEndpoint.", affected_objects: ["customer_group"], evidence_refs: ["readiness.json"], recommended_action: "Create a FieldEndpoint for customer_group.", provenance: { assessment_run_id: "READINESS-CUSTOMER_SAMPLE", location: { column_name: "customer_group" } } },
    ],
    evidence: {
      readiness_json: "readiness/readiness.json",
      readiness_markdown: "readiness/readiness.md",
      profile: "dataset_profiles/customer_sample.json",
      draft_proposal: "model/patch-proposals/PP-INFER-CUSTOMER-SAMPLE.md",
    },
    provenance: { created_at: "2026-08-02T10:00:00Z", input_name: "customer_sample.csv", input_format: "csv", input_sha256: "abc123def456", tool_version: "0.9.0" },
    decision_gate: {
      total: 2,
      reviewed: 0,
      remaining: 2,
      deferred: 0,
      proposal_review_ready: false,
      gate_reason: "Classify 2 remaining evidence finding(s).",
      assessment_id: "readiness",
      proposal_id: "PP-INFER-CUSTOMER-SAMPLE",
    },
  };

  function stubStartWorkspaceFetch(startResult, { readOnly = true } = {}) {
    vi.stubGlobal("fetch", vi.fn((url) => {
      const address = String(url);
      const payload = address.includes("/api/v1/start-result")
        ? startResult
        : address.includes("/api/v1/findings")
          ? { total_count: 0, findings: [] }
          : address.includes("/api/v1/proposals")
            ? { total_count: 1, proposals: [{ id: "PP-INFER-CUSTOMER-SAMPLE", status: "pending_review", title: "Inferred model", operations_count: 10, affected_objects_count: 10, risk_level: "high", validation_status: "valid" }] }
            : address.includes("/api/v1/recovery")
              ? { states: [] }
              : {
                api_version: "v1", version: "0.9.0", indexed: true, canonical_files: 2,
                read_only: readOnly, read: [], mutations: [], recovery: [],
                ai: { active_providers: ["no_provider"] },
              };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload), text: () => Promise.resolve("") });
    }));
  }

  it("renders the persisted start verdict, finding count, and one primary action", async () => {
    window.location.hash = "#/home";
    stubStartWorkspaceFetch(START_BLOCKED_RESULT);
    render(<App />);

    await waitFor(() => expect(screen.getByRole("heading", { name: "2 evidence decisions remain before change review." })).toBeInTheDocument());
    expect(screen.getAllByText("Dataset column 'customer_id' has no matching FieldEndpoint.").length).toBeGreaterThan(0);
    expect(screen.queryByText(/items? need your attention/)).not.toBeInTheDocument();
    expect(screen.queryByText("Working in local sample mode")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Classify next finding/ })).toBeInTheDocument();
    expect(screen.getByText(/Accepted risk and deferral require a recorded rationale/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open persisted report/ })).toHaveAttribute("href", expect.stringContaining("/api/v1/reports/readiness/readiness.md"));
    expect(screen.getByText(/Persisted start run · sha256 abc123def456/)).toBeInTheDocument();
    expect(screen.getByText(/Read-only workspace: evidence remains inspectable/)).toBeInTheDocument();
    expect(screen.getByText(/No AI provider is active. The findings shown here are deterministic/)).toBeInTheDocument();
  });

  it("records a human disposition before opening the candidate change", async () => {
    window.location.hash = "#/home";
    vi.stubGlobal("fetch", vi.fn((url, options = {}) => {
      const address = String(url);
      let payload;
      if (address.includes("/api/v1/findings/review") && options.method === "POST") {
        const body = JSON.parse(options.body);
        payload = { ...body, reviewed_at: "2026-08-24T10:00:00Z", note: body.note || "" };
      } else if (address.includes("/api/v1/start-result")) payload = START_BLOCKED_RESULT;
      else if (address.includes("/api/v1/findings")) payload = { total_count: 0, findings: [] };
      else if (address.includes("/api/v1/proposals")) payload = { total_count: 1, proposals: [] };
      else if (address.includes("/api/v1/recovery")) payload = { states: [] };
      else payload = {
        api_version: "v1", version: "0.9.0", indexed: true, canonical_files: 2,
        read_only: false, read: [], mutations: [{ name: "review_finding" }], recovery: [],
        ai: { active_providers: ["no_provider"] },
      };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload), text: () => Promise.resolve("") });
    }));
    render(<App />);

    await screen.findByRole("heading", { name: "2 evidence decisions remain before change review." });
    fireEvent.click(screen.getByRole("button", { name: /Confirm gap/ }));
    fireEvent.click(screen.getByRole("button", { name: /Record decision/ }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "1 evidence decision remains before change review." })).toBeInTheDocument());
    expect(screen.getByText(/1\/2 findings classified/)).toBeInTheDocument();
  });

  it("shows the healthy start verdict with a no-mutation primary action", async () => {
    window.location.hash = "#/home";
    stubStartWorkspaceFetch({
      ...START_BLOCKED_RESULT,
      verdict: "ready",
      total_findings: 0,
      dataset_gaps: 0,
      findings: [],
      recommended_next_action: "No action required: all 1 dataset column(s) matched canonical FieldEndpoints.",
      evidence: { readiness_json: "readiness/readiness.json", readiness_markdown: "readiness/readiness.md", profile: "dataset_profiles/input.json", draft_proposal: null },
    });
    render(<App />);

    await waitFor(() => expect(screen.getByRole("heading", { name: "This file is ready for governed inspection." })).toBeInTheDocument());
    expect(screen.getByText("No open findings in this case")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Inspect governed model/ })).toBeInTheDocument();
  });

  it("states the no-input state instead of a fabricated zero result", async () => {
    window.location.hash = "#/home";
    stubStartWorkspaceFetch({ available: false });
    render(<App />);

    await waitFor(() => expect(screen.getByRole("heading", { name: "Start with one migration artifact" })).toBeInTheDocument());
    expect(screen.getByText(/martenweave start <dataset-file>/)).toBeInTheDocument();
    expect(screen.queryByText(/items? need your attention/)).not.toBeInTheDocument();
    expect(screen.queryByText("Sample evidence ready")).not.toBeInTheDocument();
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

  it("keeps the sample import flow available from the command palette", async () => {
    window.location.hash = "#/home";
    render(<App />);
    fireEvent.keyDown(window, { key: "k", metaKey: true });
    await waitFor(() => expect(screen.getByText("Open import flow")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Open import flow"));
    await waitFor(() => expect(screen.getByText("Load model knowledge")).toBeInTheDocument());
  });

  it("keeps export available as a governed workspace action", async () => {
    window.location.hash = "#/home";
    render(<App />);
    await waitFor(() => expect(screen.getAllByText("Demo workspace").length).toBeGreaterThan(0));
    fireEvent.keyDown(window, { key: "k", metaKey: true });
    await waitFor(() => expect(screen.getByText("Export current report")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Export current report"));
    await waitFor(() => expect(screen.getByText("Export project output")).toBeInTheDocument());
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

  it("supports global navigation from the readiness workspace", async () => {
    window.location.hash = "#/home";
    render(<App />);
    await waitFor(() => expect(screen.getAllByText("Demo workspace").length).toBeGreaterThan(0));
    fireEvent.keyDown(window, { key: "/" });
    expect(screen.getByLabelText("Search model")).toHaveFocus();
    fireEvent.keyDown(screen.getByLabelText("Search model"), { key: "Escape" });
    screen.getByLabelText("Search model").blur();
    fireEvent.keyDown(window, { key: "g" });
    fireEvent.keyDown(window, { key: "m" });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Global model search" })).toBeInTheDocument());
  });

  it("opens proposal decision dialog and records approval", async () => {
    window.location.hash = "#/proposal?id=27";
    render(<App />);
    await waitFor(() => expect(screen.getAllByText("Demo workspace").length).toBeGreaterThan(0));
    const approveButtons = await screen.findAllByRole("button", { name: "Approve proposal" });
    fireEvent.click(approveButtons[0]);
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    await waitFor(() => expect(screen.getByText(/Approved: Proposal #27/)).toBeInTheDocument());
  });

  it("returns an approved proposal to draft", async () => {
    window.location.hash = "#/proposal?id=27";
    render(<App />);
    await waitFor(() => expect(screen.getAllByText("Demo workspace").length).toBeGreaterThan(0));
    const approveButtons = await screen.findAllByRole("button", { name: "Approve proposal" });
    fireEvent.click(approveButtons[0]);
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
    expect(screen.getByRole("heading", { name: "Decision history" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Model Ledger workbench" })).toBeInTheDocument();
    expect(screen.getByText("Synced with CHANGELOG.md")).toBeInTheDocument();
  });

  it("renders a contextual command bar without a generic chatbot", async () => {
    window.location.hash = "#/home";
    render(<App />);
    await waitFor(() => expect(screen.getByText(/Explain DEMO_FINDING/)).toBeInTheDocument());
    expect(screen.queryByRole("heading", { name: "Ask about your model" })).not.toBeInTheDocument();
  });

  it("opens context for a selected evidence finding", async () => {
    window.location.hash = "#/home";
    render(<App />);
    await waitFor(() => expect(screen.getByRole("listbox", { name: "Readiness queue" })).toBeInTheDocument());
    const findings = screen.getAllByRole("option");
    fireEvent.click(findings[1]);
    expect(findings[1]).toHaveAttribute("aria-selected", "true");
    expect(screen.getAllByText("Human decision").length).toBeGreaterThan(0);
  });

  it("filters the current evidence case locally", async () => {
    window.location.hash = "#/home";
    render(<App />);
    const input = await screen.findByLabelText("Find in this evidence case");
    fireEvent.change(input, { target: { value: "definitely missing" } });
    expect(screen.getByText(/No evidence matches/)).toBeInTheDocument();
  });

  it("navigates from the context panel to related evidence", async () => {
    window.location.hash = "#/home";
    vi.stubGlobal("ResizeObserver", class {
      observe() {}
      unobserve() {}
      disconnect() {}
    });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Open related evidence" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: /lineage/i })).toBeInTheDocument());
  });
});

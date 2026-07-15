import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

afterEach(() => {
  cleanup();
  window.location.hash = "#/";
});

describe("Martenweave workbench", () => {
  it("renders the canonical model ledger by default", () => {
    window.location.hash = "#/";
    render(<App />);
    expect(screen.getByRole("heading", { name: "Canonical model ledger" })).toBeInTheDocument();
    expect(screen.getAllByText("ATTR-BP-TAX-NUMBER").length).toBeGreaterThan(0);
    expect(screen.getByText("AI proposes. Validators verify. Humans approve.")).toBeInTheDocument();
  });

  it("navigates to models and filters by query", async () => {
    window.location.hash = "#/models";
    render(<App />);
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
    fireEvent.click(screen.getByText("Export ledger"));
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
    fireEvent.keyDown(window, { key: "Enter" });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Business Partner" })).toBeInTheDocument());
    fireEvent.keyDown(window, { key: "g" });
    fireEvent.keyDown(window, { key: "m" });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Global model search" })).toBeInTheDocument());
  });

  it("opens proposal decision dialog and records approval", async () => {
    window.location.hash = "#/proposal?id=27";
    render(<App />);
    fireEvent.click(screen.getByText(/Approve proposal/));
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    await waitFor(() => expect(screen.getByText(/Approved: Proposal #27/)).toBeInTheDocument());
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
});

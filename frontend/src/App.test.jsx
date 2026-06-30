import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { App } from "./App";

describe("App routing", () => {
  it("renders home by default", () => {
    window.location.hash = "#/";
    render(<App />);
    expect(screen.getByText("Ask your model layer anything")).toBeInTheDocument();
  });

  it("navigates to models and filters by query", async () => {
    window.location.hash = "#/models";
    render(<App />);
    const input = screen.getByPlaceholderText("Search model");
    fireEvent.change(input, { target: { value: "TAX_NUMBER" } });
    await waitFor(() => {
      expect(screen.queryByText("Customer alternative key mapping")).not.toBeInTheDocument();
    });
  });

  it("disables notification button with explanation", () => {
    window.location.hash = "#/home";
    render(<App />);
    const bell = screen.getByLabelText(/Notifications/);
    expect(bell).toBeDisabled();
  });

  it("opens proposal decision dialog and returns to list", async () => {
    window.location.hash = "#/proposal?id=27";
    render(<App />);
    fireEvent.click(screen.getByText(/Approve proposal/));
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Cancel"));
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("filters proposals by status tab", async () => {
    window.location.hash = "#/proposals";
    render(<App />);
    fireEvent.click(screen.getByText("Approved"));
    await waitFor(() => {
      expect(screen.getByText("No proposals match")).toBeInTheDocument();
    });
  });
});

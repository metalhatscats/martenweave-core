import { test, expect } from "@playwright/test";
import path from "node:path";
import { existsSync, readdirSync, writeFileSync } from "node:fs";
import { apiDownloadReport, apiGet } from "./fixtures/api.js";
import { seedFinding } from "./fixtures/repo.js";
import {
  createApprovedChangeRequest,
  createAcceptedProposal,
  createAttributeOperation,
  createPendingProposal,
} from "./fixtures/proposal.js";

const repoPath = process.env.MARTENWEAVE_E2E_REPO;
const BASE_URL = "http://127.0.0.1:5173";

async function gotoHash(page, hash) {
  await page.goto(`${BASE_URL}/${hash}`);
}

function uniqueId(prefix) {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

function listModelEntries() {
  return readdirSync(path.join(repoPath, "model"));
}

test.describe("connected workbench", () => {
  test.beforeAll(async () => {
    if (!repoPath || !existsSync(repoPath)) {
      throw new Error(
        `Temporary repository is missing. Expected MARTENWEAVE_E2E_REPO to be set.`
      );
    }
  });

  test("workspace shows repository health", async ({ page }) => {
    await gotoHash(page, "#/home");
    const pill = page.locator(".environment-pill");
    await expect(pill).toContainText("Local API", { timeout: 15000 });
    await expect(page.locator(".repo-switcher")).toContainText("Local workspace");
  });

  test("search for Customer Group and open object detail", async ({ page }) => {
    await gotoHash(page, "#/models?search=Customer%20Group");
    await page.waitForSelector(".result-row", { timeout: 15000 });
    const result = page
      .locator(".result-row")
      .filter({ hasText: "Customer Group" })
      .first();
    await expect(result).toBeVisible();
    await result.click();
    await expect(page.locator(".object-hero h1")).toContainText("Customer Group");
  });

  test("trace KNVV-KDGRP and inspect impact", async ({ page }) => {
    await gotoHash(page, "#/lineage?id=FEP-S4-KNVV-KDGRP");
    await page.waitForSelector(".lineage-canvas, .lineage-path-view", {
      timeout: 15000,
    });
    await expect(page.locator(".lineage-header h1")).toContainText(/lineage/i);
  });

  test("open gaps, review evidence, and set a disposition", async ({ page }) => {
    const assessmentName = `assessment-${new Date().toISOString().slice(0, 10)}`;
    const findingId = uniqueId("F-CONN");
    await seedFinding(repoPath, assessmentName, {
      id: findingId,
      category: "coverage",
      severity: "medium",
      message: "Missing Customer Group mapping in connected e2e test",
      status: "open",
      lifecycle_state: "open",
      provenance: {
        assessment_run_id: assessmentName,
        source_kind: "model_validation",
        detection_mode: "deterministic",
        rule_id: "model_validation:coverage",
        location: { file: "model/attributes/ATTR-CUST-SALES-CUSTOMER-GROUP.md" },
        evidence_refs: ["model/attributes/ATTR-CUST-SALES-CUSTOMER-GROUP.md"],
        affected_objects: ["ATTR-CUST-SALES-CUSTOMER-GROUP"],
      },
      rule_id: "model_validation:coverage",
      evidence_refs: ["model/attributes/ATTR-CUST-SALES-CUSTOMER-GROUP.md"],
      affected_objects: ["ATTR-CUST-SALES-CUSTOMER-GROUP"],
      recommended_action: "Add the missing Customer Group mapping.",
      readiness_impact: "ready_with_warnings",
    });

    // Verify the API sees the seeded finding.
    const findings = await apiGet("/api/v1/findings");
    expect(findings.total_count).toBeGreaterThan(0);

    await gotoHash(page, "#/gaps");
    await page.waitForSelector(".gap-card", { timeout: 15000 });

    const reviewForm = page.locator(".finding-review-form").first();
    await reviewForm.locator("select").selectOption("confirmed");
    await reviewForm.locator("textarea").fill("Confirmed in connected e2e test.");
    await reviewForm.locator('button:has-text("Save disposition")').click();

    const firstGap = page.locator(".gap-card").first();
    await expect(firstGap).toContainText("confirmed", { timeout: 10000 });
  });

  test("review and approve a proposal without applying it", async ({ page }) => {
    const proposalId = uniqueId("PP-CONN-APPROVE");
    createPendingProposal(repoPath, proposalId, []);

    await gotoHash(page, "#/proposals");
    await page.waitForSelector(".proposal-row", { timeout: 15000 });

    const row = page.locator(".proposal-row").filter({ hasText: proposalId }).first();
    await expect(row).toBeVisible();
    await row.click();

    await page.click('button:has-text("Approve proposal")');
    await page.waitForSelector("[role='dialog']", { timeout: 10000 });
    await page.click(".decision-dialog button:has-text('Approve')");

    await expect(page.locator(".proposal-title-row .badge").first()).toContainText(
      "Approved",
      { timeout: 10000 }
    );
  });

  test("apply an approved proposal and verify the receipt", async ({ page }) => {
    const objectId = uniqueId("ATTR-CONN-APPLY");
    const proposalId = uniqueId("PP-CONN-APPLY");
    const crId = uniqueId("CR-CONN-APPLY");
    createAcceptedProposal(repoPath, proposalId, [
      createAttributeOperation(
        objectId,
        "Connected E2E Attribute",
        "DOMAIN-CUSTOMER-BP"
      ),
    ]);
    createApprovedChangeRequest(repoPath, crId, proposalId);

    await gotoHash(page, "#/proposals");
    await page.waitForSelector(".proposal-row", { timeout: 15000 });

    const row = page.locator(".proposal-row").filter({ hasText: proposalId }).first();
    await expect(row).toBeVisible();
    await row.click();

    await page.click('button:has-text("Apply to canonical")');
    await page.waitForSelector(".workbench-toast", { timeout: 15000 });
    await expect(page.locator(".workbench-toast")).toContainText("Applied");

    const objectFile = path.join(repoPath, "model", "attributes", `${objectId}.md`);
    expect(existsSync(objectFile)).toBe(true);

    const transactionsDir = path.join(repoPath, "generated", "patch-transactions");
    expect(existsSync(transactionsDir)).toBe(true);
    const txDirs = readdirSync(transactionsDir);
    expect(txDirs.length).toBeGreaterThan(0);
    const receiptPath = path.join(transactionsDir, txDirs[0], "receipt.json");
    expect(existsSync(receiptPath)).toBe(true);
  });

  test("generate and download a business review pack", async ({ page }) => {
    await gotoHash(page, "#/reports");
    await page.click('button:has-text("New export")');

    await page.waitForSelector(".export-modal", { timeout: 10000 });
    await page.locator('label:has-text("Format") select').selectOption("XLSX");

    // Generate the export and wait for the backend mutation to complete.
    const [exportResponse] = await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes("/api/v1/exports") &&
          response.request().method() === "POST"
      ),
      page.click('button:has-text("Generate export")'),
    ]);
    expect(exportResponse.status()).toBe(200);

    // The dialog triggers a file download via window.location.assign. Verify
    // the artifact is downloadable through the local API.
    const { status } = await apiDownloadReport("exports/model.xlsx");
    expect(status).toBe(200);
  });

  test("import preflight and cancel without writes", async ({ page }) => {
    const csvPath = path.join(repoPath, "e2e-sample.csv");
    writeFileSync(
      csvPath,
      "id,name,customer_group\n1,Acme Industries,A\n2,Globex Corp,B\n",
      "utf-8"
    );

    const modelBefore = listModelEntries();

    await gotoHash(page, "#/home");
    await page.click('button:has-text("Import")');
    await page.waitForSelector(".import-modal", { timeout: 10000 });

    await page.click('button:has-text("Dataset extracts")');
    await page.locator('.import-modal input[type="file"]').setInputFiles(csvPath);
    await page.click('button:has-text("Profile / Preview")');

    await page.waitForSelector(".import-summary", { timeout: 20000 });
    await expect(page.locator(".import-summary")).toContainText("Sheets");
    await expect(page.locator(".parsed-preview")).toContainText("Workbook interpretation");
    await page.click('button:has-text("Run dataset profile")');
    await expect(page.locator(".import-summary")).toContainText("Rows");

    // The review step has "Back" and "Load into workspace"; return to the
    // source step to find the Cancel button.
    await page.click('.import-modal footer button:has-text("Back")');
    await page.click('.import-modal footer button:has-text("Cancel")');
    await page.waitForSelector(".import-modal", { state: "hidden", timeout: 10000 });

    const modelAfter = listModelEntries();
    expect(modelAfter.sort()).toEqual(modelBefore.sort());
  });
});

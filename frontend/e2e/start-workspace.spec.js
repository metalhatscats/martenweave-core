/**
 * Connected e2e coverage for workspaces created by `martenweave start` (#626).
 *
 * Each state runs against the packaged Workbench (API + SPA on one origin),
 * served from real local workspaces on disk:
 *   - blocked: a genuine `martenweave start` run with a blocked verdict.
 *   - healthy: a genuine deterministic readiness run with a ready verdict.
 *   - empty: an initialized workspace with no persisted start run.
 * The blocked workspace is served exactly as `martenweave workbench` serves it:
 * read-only and without an AI provider.
 */

import { test, expect } from "@playwright/test";
import { spawn, spawnSync } from "node:child_process";
import { openSync } from "node:fs";
import path from "node:path";
import {
  createEmptyWorkspace,
  createHealthyStartWorkspace,
  createStartWorkspace,
  MARTENWEAVE_BIN,
  PROJECT_ROOT,
  REPOS_DIR,
  removeTempRepo,
} from "./fixtures/repo.js";

const FIXTURE_CSV = path.join(PROJECT_ROOT, "tests", "fixtures", "customer_sample.csv");
const FRONTEND_DIR = path.join(PROJECT_ROOT, "frontend");

const STATES = {
  blocked: { port: 8630, workspace: path.join(REPOS_DIR, "start-blocked") },
  healthy: { port: 8631, workspace: path.join(REPOS_DIR, "start-healthy") },
  empty: { port: 8632, workspace: path.join(REPOS_DIR, "start-empty") },
};

const processes = [];

async function waitForHealth(port, timeoutMs = 120_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/health`);
      if (response.ok) return;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Workbench on port ${port} did not become healthy: ${lastError}`);
}

function spawnWorkbench(workspace, port) {
  const logFd = openSync(path.join(REPOS_DIR, `workbench-${port}.log`), "a");
  const child = spawn(
    MARTENWEAVE_BIN,
    ["workbench", "--repo", workspace, "--port", String(port), "--host", "127.0.0.1", "--no-open"],
    { detached: true, stdio: ["ignore", logFd, logFd] }
  );
  processes.push(child);
  return child;
}

test.describe("start-created workspaces", () => {
  test.describe.configure({ timeout: 300_000 });

  test.beforeAll(async () => {
    const build = spawnSync("npm", ["run", "build"], {
      cwd: FRONTEND_DIR,
      encoding: "utf-8",
      timeout: 240_000,
    });
    if (build.status !== 0) {
      throw new Error(`frontend build failed:\n${build.stdout}\n${build.stderr}`);
    }

    createStartWorkspace(STATES.blocked.workspace, FIXTURE_CSV);
    await createHealthyStartWorkspace(STATES.healthy.workspace);
    await createEmptyWorkspace(STATES.empty.workspace);

    for (const state of Object.values(STATES)) {
      spawnWorkbench(state.workspace, state.port);
    }
    for (const state of Object.values(STATES)) {
      await waitForHealth(state.port);
    }
  });

  test.afterAll(async () => {
    for (const child of processes) {
      try {
        process.kill(-child.pid, "SIGTERM");
      } catch {
        // The process group may already be gone.
      }
    }
    for (const state of Object.values(STATES)) {
      await removeTempRepo(state.workspace);
    }
  });

  test("blocked workspace renders the persisted verdict, findings, and one safe action", async ({ page }) => {
    const base = `http://127.0.0.1:${STATES.blocked.port}`;
    await page.goto(`${base}/#/home`);

    await expect(page.getByText("Readiness verdict: blocked")).toBeVisible({ timeout: 20000 });
    await expect(page.getByText("4 findings from the start run · verdict: blocked")).toBeVisible();
    await expect(
      page.getByText("Dataset column 'customer_id' has no matching FieldEndpoint.").first()
    ).toBeVisible();

    // One primary, capability-safe action with its mutation boundary stated.
    await expect(page.getByRole("button", { name: /Review draft proposal/ })).toBeVisible();
    await expect(
      page.getByText(/Mutation boundary: nothing is applied without explicit approval/)
    ).toBeVisible();

    // Real evidence links and provenance, never sample or zero substitutes.
    const reportLink = page.getByRole("link", { name: /Readiness report \(Markdown\)/ });
    await expect(reportLink).toHaveAttribute("href", /\/api\/v1\/reports\/readiness\/readiness\.md/);
    await expect(page.getByText(/Provenance: customer_sample\.csv/)).toBeVisible();
    await expect(page.getByText(/items? need your attention/)).toHaveCount(0);
    await expect(page.getByText("Working in local sample mode")).toHaveCount(0);
    await expect(page.getByText("Sample evidence ready")).toHaveCount(0);

    // Read-only and AI-unconfigured boundaries are stated, not hidden.
    await expect(
      page.getByText(/Read-only session: findings, evidence, catalog, and reports still work/)
    ).toBeVisible();
    await expect(
      page.getByText(/No AI provider configured: every result shown here is deterministic/)
    ).toBeVisible();
  });

  test("blocked workspace shows real catalog objects and generated outputs", async ({ page }) => {
    const base = `http://127.0.0.1:${STATES.blocked.port}`;

    await page.goto(`${base}/#/models?search=Example`);
    await page.waitForSelector(".result-row", { timeout: 20000 });
    await expect(page.locator(".result-row").filter({ hasText: "Example Domain" })).toBeVisible();

    await page.goto(`${base}/#/reports`);
    await expect(page.getByRole("button", { name: /readiness\.md/ })).toBeVisible({ timeout: 20000 });
    await expect(page.getByRole("button", { name: /start_manifest\.json/ })).toBeVisible();
  });

  test("healthy workspace renders the ready verdict with a no-mutation action", async ({ page }) => {
    const base = `http://127.0.0.1:${STATES.healthy.port}`;
    await page.goto(`${base}/#/home`);

    await expect(page.getByText("Readiness verdict: ready")).toBeVisible({ timeout: 20000 });
    await expect(page.getByText("No open findings · verdict: ready")).toBeVisible();
    await expect(page.getByText("No open findings", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: /Browse the catalog/ })).toBeVisible();
    await expect(page.getByText(/items? need your attention/)).toHaveCount(0);
  });

  test("empty workspace states the no-input state instead of a fabricated zero", async ({ page }) => {
    const base = `http://127.0.0.1:${STATES.empty.port}`;
    await page.goto(`${base}/#/home`);

    await expect(page.getByText("No first-value result yet")).toBeVisible({ timeout: 20000 });
    await expect(page.getByText("No readiness result persisted")).toBeVisible();
    await expect(page.getByText("No persisted readiness result")).toBeVisible();
    await expect(page.getByText(/martenweave start/).first()).toBeVisible();
    await expect(page.getByText("Sample evidence ready")).toHaveCount(0);
    await expect(page.getByText(/items? need your attention/)).toHaveCount(0);
  });
});

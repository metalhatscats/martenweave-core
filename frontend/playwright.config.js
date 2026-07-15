import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { MARTENWEAVE_BIN, REPOS_DIR } from "./e2e/fixtures/repo.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SHARED_REPO = path.join(__dirname, "e2e", ".repos", "playwright-shared");

// Fixed local mutation token shared between the backend server and the browser
// context so that write operations can be exercised end-to-end.
process.env.MARTENWEAVE_MUTATION_TOKEN = "e2e-test-token";
const mutationToken = process.env.MARTENWEAVE_MUTATION_TOKEN;

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.js",
  baseURL: "http://127.0.0.1:5173",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    extraHTTPHeaders: {
      "X-Martenweave-Token": mutationToken,
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `"${MARTENWEAVE_BIN}" serve --repo "${SHARED_REPO}" --port 8000 --host 127.0.0.1 --mutation-token ${mutationToken}`,
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: "npm run dev -- --port 5173 --host 127.0.0.1",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
  ],
});

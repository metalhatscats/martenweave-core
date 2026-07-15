/**
 * Global setup for Playwright end-to-end tests.
 *
 * Creates a single isolated temporary repository that the shared backend server
 * and all tests use. The path is exposed through `process.env` so that the
 * Playwright config and test workers can locate it without each creating their
 * own copy.
 */

import path from "node:path";
import { fileURLToPath } from "node:url";
import { createTempRepo, removeTempRepo, REPOS_DIR } from "./fixtures/repo.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SHARED_REPO = path.join(__dirname, ".repos", "playwright-shared");

export default async function globalSetup() {
  const repoPath = await createTempRepo(SHARED_REPO);
  process.env.MARTENWEAVE_E2E_REPO = repoPath;

  return async () => {
    // Global teardown: remove the isolated repository.
    await removeTempRepo(repoPath);
  };
}

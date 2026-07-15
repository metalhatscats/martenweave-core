/**
 * Repository fixture helpers for connected end-to-end tests.
 *
 * These helpers create isolated temporary copies of the example customer_bp_model
 * repository, build the disposable SQLite index, and expose paths that the
 * Playwright config and tests can share.
 */

import { execSync, spawnSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync } from "node:fs";
import { cp, mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** Absolute path to the project root (two levels above frontend/e2e/fixtures). */
export const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");

/** Absolute path to the Python virtual environment's `martenweave` executable. */
export const MARTENWEAVE_BIN = path.join(
  PROJECT_ROOT,
  ".venv",
  "bin",
  "martenweave"
);

/** Base directory where isolated test repositories are created. */
export const REPOS_DIR = path.join(__dirname, "..", ".repos");

/** Example repository used as the template for temp workspaces. */
export const EXAMPLE_REPO = path.join(
  PROJECT_ROOT,
  "examples",
  "customer_bp_model"
);

/**
 * Return an environment object that points child processes at the project venv.
 */
function venvEnv() {
  const venvBin = path.dirname(MARTENWEAVE_BIN);
  return {
    ...process.env,
    PATH: `${venvBin}${path.delimiter}${process.env.PATH || ""}`,
  };
}

/**
 * Run a `martenweave` CLI command against a repository.
 *
 * @param {string[]} args
 * @param {object} [options]
 * @param {string} [options.cwd]
 * @param {boolean} [options.throwOnError]
 */
export function runMartenweave(args, { cwd, throwOnError = true } = {}) {
  const result = spawnSync(MARTENWEAVE_BIN, args, {
    cwd: cwd || PROJECT_ROOT,
    env: venvEnv(),
    encoding: "utf-8",
    timeout: 120_000,
  });

  if (throwOnError && result.status !== 0) {
    const stdout = result.stdout || "";
    const stderr = result.stderr || "";
    throw new Error(
      `martenweave ${args.join(" ")} failed (exit ${result.status}):\n${stdout}\n${stderr}`
    );
  }

  return result;
}

/**
 * Create a fresh temporary repository by copying the example customer_bp_model
 * repository and building its disposable index.
 *
 * @param {string} [targetPath] Optional absolute path to use. If omitted, a
 *   random directory under `e2e/.repos/` is created.
 * @returns {Promise<string>} Absolute path to the created repository.
 */
export async function createTempRepo(targetPath) {
  if (!existsSync(EXAMPLE_REPO)) {
    throw new Error(`Example repository not found: ${EXAMPLE_REPO}`);
  }

  await mkdir(REPOS_DIR, { recursive: true });

  const repoPath = targetPath || path.join(REPOS_DIR, randomUUID());

  // Remove any previous copy at the target path so the repository is fresh.
  await rm(repoPath, { recursive: true, force: true });
  await mkdir(repoPath, { recursive: true });
  await cp(EXAMPLE_REPO, repoPath, { recursive: true });

  const buildResult = spawnSync(
    MARTENWEAVE_BIN,
    ["build-index", "--repo", repoPath],
    {
      cwd: PROJECT_ROOT,
      env: venvEnv(),
      encoding: "utf-8",
      timeout: 120_000,
    }
  );

  if (buildResult.status !== 0) {
    await rm(repoPath, { recursive: true, force: true });
    throw new Error(
      `martenweave build-index failed for ${repoPath}:\n${buildResult.stdout}\n${buildResult.stderr}`
    );
  }

  return repoPath;
}

/**
 * Remove a previously created temporary repository.
 *
 * @param {string} repoPath
 */
export async function removeTempRepo(repoPath) {
  await rm(repoPath, { recursive: true, force: true });
}

/**
 * Rebuild the disposable index for a temporary repository.
 *
 * @param {string} repoPath
 */
export function rebuildIndex(repoPath) {
  runMartenweave(["build-index", "--repo", repoPath]);
}

/**
 * Write an assessment manifest and one finding into a temp repo so the live
 * findings view has reviewable evidence.
 *
 * @param {string} repoPath
 * @param {string} assessmentDirName
 * @param {object} finding
 */
export async function seedFinding(repoPath, assessmentDirName, finding) {
  const generatedRoot = path.join(repoPath, "generated");
  const assessmentDir = path.join(generatedRoot, assessmentDirName);
  await mkdir(assessmentDir, { recursive: true });

  const manifest = {
    run_id: assessmentDirName,
    created_at: new Date().toISOString(),
    assessment_type: "model_validation",
  };

  const findings = {
    findings: [finding],
  };

  await writeFile(
    path.join(assessmentDir, "manifest.json"),
    JSON.stringify(manifest, null, 2)
  );
  await writeFile(
    path.join(assessmentDir, "findings.json"),
    JSON.stringify(findings, null, 2)
  );
}

/**
 * Ensure the fixture directories exist. Called automatically by helpers.
 */
export function ensureFixtureDirs() {
  mkdirSync(REPOS_DIR, { recursive: true });
}

ensureFixtureDirs();

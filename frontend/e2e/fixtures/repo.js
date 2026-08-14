/**
 * Repository fixture helpers for connected end-to-end tests.
 *
 * These helpers create isolated temporary copies of the example customer_bp_model
 * repository, build the disposable SQLite index, and expose paths that the
 * Playwright config and tests can share.
 */

import { execSync, spawnSync } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
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

/**
 * Create a workspace with the real `martenweave start` command (blocked state).
 *
 * @param {string} targetPath Absolute path for the new workspace.
 * @param {string} inputCsv Absolute path to the input dataset.
 * @returns {string} The workspace path.
 */
export function createStartWorkspace(targetPath, inputCsv) {
  runMartenweave(["start", inputCsv, "--out", targetPath, "--no-open", "--json"]);
  return targetPath;
}

const HEALTHY_MODEL_FILES = {
  "PERSON-OWNER.md": `---
id: PERSON-OWNER
type: Person
status: active
name: Workspace Owner
schema_version: "1.0"
---

# Workspace Owner
`,
  "ATTR-CUSTOMER-GROUP.md": `---
id: ATTR-CUSTOMER-GROUP
type: Attribute
status: active
name: Customer Group
domain: DOMAIN-EXAMPLE
business_owner: PERSON-OWNER
data_steward: PERSON-OWNER
schema_version: "1.0"
---

# Customer Group
`,
  "FEP-SRC-CUSTOMER-GROUP.md": `---
id: FEP-SRC-CUSTOMER-GROUP
type: FieldEndpoint
status: active
name: CUSTOMER_GROUP
attribute: ATTR-CUSTOMER-GROUP
endpoint_type: file_column
business_owner: PERSON-OWNER
data_steward: PERSON-OWNER
schema_version: "1.0"
---

# CUSTOMER_GROUP source column
`,
};

/**
 * Create a workspace whose persisted start run has a healthy ("ready") verdict.
 *
 * The readiness report is produced by the real deterministic workflow against a
 * minimal warning-free model; the start manifest mirrors the exact schema the
 * `martenweave start` command writes, with counts taken from that report.
 *
 * @param {string} targetPath Absolute path for the new workspace.
 * @returns {string} The workspace path.
 */
export async function createHealthyStartWorkspace(targetPath) {
  await rm(targetPath, { recursive: true, force: true });
  runMartenweave(["init", targetPath]);

  for (const [name, content] of Object.entries(HEALTHY_MODEL_FILES)) {
    await writeFile(path.join(targetPath, "model", name), content);
  }
  const inputCsv = path.join(targetPath, "input.csv");
  await writeFile(inputCsv, "CUSTOMER_GROUP\nA\n");

  const readinessDir = path.join(targetPath, "generated", "readiness");
  runMartenweave([
    "run", "dataset-readiness", inputCsv,
    "--repo", targetPath,
    "--out", readinessDir,
    "--check-model",
  ]);

  const report = JSON.parse(
    readFileSync(path.join(readinessDir, "readiness.json"), "utf-8")
  );
  if (report.verdict !== "ready") {
    throw new Error(`Healthy fixture expected a ready verdict, got: ${report.verdict}`);
  }

  const profileDir = path.join(targetPath, "generated", "dataset_profiles");
  await mkdir(profileDir, { recursive: true });
  await writeFile(
    path.join(profileDir, "input.json"),
    JSON.stringify(report.dataset_profile, null, 2)
  );

  const totalFindings = report.dataset_gaps.length + report.model_gaps.length;
  const manifest = {
    schema_version: "1.0",
    created_at: new Date().toISOString(),
    input: {
      path: inputCsv,
      format: "csv",
      sha256: createHash("sha256").update(readFileSync(inputCsv)).digest("hex"),
    },
    workspace: targetPath,
    readiness: {
      verdict: report.verdict,
      total_findings: totalFindings,
      dataset_gaps: report.dataset_gaps.length,
      model_gaps: report.model_gaps.length,
      validation_errors: report.validation.error_count,
      validation_warnings: report.validation.warning_count,
    },
    checks: {
      unmapped_columns: "evaluated",
      ownership_gaps: "evaluated through canonical validation",
      invalid_values: "not_assessed_without_governed_value_lists",
      transformation_risks: "represented by deterministic dataset/model gaps",
    },
    generated_outputs: {
      profile: "generated/dataset_profiles/input.json",
      readiness_json: "generated/readiness/readiness.json",
      readiness_markdown: "generated/readiness/readiness.md",
      draft_proposal: null,
    },
    canonical_model: {
      created_workspace_seed_only: true,
      input_never_overwrote_canonical_files: true,
      draft_proposal_requires_validation_and_human_review: true,
    },
    ai: {
      configured: false,
      message: "No AI provider is required for profiling, readiness, or draft inference.",
    },
    workbench: {
      url: "http://127.0.0.1:8000",
      command: `martenweave workbench --repo ${targetPath}`,
    },
  };
  await writeFile(
    path.join(targetPath, "generated", "start_manifest.json"),
    JSON.stringify(manifest, null, 2)
  );
  return targetPath;
}

/**
 * Create an empty (no-input) workspace: initialized and indexed, but with no
 * persisted start run.
 *
 * @param {string} targetPath Absolute path for the new workspace.
 * @returns {string} The workspace path.
 */
export async function createEmptyWorkspace(targetPath) {
  await rm(targetPath, { recursive: true, force: true });
  runMartenweave(["init", targetPath]);
  runMartenweave(["build-index", "--repo", targetPath]);
  return targetPath;
}

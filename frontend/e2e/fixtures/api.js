/**
 * Direct API helpers for end-to-end tests.
 *
 * These use Node's native fetch to talk to the local Martenweave API that
 * Playwright starts. They are useful for verifying backend state and for
 * mutations that would otherwise require the UI to send the mutation token.
 */

const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * @returns {string|undefined}
 */
function mutationToken() {
  return process.env.MARTENWEAVE_MUTATION_TOKEN;
}

/**
 * Build request headers, including the mutation token when one is configured.
 */
function headers() {
  const token = mutationToken();
  if (!token) return { "Content-Type": "application/json" };
  return {
    "Content-Type": "application/json",
    "X-Martenweave-Token": token,
  };
}

/**
 * Perform a JSON request against the local API.
 *
 * @param {string} method
 * @param {string} pathname
 * @param {object} [body]
 * @param {Record<string, string>} [query]
 * @returns {Promise<any>}
 */
export async function apiRequest(method, pathname, body, query) {
  const url = new URL(pathname, API_BASE_URL);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }

  const options = {
    method,
    headers: headers(),
  };

  if (body !== undefined) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url.toString(), options);
  const text = await response.text();

  if (!response.ok) {
    throw new Error(
      `${method} ${pathname} failed (${response.status}): ${text}`
    );
  }

  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/**
 * GET shortcut.
 */
export function apiGet(pathname, query) {
  return apiRequest("GET", pathname, undefined, query);
}

/**
 * POST shortcut.
 */
export function apiPost(pathname, body, query) {
  return apiRequest("POST", pathname, body, query);
}

/**
 * Verify that the API health endpoint is healthy and return the JSON payload.
 */
export function apiHealth() {
  return apiGet("/health");
}

/**
 * Upload a file to the import profile endpoint.
 *
 * @param {Blob} file
 * @param {string} [datasetId]
 */
export async function apiImportProfile(file, datasetId) {
  const url = new URL("/api/v1/imports/profile", API_BASE_URL);
  if (datasetId) url.searchParams.set("dataset_id", datasetId);

  const formData = new FormData();
  formData.append("file", file);

  const token = mutationToken();
  const response = await fetch(url.toString(), {
    method: "POST",
    headers: token ? { "X-Martenweave-Token": token } : undefined,
    body: formData,
  });

  const text = await response.text();
  if (!response.ok) {
    throw new Error(`Import profile failed (${response.status}): ${text}`);
  }
  return JSON.parse(text);
}

/**
 * Download a report artifact and return the response object.
 *
 * @param {string} artifactId
 */
export async function apiDownloadReport(artifactId) {
  const pathname = `/api/v1/reports/${artifactId}`;
  const url = new URL(pathname, API_BASE_URL);
  const response = await fetch(url.toString());
  return { status: response.status, headers: response.headers };
}

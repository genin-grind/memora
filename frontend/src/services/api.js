const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json();

  if (!response.ok) {
    const message = data?.message || "Request failed";
    throw new Error(message);
  }

  return data;
}

export function loginWithEmail(email) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function fetchOrgSummary() {
  return request("/api/org/summary");
}

export function fetchExplorerWorkspace() {
  return request("/api/explorer/workspace");
}

export function fetchSyncStatus() {
  return request("/api/sync/status");
}

export function runSyncNow() {
  return request("/api/sync/run", {
    method: "POST",
  });
}

export function uploadManualDocument(payload) {
  return request("/api/sync/upload", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function queryMemora(question) {
  return request("/api/memora/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

/**
 * API client for Pivot.AI backend.
 * All calls go through Next.js rewrite proxy → FastAPI at localhost:8000
 */

const BASE = "/api/v1";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// Profile
export const getProfile = (userId) => request(`/profile/${userId}`);
export const upsertProfile = (data) =>
  request("/profile", { method: "POST", body: JSON.stringify(data) });

// Goals
export const getGoals = (userId) => request(`/goals/${userId}`);
export const upsertGoals = (data) =>
  request("/goals", { method: "POST", body: JSON.stringify(data) });

// Jobs
export const getJobs = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/jobs${qs ? `?${qs}` : ""}`);
};
export const triggerIngestion = () =>
  request("/jobs/ingest", { method: "POST" });

// Companies
export const getCompanies = () => request("/companies");

// Discovery
export const triggerDiscovery = () =>
  request("/discovery/run", { method: "POST" });

// Pipeline & Scoring
export const getPipeline = (userId) => request(`/pipeline/${userId}`);
export const updatePipelineStatus = (userId, jobId, status) =>
  request(`/pipeline/${userId}/${jobId}/status`, {
    method: "PUT",
    body: JSON.stringify({ status }),
  });
export const triggerScoring = (userId) =>
  request(`/pipeline/${userId}/score`, { method: "POST" });

// Admin Settings & Operations
export const getAdminSettings = () => request("/admin/settings");
export const updateAdminSettings = (data) =>
  request("/admin/settings", { method: "PUT", body: JSON.stringify(data) });
export const adminRunDiscovery = () =>
  request("/admin/discovery/run", { method: "POST" });
export const adminRunIngestion = () =>
  request("/admin/ingestion/run", { method: "POST" });

// Stats (aggregated from existing endpoints)
export async function getStats() {
  const [jobs, companies] = await Promise.all([
    getJobs({ limit: 1 }).catch(() => []),
    getCompanies().catch(() => []),
  ]);
  // Fetch total job count with a large limit
  const allJobs = await getJobs({ limit: 500 }).catch(() => []);
  return {
    jobCount: allJobs.length,
    companyCount: companies.length,
  };
}

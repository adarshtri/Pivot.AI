/**
 * API client for Pivot.AI backend.
 * All calls go through Next.js rewrite proxy → FastAPI at localhost:8000
 */

const BASE = "/api/v1";

async function request(path, options = {}) {
  const { token, ...fetchOptions } = options;
  const headers = {
    "Content-Type": "application/json",
    ...fetchOptions.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Profile
export const getProfile = (token) => request("/profile", { token });
export const upsertProfile = (token, data) =>
  request("/profile", { method: "POST", body: JSON.stringify(data), token });
export const tailorResume = (token, jobId) => 
  request(`/profile/resume/tailor/${jobId}`, { method: "POST", token });
export const getTailoredResume = (token, jobId) => 
  request(`/profile/resume/tailored/${jobId}`, { token });

// Goals
export const getGoals = (token) => request("/goals", { token });
export const upsertGoals = (token, data) =>
  request("/goals", { method: "POST", body: JSON.stringify(data), token });

// Jobs
export const getJobs = (token, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/jobs${qs ? `?${qs}` : ""}`, { token });
};
export const triggerIngestion = (token) =>
  request("/jobs/ingest", { method: "POST", token });

// Companies
export const getCompanies = (token) => request("/companies", { token });

// Discovery
export const triggerDiscovery = (token) =>
  request("/discovery/run", { method: "POST", token });

// Pipeline & Scoring
export const getPipeline = (token, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/pipeline${qs ? `?${qs}` : ""}`, { token });
};

export const updatePipelineStatus = (token, jobId, status, reason = null) =>
  request(`/pipeline/${jobId}/status`, {
    method: "PUT",
    body: JSON.stringify({ status, reason }),
    token,
  });

export const triggerScoring = (token) =>
  request("/pipeline/score", { method: "POST", token });
export const triggerInference = (token) =>
  request("/pipeline/infer", { method: "POST", token });

// Admin Settings & Operations
export const getAdminSettings = (token) => request("/admin/settings", { token });
export const updateAdminSettings = (token, data) =>
  request("/admin/settings", { method: "PUT", body: JSON.stringify(data), token });
export const adminRunDiscovery = (token) =>
  request("/admin/discovery/run", { method: "POST", token });
export const adminRunIngestion = (token) =>
  request("/admin/ingestion/run", { method: "POST", token });
export const adminRunCompanyEnrichment = (token, force = false) =>
  request(`/admin/discovery/companies/enrich?force=${force}`, { method: "POST", token });
export const adminRunCompanyScoring = (token) =>
  request("/admin/scoring/companies/run", { method: "POST", token });
export const syncTelegramWebhooks = (token) =>
  request("/admin/telegram/sync-webhooks", { method: "POST", token });
export const adminTestTelegramAlert = (token, targetUserId) =>
  request(`/admin/telegram/test-alert?target_user_id=${targetUserId}`, { method: "POST", token });


// Insights Engine
export const getInsights = (token) => request("/insights", { token });
export const triggerInsights = (token) => request("/insights/run", { method: "POST", token });
export const deleteInsight = (token, insightId) => request(`/insights/${insightId}`, { method: "DELETE", token });



// Learning Hub
export const getLearningHub = (token) => request("/learning", { token });
export const trackSkill = (token, skillName, insightId = null) => 
  request(`/learning?skill_name=${encodeURIComponent(skillName)}${insightId ? `&origin_insight_id=${insightId}` : ""}`, { method: "POST", token });
export const updateLearningStatus = (token, itemId, status) => 
  request(`/learning/${itemId}?status=${status}`, { method: "PATCH", token });
export const promoteSkill = (token, itemId) => 
  request(`/learning/${itemId}/promote`, { method: "POST", token });
export const deleteLearningItem = (token, itemId) => 
  request(`/learning/${itemId}`, { method: "DELETE", token });


// Stats (aggregated from existing endpoints)
export async function getStats(token) {
  const [pipeline, companies] = await Promise.all([
    getPipeline(token, { limit: 1 }).catch(() => ({ total: 0 })),
    getCompanies(token).catch(() => []),
  ]);
  
  return {
    jobCount: pipeline.total || 0,
    companyCount: companies.length,
  };
}

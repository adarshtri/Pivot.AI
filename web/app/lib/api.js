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
  if (res.status === 204) return null;
  return res.json();
}

// Profile
export const getProfile = (userId) => request(`/profile/${userId}`);
export const upsertProfile = (data) =>
  request("/profile", { method: "POST", body: JSON.stringify(data) });
export const tailorResume = (userId, jobId) => 
  request(`/profile/${userId}/resume/tailor/${jobId}`, { method: "POST" });
export const getTailoredResume = (userId, jobId) => 
  request(`/profile/${userId}/resume/tailored/${jobId}`);

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
export const getCompanies = (userId = "user1") => request(`/companies?user_id=${userId}`);

// Discovery
export const triggerDiscovery = () =>
  request("/discovery/run", { method: "POST" });

// Pipeline & Scoring
export const getPipeline = (userId, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/pipeline/${userId}${qs ? `?${qs}` : ""}`);
};

export const updatePipelineStatus = (userId, jobId, status, reason = null) =>
  request(`/pipeline/${userId}/${jobId}/status`, {
    method: "PUT",
    body: JSON.stringify({ status, reason }),
  });

export const triggerScoring = (userId) =>
  request(`/pipeline/${userId}/score`, { method: "POST" });
export const triggerInference = (userId) =>
  request(`/pipeline/${userId}/infer`, { method: "POST" });

// Admin Settings & Operations
export const getAdminSettings = () => request("/admin/settings");
export const updateAdminSettings = (data) =>
  request("/admin/settings", { method: "PUT", body: JSON.stringify(data) });
export const adminRunDiscovery = () =>
  request("/admin/discovery/run", { method: "POST" });
export const adminRunIngestion = () =>
  request("/admin/ingestion/run", { method: "POST" });
export const adminRunCompanyEnrichment = (force = false) =>
  request(`/admin/discovery/companies/enrich?force=${force}`, { method: "POST" });
export const adminRunCompanyScoring = () =>
  request("/admin/scoring/companies/run", { method: "POST" });
export const syncTelegramWebhooks = () =>
  request("/admin/telegram/sync-webhooks", { method: "POST" });
export const adminTestTelegramAlert = (targetUserId) =>
  request(`/admin/telegram/test-alert?target_user_id=${targetUserId}`, { method: "POST" });


// Insights Engine
export const getInsights = (userId) => request(`/insights?user_id=${userId}`);
export const triggerInsights = (userId) => request(`/insights/run?user_id=${userId}`, { method: "POST" });
export const deleteInsight = (userId, insightId) => request(`/insights/${insightId}?user_id=${userId}`, { method: "DELETE" });



// Learning Hub
export const getLearningHub = (userId) => request(`/learning?user_id=${userId}`);
export const trackSkill = (userId, skillName, insightId = null) => 
  request(`/learning?user_id=${userId}&skill_name=${encodeURIComponent(skillName)}${insightId ? `&origin_insight_id=${insightId}` : ""}`, { method: "POST" });
export const updateLearningStatus = (userId, itemId, status) => 
  request(`/learning/${itemId}?user_id=${userId}&status=${status}`, { method: "PATCH" });
export const promoteSkill = (userId, itemId) => 
  request(`/learning/${itemId}/promote?user_id=${userId}`, { method: "POST" });
export const deleteLearningItem = (userId, itemId) => 
  request(`/learning/${itemId}?user_id=${userId}`, { method: "DELETE" });


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

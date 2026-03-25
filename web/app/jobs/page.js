"use client";
import { useEffect, useState } from "react";
import { getPipeline, updatePipelineStatus } from "../lib/api";
import { Spinner, EmptyState, useToast } from "../components/ui";

export default function JobsPage() {
  const [pipeline, setPipeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("recommended");
  const { showToast, ToastComponent } = useToast();

  const load = async () => {
    try {
      const data = await getPipeline("user1");
      setPipeline(data);
    } catch {
      setPipeline([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleStatusUpdate = async (jobId, status) => {
    try {
      await updatePipelineStatus("user1", jobId, status);
      // Optimistically update the local state to shift it across tabs instantly
      setPipeline((prev) =>
        prev.map((item) =>
          item.job_id === jobId ? { ...item, pipeline_status: status } : item
        )
      );
      showToast(`Moved to ${status}`);
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch {
      return "—";
    }
  };

  const tabs = [
    { id: "recommended", label: "Recommended" },
    { id: "saved", label: "Saved" },
    { id: "applied", label: "Applied" },
    { id: "ignored", label: "Ignored" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-[#8a8ca0]">
        <Spinner /> Loading your AI Pipeline…
      </div>
    );
  }

  const filteredJobs = pipeline.filter((j) => j.pipeline_status === activeTab);

  return (
    <div>
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 pb-4 border-b border-[#2a2b40]">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">AI Pipeline</h1>
          <p className="text-[#8a8ca0]">
            Review tailored job matches based on your goals and semantic profile.
          </p>
        </div>
        
        <div className="flex gap-2 mt-4 md:mt-0 bg-[#161726] p-1 rounded-lg border border-[#2a2b40]">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === t.id
                  ? "bg-[var(--accent)] text-white"
                  : "text-[#8a8ca0] hover:text-[#d0d3e2]"
              }`}
            >
              {t.label} 
              <span className="ml-2 opacity-60 text-xs">
                {pipeline.filter((j) => j.pipeline_status === t.id).length}
              </span>
            </button>
          ))}
        </div>
      </div>

      {filteredJobs.length === 0 ? (
        <EmptyState
          icon="✨"
          message={`No jobs in ${activeTab}. Run the AI Scoring Engine from the Admin pane to find new matches!`}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredJobs.map((job) => (
            <div key={job.job_id} className="glass-card flex flex-col hover:-translate-y-0.5 transition-transform">
              
              {/* Header: Score & Meta */}
              <div className="p-5 pb-3 border-b border-[#2a2b40]">
                <div className="flex justify-between items-start mb-2">
                  <div className="font-bold text-lg leading-tight line-clamp-2 pr-2">{job.role}</div>
                  <div className="flex flex-col items-end shrink-0">
                    <span className="text-xl font-black text-[#56d364]">
                      {job.pipeline_score?.toFixed(0)}
                    </span>
                    <span className="text-[0.65rem] uppercase tracking-wider text-[#8a8ca0] font-bold">Match</span>
                  </div>
                </div>
                <div className="text-sm text-[#8a8ca0] font-medium mb-2">{job.company}</div>
                <div className="flex gap-4 text-xs text-[#5a5c72]">
                  {job.location && <span>📍 {job.location}</span>}
                  <span>📅 {formatDate(job.created_at)}</span>
                </div>
              </div>

              {/* Rationale & Description Snippet */}
              <div className="p-5 flex-1 text-sm text-[#d0d3e2]">
                {job.pipeline_rationale && (
                  <div className="mb-3 px-3 py-1.5 bg-[#161726] rounded-md text-xs text-[#8a8ca0] border-l-2 border-[#56d364]">
                    🧠 {job.pipeline_rationale}
                  </div>
                )}
                <div className="line-clamp-4 leading-relaxed opacity-80">
                  {job.description}
                </div>
              </div>

              {/* Actions Footer */}
              <div className="p-3 bg-[#161726] border-t border-[#2a2b40] rounded-b-xl flex justify-between items-center gap-2">
                <div className="flex gap-2">
                  {activeTab !== "ignored" && (
                    <button 
                      onClick={() => handleStatusUpdate(job.job_id, "ignored")}
                      className="px-3 py-1.5 text-xs font-semibold text-[#8a8ca0] hover:text-white hover:bg-[#2a2b40] rounded-md transition-colors"
                    >
                      Ignore
                    </button>
                  )}
                  {activeTab !== "saved" && activeTab !== "applied" && (
                    <button 
                      onClick={() => handleStatusUpdate(job.job_id, "saved")}
                      className="px-3 py-1.5 text-xs font-semibold text-[#56d364] hover:bg-[#56d364]/10 rounded-md transition-colors"
                    >
                      Save
                    </button>
                  )}
                </div>
                
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => {
                    if (activeTab !== "applied") {
                      handleStatusUpdate(job.job_id, "applied");
                    }
                  }}
                  className="px-4 py-1.5 text-xs font-bold bg-[var(--accent)] text-white shadow-lg shadow-[var(--accent)]/20 hover:shadow-[var(--accent)]/40 hover:-translate-y-0.5 transition-all rounded-md"
                >
                  Apply →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {ToastComponent}
    </div>
  );
}

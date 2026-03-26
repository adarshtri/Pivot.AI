"use client";
import { useEffect, useState } from "react";
import { getPipeline, updatePipelineStatus } from "../lib/api";
import { Spinner, EmptyState, useToast } from "../components/ui";

export default function JobsPage() {
  const [data, setData] = useState({ items: [], total: 0, page: 1, total_pages: 0, counts: {} });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("recommended");
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(21); // Using 21 for a 3-column grid
  const { showToast, ToastComponent } = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const res = await getPipeline("user1", { page, limit, status: activeTab });
      setData(res);
    } catch (err) {
      showToast(err.message, "error");
      setData({ items: [], total: 0, page: 1, total_pages: 0, counts: {} });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [activeTab, page, limit]);

  // Reset to page 1 when tab changes
  useEffect(() => {
    setPage(1);
  }, [activeTab]);

  const handleStatusUpdate = async (jobId, status) => {
    let reason = null;
    if (status === "ignored") {
      reason = window.prompt("Why are you ignoring this job? (Optional)");
      if (reason === null) return; // User cancelled
      if (reason.trim() === "") reason = "Following system recommendation.";
    }


    try {
      await updatePipelineStatus("user1", jobId, status, reason);
      // Refresh data to move the item out of the current view
      load();
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

  const cleanDescription = (htmlStr) => {
    if (!htmlStr) return "";
    let decoded = htmlStr
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&amp;/g, '&')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ');
    return decoded.replace(/<[^>]*>?/gm, '').trim();
  };

  const tabs = [
    { id: "recommended", label: "Recommended" },
    { id: "saved", label: "Saved" },
    { id: "applied", label: "Applied" },
    { id: "ignored", label: "Ignored" },
  ];

  const Pagination = () => {
    if (data.total_pages <= 1) return null;

    return (
      <div className="mt-10 flex flex-col md:flex-row items-center justify-between gap-4 py-6 border-t border-[#2a2b40]">
        <div className="text-sm text-[#8a8ca0]">
          Showing <span className="text-white font-medium">{(data.page - 1) * data.limit + 1}-{Math.min(data.page * data.limit, data.total)}</span> of <span className="text-white font-medium">{data.total}</span> matches
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={data.page === 1}
            className="p-2 rounded-md border border-[#2a2b40] text-[#8a8ca0] hover:text-white hover:bg-[#2a2b40] disabled:opacity-30 disabled:hover:bg-transparent transition-all"
          >
             ← Previous
          </button>
          
          <div className="flex items-center gap-1 mx-2">
            {[...Array(data.total_pages)].map((_, i) => {
              const p = i + 1;
              // Show limited page numbers if too many
              if (data.total_pages > 7) {
                if (p !== 1 && p !== data.total_pages && (p < data.page - 1 || p > data.page + 1)) {
                  if (p === 2 || p === data.total_pages - 1) return <span key={p} className="px-1 text-[#5a5c72]">...</span>;
                  return null;
                }
              }

              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-8 h-8 flex items-center justify-center rounded-md text-sm font-bold transition-all ${
                    data.page === p
                      ? "bg-[var(--accent)] text-white shadow-lg shadow-[var(--accent)]/20"
                      : "text-[#8a8ca0] hover:text-white hover:bg-[#2a2b40]"
                  }`}
                >
                  {p}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
            disabled={data.page === data.total_pages}
            className="p-2 rounded-md border border-[#2a2b40] text-[#8a8ca0] hover:text-white hover:bg-[#2a2b40] disabled:opacity-30 disabled:hover:bg-transparent transition-all"
          >
            Next →
          </button>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-[#5a5c72] font-bold uppercase tracking-wider">Show:</span>
          <select 
            value={limit} 
            onChange={(e) => { setLimit(Number(e.target.value)); setPage(1); }}
            className="bg-[#161726] border border-[#2a2b40] text-[#d0d3e2] text-xs font-bold rounded-md px-2 py-1 outline-none hover:border-[var(--accent)] transition-colors cursor-pointer"
          >
            <option value={9}>9</option>
            <option value={21}>21</option>
            <option value={51}>51</option>
            <option value={99}>99</option>
          </select>
        </div>
      </div>
    );
  };

  return (
    <div className="pb-10">
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
                {data.counts?.[t.id] || 0}
              </span>
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-64 gap-4 text-[#8a8ca0]">
          <Spinner /> 
          <span className="text-sm font-medium animate-pulse">Fetching page {page}...</span>
        </div>
      ) : data.items.length === 0 ? (
        <EmptyState
          icon="✨"
          message={`No jobs in ${activeTab}. Run the AI Scoring Engine from the Admin pane to find new matches!`}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {data.items.map((job) => (
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

                <div className="p-5 flex-1 text-sm text-[#d0d3e2]">
                  {job.pipeline_llm_verdict && (
                    <div className="mb-3 flex items-center">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold border ${
                          job.pipeline_llm_verdict === "Strong Match"
                            ? "bg-[#56d364]/10 text-[#56d364] border-[#56d364]/20"
                            : job.pipeline_llm_verdict === "Weak Match"
                            ? "bg-[#f85149]/10 text-[#f85149] border-[#f85149]/20"
                            : "bg-[#d29922]/10 text-[#d29922] border-[#d29922]/20"
                        }`}
                      >
                        ✨ {job.pipeline_llm_verdict}
                      </span>
                    </div>
                  )}
                  {job.pipeline_rationale && (
                    <div className={`mb-3 px-3 py-2 bg-[#161726] rounded-md text-xs leading-relaxed text-[#8a8ca0] border-l-2 ${
                      job.pipeline_llm_verdict === "Strong Match"
                        ? "border-[#56d364]"
                        : job.pipeline_llm_verdict === "Weak Match"
                        ? "border-[#f85149]"
                        : job.pipeline_llm_verdict ? "border-[#d29922]" : "border-[#5a5c72]"
                    }`}>
                      🧠 {job.pipeline_rationale}
                    </div>
                  )}

                  {activeTab === "ignored" && job.pipeline_ignore_reason && (
                    <div className="mb-4 px-3 py-2 bg-[#f85149]/5 border border-[#f85149]/10 rounded-md text-xs italic text-[#8a8ca0]">
                      <span className="text-[#f85149] font-bold not-italic mr-1">Ignored because:</span> {job.pipeline_ignore_reason}
                    </div>
                  )}

                  
                  {job.pipeline_goal_scores && Object.keys(job.pipeline_goal_scores).length > 0 && (
                    <div className="mb-4 space-y-1.5 p-3 rounded-lg bg-[rgba(124,92,252,0.05)] border border-[rgba(124,92,252,0.15)]">
                      <div className="text-[0.65rem] uppercase tracking-wider text-[var(--accent)] font-bold mb-2">Priority Rubric Breakdown</div>
                      {(() => {
                        const categoryOrder = { "Location": 1, "Target Role": 2, "Domain": 3, "Career Direction": 4 };
                        
                        const goalsArray = Object.entries(job.pipeline_goal_scores).map(([text, data]) => ({
                          text,
                          score: typeof data === 'number' ? data : data.score,
                          weight: typeof data === 'number' ? 1.0 : data.weight,
                          category: typeof data === 'number' ? "Unknown" : (data.category || "Unknown")
                        }));

                        goalsArray.sort((a, b) => {
                          const catA = categoryOrder[a.category] || 99;
                          const catB = categoryOrder[b.category] || 99;
                          if (catA !== catB) return catA - catB;
                          if (a.weight !== b.weight) return b.weight - a.weight;
                          return a.text.localeCompare(b.text);
                        });

                        return goalsArray.map(g => {
                          let weightBadge = null;
                          if (g.weight >= 10) weightBadge = <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.65rem] font-bold bg-red-400/10 text-red-400 border border-red-400/20 mr-2 shrink-0">10x</span>;
                          else if (g.weight >= 5) weightBadge = <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.65rem] font-bold bg-amber-400/10 text-amber-400 border border-amber-400/20 mr-2 shrink-0">5x</span>;
                          else weightBadge = <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.65rem] font-bold bg-slate-400/10 text-slate-400 border border-slate-400/20 mr-2 shrink-0">1x</span>;

                          return (
                            <div key={g.text} className="flex justify-between items-center text-xs">
                              <div className="flex items-center truncate pr-3 opacity-90">
                                {weightBadge}
                                <span className="truncate">{g.text}</span>
                              </div>
                              <span className={`font-mono font-bold shrink-0 ${g.score > 75 ? 'text-[#56d364]' : g.score < 40 ? 'text-[#f85149]' : 'text-[#d0d3e2]'}`}>
                                {g.score.toFixed(0)}
                              </span>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  )}
                  
                  <div className="line-clamp-4 leading-relaxed opacity-80 mt-2">
                    {cleanDescription(job.description)}
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
                    {activeTab !== "saved" && activeTab === "recommended" && (
                      <button 
                        onClick={() => handleStatusUpdate(job.job_id, "saved")}
                        className="px-3 py-1.5 text-xs font-semibold text-[#56d364] hover:bg-[#56d364]/10 rounded-md transition-colors"
                      >
                        Save
                      </button>
                    )}
                    {activeTab !== "applied" && (
                      <button 
                        onClick={() => handleStatusUpdate(job.job_id, "applied")}
                        className="px-3 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--accent)]/10 rounded-md transition-colors"
                      >
                        Mark Applied
                      </button>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 text-xs font-medium text-[#8a8ca0] hover:text-[#d0d3e2] bg-[#2a2b40]/50 hover:bg-[#2a2b40] rounded-md transition-all"
                    >
                      View Posting
                    </a>
                    
                    {activeTab !== "applied" && (
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => handleStatusUpdate(job.job_id, "applied")}
                        className="px-4 py-1.5 text-xs font-bold bg-[var(--accent)] text-white shadow-lg shadow-[var(--accent)]/20 hover:shadow-[var(--accent)]/40 hover:-translate-y-0.5 transition-all rounded-md"
                      >
                        Apply Now →
                      </a>
                    )}
                  </div>
                </div>

              </div>
            ))}
          </div>
          <Pagination />
        </>
      )}

      {ToastComponent}
    </div>
  );
}


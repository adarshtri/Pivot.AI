"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { getCompanies } from "../lib/api";
import { Spinner, EmptyState } from "../components/ui";

export default function CompaniesPage() {
  const { getToken } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getCompanies(token);
      setCompanies(data);
    } catch {
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [getToken]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-[#8a8ca0]">
        <Spinner /> Loading…
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">Companies</h1>
          <p className="text-[#8a8ca0]">
            Discovered from your goals via Brave Search.
          </p>
        </div>
      </div>

      {companies.length === 0 ? (
        <EmptyState
          icon="🏢"
          message="No companies discovered yet. Check your goals and wait for the discovery pipeline."
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {companies.map((c, i) => (
            <div key={i} className={`glass-card p-5 group hover:border-[var(--accent)]/30 transition-all duration-300 flex flex-col relative overflow-hidden
              ${c.user_match_verdict === "Strong Match" ? "ring-1 ring-emerald-500/20 bg-emerald-500/[0.02]" : ""}`}>
              
              {c.user_match_verdict === "Strong Match" && (
                <div className="absolute top-0 right-0 px-2 py-0.5 bg-emerald-500 text-[8px] font-black uppercase tracking-[0.2em] text-[#0d0e1a] rounded-bl-lg z-10">
                  ✨ Top Pick
                </div>
              )}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="font-bold text-lg tracking-tight text-white mb-0.5">{c.name}</div>
                  <div className="flex items-center gap-2 text-[10px] text-[#8a8ca0] font-medium uppercase tracking-widest">
                    <span>{c.domain || "no-domain.com"}</span>
                    {c.stage && <span>• {c.stage}</span>}
                    {c.size && <span>• {c.size} employees</span>}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1.5 min-w-[100px]">
                  {c.user_match_verdict && (
                    <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border shadow-lg
                      ${c.user_match_verdict === "Strong Match" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-emerald-500/5" : 
                        c.user_match_verdict === "Moderate Match" ? "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-amber-500/5" : 
                        "bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-rose-500/5"}`}>
                      {c.user_match_verdict}
                    </div>
                  )}
                  {c.user_match_score !== undefined && c.user_match_score !== null && (
                    <div className="flex items-center gap-2">
                       <span className="text-[10px] font-bold text-[#5a5c72] uppercase tracking-widest">Alignment</span>
                       <span className={`text-sm font-black ${
                         c.user_match_score > 0.75 ? "text-emerald-400" : 
                         c.user_match_score > 0.4 ? "text-amber-400" : "text-rose-400"
                       }`}>
                         {(c.user_match_score * 100).toFixed(0)}%
                       </span>
                    </div>
                  )}
                </div>
              </div>

              {c.description && (
                <p className="text-xs text-[#d0d3e2] mb-4 leading-relaxed line-clamp-2">
                  {c.description}
                </p>
              )}

              <div className="mt-auto">
                <div className="flex items-center justify-between pt-4 border-t border-white/5">
                  <div className="flex items-center gap-3">
                    <Link
                      href={`/jobs?company=${encodeURIComponent(c.name)}`}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-500 hover:bg-emerald-500/20 transition-colors"
                    >
                      {c.open_jobs_count} Open Jobs
                    </Link>
                    <span className="text-[10px] font-bold text-[#5a5c72]">
                      {c.closed_jobs_count} Archived
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-[9px] font-black uppercase tracking-[0.2em] text-[#3a3b4f]">via {c.discovered_via}</span>
                    <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest border
                      ${c.source === "greenhouse" ? "border-emerald-500/20 text-emerald-500/60" : "border-blue-500/20 text-blue-500/60"}`}>
                      {c.source}
                    </span>
                  </div>
                </div>

                {c.user_match_rationale && (
                  <div className="mt-4 p-3 bg-[#0d0e1a] rounded-xl border border-white/5 text-[10px] text-[#8a8ca0] italic leading-relaxed">
                    <span className="text-[#5a5c72] font-black uppercase tracking-widest not-italic mr-2">AI Summary:</span>
                    {c.user_match_rationale}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}

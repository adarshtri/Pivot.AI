"use client";
import { useEffect, useState } from "react";
import { getCompanies } from "../lib/api";
import { Spinner, EmptyState } from "../components/ui";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await getCompanies();
      setCompanies(data);
    } catch {
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

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
        <div className="space-y-3">
          {companies.map((c, i) => (
            <div key={i} className="glass-card p-4 flex items-center justify-between">
              <div>
                <div className="font-semibold text-sm">{c.name}</div>
                <div className="text-xs text-[#8a8ca0]">
                  {c.domain || "—"} {c.stage ? `• ${c.stage}` : ""}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {c.discovered_via && (
                  <span className="text-xs text-[#5a5c72]">via {c.discovered_via}</span>
                )}
                <span
                  className={`inline-flex px-2 py-0.5 rounded-full text-[0.7rem] font-semibold uppercase tracking-wide
                    ${c.source === "greenhouse" ? "badge-greenhouse" : "badge-lever"}`}
                >
                  {c.source}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}

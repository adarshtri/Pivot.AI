"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getProfile, getGoals, getStats } from "./lib/api";

export default function DashboardPage() {
  const [profile, setProfile] = useState(null);
  const [goals, setGoals] = useState(null);
  const [stats, setStats] = useState({ jobCount: 0, companyCount: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [p, g, s] = await Promise.all([
          getProfile("user1").catch(() => null),
          getGoals("user1").catch(() => null),
          getStats(),
        ]);
        setProfile(p);
        setGoals(g);
        setStats(s);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-[#8a8ca0]">
        <div className="w-5 h-5 border-2 border-white/10 border-t-[var(--accent)] rounded-full animate-spin" />
        Loading…
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-1">Dashboard</h1>
        <p className="text-[#8a8ca0]">Your career intelligence overview.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard value={stats.jobCount} label="Jobs Ingested" />
        <StatCard value={stats.companyCount} label="Companies" />
        <StatCard value={profile?.skills?.length || 0} label="Skills" />
        <StatCard value={goals?.target_roles?.length || 0} label="Target Roles" />
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Profile Card */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-semibold">My Career Profile</h2>
            <Link href="/profile" className="text-xs text-[var(--accent)] hover:underline">
              Edit →
            </Link>
          </div>
          {profile ? (
            <div>
              <div className="text-sm text-[#8a8ca0] mb-1">
                {profile.current_role} • {profile.experience_level}
              </div>
              <div className="flex flex-wrap gap-2 mt-3">
                {profile.skills?.map((s) => (
                  <span key={s} className="tag">{s}</span>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-[#5a5c72]">
              No profile set.{" "}
              <Link href="/profile" className="text-[var(--accent)]">Create one →</Link>
            </p>
          )}
        </div>

        {/* Goals Card */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-semibold">Goals & Direction</h2>
            <Link href="/goals" className="text-xs text-[var(--accent)] hover:underline">
              Edit →
            </Link>
          </div>
          {goals ? (
            <div>
              <div className="text-xs text-[#8a8ca0] uppercase tracking-wider mb-2">Target Roles</div>
              <div className="flex flex-wrap gap-2 mb-4">
                {goals.target_roles?.map((r) => (
                  <span key={r} className="tag">{r}</span>
                ))}
              </div>
              <div className="text-xs text-[#8a8ca0] uppercase tracking-wider mb-2">Domains</div>
              <div className="flex flex-wrap gap-2 mb-4">
                {goals.domains?.map((d) => (
                  <span key={d} className="tag">{d}</span>
                ))}
              </div>
              {goals.career_direction && (
                <div className="text-sm text-[#8a8ca0] mt-2 italic">
                  "{goals.career_direction}"
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-[#5a5c72]">
              No goals set.{" "}
              <Link href="/goals" className="text-[var(--accent)]">Set goals →</Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ value, label }) {
  return (
    <div className="glass-card p-5 text-center">
      <div className="text-3xl font-bold gradient-text mb-1">{value}</div>
      <div className="text-xs text-[#8a8ca0] uppercase tracking-wider">{label}</div>
    </div>
  );
}

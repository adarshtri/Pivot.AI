"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { getProfile, getGoals, getStats, getInsights, getLearningHub, trackSkill } from "./lib/api";
import { useToast, Spinner } from "./components/ui";

export default function DashboardPage() {
  const { getToken } = useAuth();
  const [profile, setProfile] = useState(null);
  const [goals, setGoals] = useState(null);
  const [insights, setInsights] = useState([]);
  const [learningHub, setLearningHub] = useState([]);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [stats, setStats] = useState({ jobCount: 0, companyCount: 0 });
  const [loading, setLoading] = useState(true);
  const { showToast, ToastComponent } = useToast();

  useEffect(() => {
    async function load() {
      try {
        const token = await getToken();
        if (!token) return;

        const [p, g, s, ins, hub] = await Promise.all([
          getProfile(token).catch(() => null),
          getGoals(token).catch(() => null),
          getStats(token).catch(() => ({ jobCount: 0, companyCount: 0 })),
          getInsights(token).catch(() => ({ insights: [] })),
          getLearningHub(token).catch(() => ({ items: [] })),
        ]);
        setProfile(p);
        setGoals(g);
        setStats(s);
        setInsights(ins.insights || []);
        setUpdatedAt(ins.updated_at);
        setLearningHub(hub.items || []);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [getToken]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-[#8a8ca0]">
        <div className="w-5 h-5 border-2 border-white/10 border-t-[var(--accent)] rounded-full animate-spin" />
        Synchronizing career data…
      </div>
    );
  }

  const handleTrackSkill = async (skillName, insightId) => {
    try {
      const token = await getToken();
      await trackSkill(token, skillName, insightId);
      showToast(`Started tracking ${skillName}!`);
      // Refresh learning hub to show update if needed
      const hub = await getLearningHub(token).catch(() => ({ items: [] }));
      setLearningHub(hub.items || []);
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const categories = [
    { type: 'skill_gap', label: 'Skill Gaps', icon: '🎯' },
    { type: 'goal_conflict', label: 'Goal Alignment', icon: '⚖️' },
    { type: 'trajectory', label: 'Trajectory', icon: '📈' }
  ];

  const itemsInProgress = learningHub.filter(i => i.status !== 'mastered');

  return (
    <div className="max-w-6xl mx-auto px-4 pb-20">
      <div className="mb-10 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1 font-outfit">Command Center</h1>
          <p className="text-[#8a8ca0] text-sm font-medium">Consolidated intelligence and career growth.</p>
        </div>
        {updatedAt && (
          <div className="text-[10px] text-[#5a5c72] uppercase tracking-widest font-bold bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
            Sync: {new Date(updatedAt).toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <StatCard value={stats.jobCount} label="Pipeline Items" />
        <StatCard value={profile?.skills?.length || 0} label="Current Skills" />
        <StatCard value={itemsInProgress.length} label="Learning Skills" />
        <StatCard value={insights.length} label="Active Tactics" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        
        {/* Sidebar: Profile & Learning */}
        <div className="lg:col-span-1 space-y-6">
          {/* Profile Card */}
          <div className="glass-card p-6 group hover:border-[var(--accent)] transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm shadow-inner group-hover:scale-110 transition-transform">👤</div>
                <h2 className="font-bold text-sm tracking-tight uppercase">Base Profile</h2>
              </div>
              <Link href="/profile" className="text-[10px] uppercase font-bold text-[var(--accent)] hover:opacity-100 opacity-60 transition-opacity">
                Edit
              </Link>
            </div>
            {profile ? (
              <div className="space-y-4">
                <div>
                  <div className="text-[13px] font-bold text-[#e8e9f0]">{profile.current_role || "Associate"}</div>
                  <div className="text-[11px] text-[#5a5c72] uppercase tracking-widest font-bold mt-0.5">{profile.experience_level}</div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {profile.skills?.map((s) => (
                    <span key={s} className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[9px] text-[#8a8ca0] font-medium">{s}</span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-xs text-[#5a5c72]">Complete profile to enable scoring.</p>
            )}
          </div>

          {/* Learning Hub Card */}
          <div className="glass-card p-6 bg-[rgba(124,92,252,0.02)] border border-[rgba(124,92,252,0.1)] group hover:border-[var(--accent)] transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center text-sm shadow-inner group-hover:rotate-12 transition-transform">🎓</div>
                <h2 className="font-bold text-sm tracking-tight uppercase">Learning Hub</h2>
              </div>
              <Link href="/learning-hub" className="text-[10px] uppercase font-bold text-[var(--accent)] hover:opacity-100 opacity-60">
                Hub →
              </Link>
            </div>
            {itemsInProgress.length > 0 ? (
              <div className="space-y-2.5">
                {itemsInProgress.slice(0, 4).map((item) => (
                  <div key={item._id} className="flex items-center justify-between p-2.5 bg-black/30 rounded-xl border border-white/5 group/skill">
                    <span className="text-xs font-semibold text-[#d0d3e2]">{item.skill_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                      <span className="text-[9px] uppercase font-black text-orange-400/80 tracking-tighter">
                        Active
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 border-2 border-dashed border-white/5 rounded-xl">
                 <p className="text-[10px] text-[#5a5c72] uppercase font-bold tracking-widest">No Active Skills</p>
              </div>
            )}
          </div>
        </div>

        {/* Strategies Section: Vertical Rows */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between px-2 mb-2">
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#5a5c72]">Strategic Tactics</h2>
            <Link href="/strategist" className="text-[10px] font-bold text-[var(--accent)] flex items-center gap-1 group">
               Full Analysis <span className="group-hover:translate-x-1 transition-transform">→</span>
            </Link>
          </div>

          <div className="space-y-4">
            {categories.map((cat) => {
              const insight = insights.find(i => i.type === cat.type);
              return (
                <div key={cat.type} className={`glass-card overflow-hidden group/row transition-all duration-500 hover:bg-white/[0.03]
                  ${!insight ? 'opacity-40 grayscale pointer-events-none border-dashed' : 'border-white/10'}`}>
                  <div className="flex flex-col md:flex-row md:items-center gap-6 p-5 relative">
                    {/* Left Icon/Type */}
                    <div className="flex flex-row md:flex-col items-center gap-3 shrink-0">
                      <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-lg shadow-sm group-hover/row:scale-110 transition-all">
                        {cat.icon}
                      </div>
                      <div className="md:text-[9px] font-black uppercase tracking-tighter text-[#5a5c72] group-hover/row:text-[var(--accent)] transition-colors">
                        {cat.label.split(' ')[0]}
                      </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1">
                      {insight ? (
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div className="max-w-md">
                            <h3 className="text-base font-bold text-[#e8e9f0] mb-1 group-hover/row:translate-x-1 transition-transform">{insight.title}</h3>
                            <p className="text-[11px] text-[#8a8ca0] line-clamp-1 italic opacity-80">"{insight.content}"</p>
                          </div>
                          
                          {/* Structured Tags */}
                          <div className="flex items-center gap-2">
                            {insight.structured_items?.slice(0, 2).map((item, idx) => (
                              <div key={idx} className="flex items-center gap-2 bg-white/5 border border-white/10 px-2 py-1.5 rounded-lg group/tag transition-all hover:border-[var(--accent)]/30">
                                <span className="text-[10px] font-bold text-[#d0d3e2]">{item.label}</span>
                                <button 
                                  onClick={() => handleTrackSkill(item.label, insight._id)}
                                  className="text-[9px] font-black text-[var(--accent)] hover:text-white transition-colors uppercase"
                                >
                                  + TRACK
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-[#5a5c72] font-medium tracking-wide uppercase italic">
                           Aggregating market intelligence...
                        </div>
                      )}
                    </div>

                    {/* Right Arrow/Link */}
                    {insight && (
                      <div className="absolute right-4 top-1/2 -translate-y-1/2 md:relative md:top-auto md:right-auto md:translate-y-0 opacity-0 group-hover/row:opacity-100 transition-opacity">
                        <Link href="/strategist" className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center text-[#5a5c72] hover:bg-[var(--accent)] hover:text-white transition-all">
                          →
                        </Link>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="glass-card p-6 mt-8 flex flex-col md:flex-row items-center justify-between gap-6 overflow-hidden relative">
            <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-[var(--accent)]/5 rounded-full blur-3xl" />
            <div className="flex-1">
              <h2 className="text-sm font-bold uppercase tracking-widest text-[#5a5c72] mb-4">Pipeline Matches</h2>
              <div className="flex items-center gap-2 text-xs text-[#e8e9f0] font-medium">
                <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
                Live scoring active for {stats.jobCount} roles
              </div>
            </div>
            <Link href="/jobs" className="px-6 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs font-bold hover:bg-white/10 transition-all shadow-sm">
               Browse Jobs Table
            </Link>
          </div>
        </div>
      </div>

      {ToastComponent}
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

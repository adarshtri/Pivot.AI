"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { getInsights, deleteInsight, trackSkill } from "../lib/api";
import { useToast, Spinner } from "../components/ui";

export default function StrategistPage() {
  const { getToken } = useAuth();
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState(null);
  const { showToast, ToastComponent } = useToast();

  const handleTrackSkill = async (skillName, insightId) => {
    try {
      const token = await getToken();
      await trackSkill(token, skillName, insightId);
      showToast(`Started tracking ${skillName} in your Learning Hub!`);
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const fetchInsights = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getInsights(token);
      setInsights(data.insights || []);
      setUpdatedAt(data.updated_at);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [getToken]);

  const handleDelete = async (id) => {
    try {
      const token = await getToken();
      await deleteInsight(token, id);
      setInsights(insights.filter(i => i._id !== id));
      showToast("Insight removed");
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const categories = [
    { type: 'skill_gap', label: 'Skill Gaps', icon: '🎯', desc: 'Technical bottlenecks' },
    { type: 'goal_conflict', label: 'Goal Alignment', icon: '⚖️', desc: 'Conflicting priorities' },
    { type: 'trajectory', label: 'Trajectory', icon: '📈', desc: 'Growth potential' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-[#8a8ca0]">
        <Spinner /> Synthesizing your latest strategy…
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4">
      <div className="mb-10 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Strategy Dashboard</h1>
          <p className="text-[#8a8ca0]">
            Market-aware intelligence derived from your pipeline and goals.
          </p>
        </div>
        {updatedAt && (
          <div className="text-[10px] text-[#5a5c72] uppercase tracking-widest font-bold">
            Last Updated: {new Date(updatedAt).toLocaleString()}
          </div>
        )}
      </div>

      {insights.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <div className="text-4xl mb-4">🧠</div>
          <h3 className="text-lg font-semibold mb-2">No Insights Yet</h3>
          <p className="text-[#8a8ca0] max-w-sm mx-auto mb-6">
            Go to the Admin panel and trigger the **AI Insights Engine** to build your first strategy dashboard.
          </p>
          <a href="/admin" className="btn-primary no-underline inline-block">
            Go to Admin
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {categories.map((cat) => {
            const insight = insights.find(i => i.type === cat.type);
            return (
              <div key={cat.type} className="flex flex-col gap-4">
                <div className="flex items-center gap-3 px-2">
                  <span className="text-xl">{cat.icon}</span>
                  <div>
                    <h3 className="font-bold text-sm uppercase tracking-wider">{cat.label}</h3>
                    <p className="text-[10px] text-[#5a5c72] font-medium">{cat.desc}</p>
                  </div>
                </div>

                {insight ? (
                  <div className="glass-card h-full flex flex-col group relative overflow-hidden">
                    {/* Priority Indicator */}
                    <div className={`absolute top-0 left-0 right-0 h-1 
                      ${insight.priority === 1 ? 'bg-orange-500' : 'bg-blue-500'}`} 
                    />
                    
                    <div className="p-5 flex-1 flex flex-col">
                      <h2 className="text-lg font-bold mb-4 leading-tight">{insight.title}</h2>
                      
                      {/* Structured Items */}
                      {insight.structured_items && insight.structured_items.length > 0 && (
                        <div className="flex flex-col gap-2 mb-6">
                          {insight.structured_items.map((item, idx) => (
                            <div key={idx} className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-3 py-2 shadow-sm group/item">
                              <span className="font-semibold text-xs">{item.label}</span>
                              <div className="flex items-center gap-2">
                                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-tighter
                                  ${item.status?.toLowerCase().includes('highly') ? 'bg-orange-500/20 text-orange-300' : 
                                    item.status?.toLowerCase().includes('nice') ? 'bg-blue-500/20 text-blue-300' : 
                                    'bg-green-500/20 text-green-300'}`}
                                >
                                  {item.status}
                                </span>
                                <button 
                                  onClick={() => handleTrackSkill(item.label, insight._id)}
                                  className="opacity-0 group-hover/item:opacity-100 text-[9px] text-[var(--accent)] hover:text-white transition-all font-bold"
                                >
                                  + TRACK
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="text-[13px] text-[#8a8ca0] mb-6 leading-relaxed italic border-l-2 border-white/5 pl-4">
                        {insight.content}
                      </div>

                      {insight.recommendations && insight.recommendations.length > 0 && (
                        <div className="mt-auto pt-4 border-t border-white/5">
                          <h4 className="text-[10px] font-bold text-[#5a5c72] uppercase tracking-wider mb-3">
                            Next Steps
                          </h4>
                          <ul className="space-y-3 p-0 m-0">
                            {insight.recommendations.map((rec, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-xs text-[#d0d3e2]">
                                <span className="text-[var(--accent)] mt-0.5">→</span>
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="glass-card p-8 border-dashed border-white/10 flex flex-col items-center justify-center text-center opacity-50 grayscale">
                    <div className="text-2xl mb-2">⏳</div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-[#5a5c72]">Analysis Pending</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {ToastComponent}
    </div>
  );
}

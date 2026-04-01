"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { getLearningHub, updateLearningStatus, promoteSkill, deleteLearningItem } from "../lib/api";
import { useToast, Spinner } from "../components/ui";

export default function LearningHubPage() {
  const { getToken } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [promoting, setPromoting] = useState(null);
  const { showToast, ToastComponent } = useToast();

  const fetchData = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const res = await getLearningHub(token);
      setItems(res.items || []);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [getToken]);

  const handleStatusChange = async (itemId, status) => {
    try {
      const token = await getToken();
      await updateLearningStatus(token, itemId, status);
      setItems(items.map(i => i._id === itemId ? { ...i, status } : i));
      showToast(`Status updated to ${status}`);
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const handlePromote = async (itemId, skillName) => {
    setPromoting(itemId);
    try {
      const token = await getToken();
      await promoteSkill(token, itemId);
      setItems(items.map(i => i._id === itemId ? { ...i, status: 'mastered' } : i));
      showToast(`${skillName} promoted to your profile! Re-scoring started.`);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setPromoting(null);
    }
  };

  const handleDelete = async (itemId) => {
    try {
      const token = await getToken();
      await deleteLearningItem(token, itemId);
      setItems(items.filter(i => i._id !== itemId));
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-[#8a8ca0]">
        <Spinner /> Loading your growth plan…
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Learning Hub</h1>
        <p className="text-[#8a8ca0]">
          Track the skills that will unlock your next career milestone.
        </p>
      </div>

      {items.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <div className="text-4xl mb-4">🎓</div>
          <h3 className="text-lg font-semibold mb-2">No Skills Tracked</h3>
          <p className="text-[#8a8ca0] max-w-sm mx-auto mb-6">
            Find recommended skills in the **Strategist** tab and add them here to track your progress.
          </p>
          <a href="/strategist" className="btn-primary no-underline inline-block">
            View Recommendations
          </a>
        </div>
      ) : (
        <div className="grid gap-6">
          {items.map((item) => (
            <div key={item._id} className="glass-card p-6 flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-xl font-bold
                  ${item.status === 'mastered' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 
                    item.status === 'in_progress' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' : 
                    'bg-white/5 text-[#8a8ca0] border border-white/10'}`}>
                  {item.skill_name.charAt(0)}
                </div>
                <div>
                  <h3 className="text-lg font-bold">{item.skill_name}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <select 
                      value={item.status}
                      onChange={(e) => handleStatusChange(item._id, e.target.value)}
                      className="bg-transparent text-xs text-[#8a8ca0] border-none outline-none cursor-pointer hover:text-white transition-all uppercase font-bold tracking-widest"
                      disabled={item.status === 'mastered'}
                    >
                      <option value="planned">Planned</option>
                      <option value="in_progress">In Progress</option>
                      <option value="mastered">Mastered (In Profile)</option>
                    </select>
                    <span className="text-[#3a3b50]">•</span>
                    <span className="text-[10px] text-[#5a5c72] uppercase tracking-widest">Added {new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {item.status !== 'mastered' && (
                  <button 
                    onClick={() => handlePromote(item._id, item.skill_name)}
                    disabled={promoting === item._id}
                    className="px-4 py-2 bg-[rgba(124,92,252,0.1)] border border-[rgba(124,92,252,0.3)] text-[var(--accent)] hover:bg-[var(--accent)] hover:text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2"
                  >
                    {promoting === item._id ? <Spinner /> : "🚀 I Learned This"}
                  </button>
                )}
                {item.status === 'mastered' && (
                  <div className="flex items-center gap-2 text-green-400 text-xs font-bold bg-green-500/5 px-4 py-2 rounded-lg border border-green-500/10">
                    ✅ Active in Profile
                  </div>
                )}
                <button 
                  onClick={() => handleDelete(item._id)}
                  className="p-2 text-[#5a5c72] hover:text-red-400 transition-all"
                  title="Remove from Hub"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {ToastComponent}
    </div>
  );
}

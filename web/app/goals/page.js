"use client";
import { useEffect, useState } from "react";
import { getGoals, upsertGoals } from "../lib/api";
import { useToast, TagInput, Spinner } from "../components/ui";

export default function GoalsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [goals, setGoals] = useState([]);
  const { showToast, ToastComponent } = useToast();

  useEffect(() => {
    getGoals("user1")
      .then((g) => {
        setGoals(g.goals || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleAddGoal = () => {
    setGoals([...goals, { id: crypto.randomUUID(), type: "Target Role", text: "", weight: 1.0 }]);
  };

  const updateGoal = (id, field, value) => {
    setGoals(goals.map(g => g.id === id ? { ...g, [field]: value } : g));
  };

  const removeGoal = (id) => {
    setGoals(goals.filter(g => g.id !== id));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const validGoals = goals.filter(g => g.text.trim());
      await upsertGoals({
        user_id: "user1",
        goals: validGoals,
      });
      showToast("Goals saved successfully");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-[#8a8ca0]">
        <Spinner /> Loading…
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-1">Goals</h1>
        <p className="text-[#8a8ca0]">
          Define what you're looking for. This drives company discovery and job scoring.
        </p>
      </div>

      <div className="glass-card p-6 max-w-4xl">
        <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-4">
          Priority Rubric
        </label>
        
        <div className="space-y-4 mb-6">
          {goals.map(g => (
            <div key={g.id} className="flex items-center gap-3">
              <select
                className="input-dark w-40 shrink-0"
                value={g.type}
                onChange={e => updateGoal(g.id, "type", e.target.value)}
              >
                <option value="Target Role">Role</option>
                <option value="Domain">Domain</option>
                <option value="Location">Location</option>
                <option value="Career Direction">Direction</option>
              </select>
              <input 
                className="input-dark flex-1" 
                value={g.text} 
                onChange={e => updateGoal(g.id, "text", e.target.value)} 
                placeholder="e.g. Senior Software Engineer" 
              />
              <select 
                className="input-dark w-48" 
                value={g.weight} 
                onChange={e => updateGoal(g.id, "weight", parseFloat(e.target.value))}
              >
                <option value={10}>Dealbreaker (10x)</option>
                <option value={5}>High Priority (5x)</option>
                <option value={1}>Standard (1x)</option>
              </select>
              <button 
                className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 text-[#5a5c72] hover:bg-red-500/10 hover:text-red-400 transition-colors"
                onClick={() => removeGoal(g.id)}
              >
                ✕
              </button>
            </div>
          ))}
          {goals.length === 0 && (
            <p className="text-sm text-[#5a5c72] italic">No goals defined. Add some rules to teach the AI what you want.</p>
          )}
        </div>
        
        <button 
          className="text-sm font-medium text-[#7c5cfc] hover:brightness-110 flex items-center gap-2 mb-8 transition-all"
          onClick={handleAddGoal}
        >
          <span className="text-lg">+</span> Add Rubric Goal
        </button>

        <button
          className="btn-primary flex items-center gap-2"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? <Spinner /> : null}
          {saving ? "Saving…" : "Save Goals"}
        </button>
      </div>

      {ToastComponent}
    </div>
  );
}

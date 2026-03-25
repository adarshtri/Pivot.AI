"use client";
import { useEffect, useState } from "react";
import { getGoals, upsertGoals } from "../lib/api";
import { useToast, TagInput, Spinner } from "../components/ui";

export default function GoalsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [targetRoles, setTargetRoles] = useState([]);
  const [domains, setDomains] = useState([]);
  const [locations, setLocations] = useState([]);
  const [careerDirection, setCareerDirection] = useState("");
  const { showToast, ToastComponent } = useToast();

  useEffect(() => {
    getGoals("user1")
      .then((g) => {
        setTargetRoles(g.target_roles || []);
        setDomains(g.domains || []);
        setLocations(g.locations || []);
        setCareerDirection(g.career_direction || "");
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await upsertGoals({
        user_id: "user1",
        target_roles: targetRoles,
        domains,
        locations,
        career_direction: careerDirection,
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

      <div className="glass-card p-6 max-w-2xl">
        <div className="mb-6">
          <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
            Target Roles
          </label>
          <TagInput
            tags={targetRoles}
            onAdd={(tag) => setTargetRoles([...targetRoles, tag])}
            onRemove={(tag) => setTargetRoles(targetRoles.filter((r) => r !== tag))}
            placeholder="e.g. AI Engineer, ML Infra Engineer"
          />
        </div>

        <div className="mb-6">
          <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
            Domains
          </label>
          <TagInput
            tags={domains}
            onAdd={(tag) => setDomains([...domains, tag])}
            onRemove={(tag) => setDomains(domains.filter((d) => d !== tag))}
            placeholder="e.g. AI, systems, infrastructure"
          />
          <p className="text-xs text-[#5a5c72] mt-2">
            Used by discovery to find companies hiring in these areas.
          </p>
        </div>

        <div className="mb-6">
          <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
            Locations
          </label>
          <TagInput
            tags={locations}
            onAdd={(tag) => setLocations([...locations, tag])}
            onRemove={(tag) => setLocations(locations.filter((l) => l !== tag))}
            placeholder="e.g. San Francisco, Remote, New York"
          />
        </div>

        <div className="mb-8">
          <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
            Career Direction
          </label>
          <input
            className="input-dark"
            value={careerDirection}
            onChange={(e) => setCareerDirection(e.target.value)}
            placeholder="e.g. Technical leadership in AI systems"
          />
        </div>

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

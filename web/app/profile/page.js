"use client";
import { useEffect, useState } from "react";
import { getProfile, upsertProfile } from "../lib/api";
import { useToast, TagInput, Spinner } from "../components/ui";

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [experienceLevel, setExperienceLevel] = useState("");
  const [currentRole, setCurrentRole] = useState("");
  const [skills, setSkills] = useState([]);
  const { showToast, ToastComponent } = useToast();

  useEffect(() => {
    getProfile("user1")
      .then((p) => {
        setProfile(p);
        setSkills(p.skills || []);
        setExperienceLevel(p.experience_level || "");
        setCurrentRole(p.current_role || "");
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const data = {
        user_id: "user1",
        skills,
        experience_level: experienceLevel,
        current_role: currentRole,
      };
      const result = await upsertProfile(data);
      setProfile(result);
      showToast("Profile saved successfully");
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
        <h1 className="text-3xl font-bold tracking-tight mb-1">Profile</h1>
        <p className="text-[#8a8ca0]">Tell the system who you are.</p>
      </div>

      <div className="glass-card p-6 max-w-2xl">
        <div className="mb-6">
          <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
            Current Role
          </label>
          <input
            className="input-dark"
            value={currentRole}
            onChange={(e) => setCurrentRole(e.target.value)}
            placeholder="e.g. Senior Software Engineer"
          />
        </div>

        <div className="mb-6">
          <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
            Experience Level
          </label>
          <input
            className="input-dark"
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value)}
            placeholder="e.g. L5, Senior, 5+ years"
          />
        </div>

        <div className="mb-8">
          <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
            Skills
          </label>
          <TagInput
            tags={skills}
            onAdd={(tag) => setSkills([...skills, tag])}
            onRemove={(tag) => setSkills(skills.filter((s) => s !== tag))}
            placeholder="Add a skill and press Enter"
          />
          <p className="text-xs text-[#5a5c72] mt-2">
            These drive job matching and scoring.
          </p>
        </div>

        <button
          className="btn-primary flex items-center gap-2"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? <Spinner /> : null}
          {saving ? "Saving…" : "Save Profile"}
        </button>
      </div>

      {ToastComponent}
    </div>
  );
}

"use client";
import { useEffect, useState } from "react";
import { useToast, Spinner } from "../components/ui";
import {
  getAdminSettings,
  updateAdminSettings,
  adminRunDiscovery,
  adminRunIngestion,
  triggerScoring,
} from "../lib/api";

export default function AdminPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [scoring, setScoring] = useState(false);

  // Form state
  const [braveKey, setBraveKey] = useState("");
  const [ingestionHours, setIngestionHours] = useState(6);
  const [discoveryHours, setDiscoveryHours] = useState(24);

  const { showToast, ToastComponent } = useToast();

  useEffect(() => {
    getAdminSettings()
      .then((s) => {
        setSettings(s);
        setIngestionHours(s.ingestion_interval_hours || 6);
        setDiscoveryHours(s.discovery_interval_hours || 24);
      })
      .catch((err) => showToast(err.message, "error"))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        brave_search_api_key: braveKey, // empty = keep existing
        ingestion_interval_hours: ingestionHours,
        discovery_interval_hours: discoveryHours,
      };
      const result = await updateAdminSettings(payload);
      setSettings(result);
      setBraveKey("");
      showToast("Settings saved");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDiscovery = async () => {
    setDiscovering(true);
    try {
      const result = await adminRunDiscovery();
      showToast(`Discovery: ${result.companies_added} new companies found`);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setDiscovering(false);
    }
  };

  const handleIngestion = async () => {
    setIngesting(true);
    try {
      const result = await adminRunIngestion();
      showToast(
        `Ingestion: ${result.new_inserted || 0} new, ${result.updated || 0} updated`
      );
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setIngesting(false);
    }
  };

  const handleScoring = async () => {
    setScoring(true);
    try {
      const result = await triggerScoring("user1");
      showToast(
        `Scoring: ${result.total_scored} jobs scored (${result.new_pipeline_items} new items)`
      );
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setScoring(false);
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
        <h1 className="text-3xl font-bold tracking-tight mb-1">Admin</h1>
        <p className="text-[#8a8ca0]">System settings and operations.</p>
      </div>

      {/* System Operations */}
      <div className="glass-card p-6 mb-6">
        <h2 className="font-semibold mb-4">System Operations</h2>
        <div className="flex gap-3 flex-wrap">
          <button
            className="btn-primary flex items-center gap-2"
            onClick={handleDiscovery}
            disabled={discovering}
          >
            {discovering ? <Spinner /> : null}
            {discovering ? "Discovering…" : "🔍 Run Discovery"}
          </button>
          <button
            className="btn-primary flex items-center gap-2"
            onClick={handleIngestion}
            disabled={ingesting}
          >
            {ingesting ? <Spinner /> : null}
            {ingesting ? "Ingesting…" : "🔄 Run Ingestion"}
          </button>
          <button
            className="btn-primary flex items-center gap-2"
            onClick={handleScoring}
            disabled={scoring}
          >
            {scoring ? <Spinner /> : null}
            {scoring ? "Scoring…" : "🧠 Run AI Scoring"}
          </button>
        </div>
      </div>

      {/* Settings */}
      <div className="glass-card p-6">
        <h2 className="font-semibold mb-6">Settings</h2>

        <div className="space-y-6 max-w-2xl">
          <div>
            <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
              Brave Search API Key
            </label>
            <input
              className="input-dark"
              type="password"
              value={braveKey}
              onChange={(e) => setBraveKey(e.target.value)}
              placeholder={settings?.brave_search_api_key_set ? "••••••• (key is set)" : "Enter your API key"}
            />
            <p className="text-xs text-[#5a5c72] mt-1">
              {settings?.brave_search_api_key_set
                ? "Key is configured. Leave blank to keep existing key."
                : "Get a free key at brave.com/search/api"}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
                Ingestion Interval (hours)
              </label>
              <input
                className="input-dark"
                type="number"
                min="1"
                value={ingestionHours}
                onChange={(e) => setIngestionHours(parseInt(e.target.value) || 6)}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
                Discovery Interval (hours)
              </label>
              <input
                className="input-dark"
                type="number"
                min="1"
                value={discoveryHours}
                onChange={(e) => setDiscoveryHours(parseInt(e.target.value) || 24)}
              />
            </div>
          </div>

          <button
            className="btn-primary flex items-center gap-2"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? <Spinner /> : null}
            {saving ? "Saving…" : "Save Settings"}
          </button>
        </div>
      </div>

      {ToastComponent}
    </div>
  );
}

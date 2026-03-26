"use client";
import { useEffect, useState } from "react";
import { useToast, Spinner } from "../components/ui";
import {
  getAdminSettings,
  updateAdminSettings,
  adminRunDiscovery,
  adminRunIngestion,
  triggerScoring,
  triggerInference,
} from "../lib/api";

export default function AdminPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [inferring, setInferring] = useState(false);

  // Form state
  const [braveKey, setBraveKey] = useState("");
  const [modelProvider, setModelProvider] = useState("ollama");
  const [modelName, setModelName] = useState("phi4-mini");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [ingestionHours, setIngestionHours] = useState(6);
  const [discoveryHours, setDiscoveryHours] = useState(24);

  const { showToast, ToastComponent } = useToast();

  useEffect(() => {
    getAdminSettings()
      .then((s) => {
        setSettings(s);
        setModelProvider(s.model_provider || "ollama");
        setModelName(s.model_name || "phi4-mini");
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
        brave_search_api_key: braveKey || (settings?.brave_search_api_key_set ? "********" : ""),
        llm_api_key: llmApiKey || (settings?.llm_api_key_set ? "********" : ""),
        model_provider: modelProvider,
        model_name: modelName,
        ingestion_interval_hours: ingestionHours,
        discovery_interval_hours: discoveryHours,
      };
      const result = await updateAdminSettings(payload);
      setSettings(result);
      setBraveKey("");
      setLlmApiKey("");
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
      showToast(result.message || "Scoring started in background");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setScoring(false);
    }
  };

  const handleInference = async () => {
    setInferring(true);
    try {
      const result = await triggerInference("user1");
      showToast(result.message || "LLM inference started in background");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setInferring(false);
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
          <button
            className="btn-primary flex items-center gap-2"
            onClick={handleInference}
            disabled={inferring}
          >
            {inferring ? <Spinner /> : null}
            {inferring ? "Reasoning…" : "🤖 Run LLM Reasoning"}
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
              className="input-dark w-full"
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
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
                Model Provider
              </label>
              <select
                className="input-dark w-full"
                value={modelProvider}
                onChange={(e) => setModelProvider(e.target.value)}
              >
                <option value="ollama">Local (Ollama)</option>
                <option value="groq">Cloud (Groq LPU)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
                Model Name
              </label>
              <input
                className="input-dark w-full"
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder={modelProvider === "ollama" ? "e.g. phi4-mini, llama3.2" : "e.g. llama3-8b-8192"}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
                API Key
              </label>
              <input
                className="input-dark w-full"
                type="password"
                value={llmApiKey}
                onChange={(e) => setLlmApiKey(e.target.value)}
                placeholder={settings?.llm_api_key_set ? "••••••• (key is set)" : modelProvider === "groq" ? "Enter your Groq key" : "Not required for Ollama"}
                disabled={modelProvider === "ollama"}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#8a8ca0] uppercase tracking-wider mb-2">
                Ingestion Interval (hours)
              </label>
              <input
                className="input-dark w-full"
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
                className="input-dark w-full"
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

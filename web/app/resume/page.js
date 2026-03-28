"use client";
import { useEffect, useState } from "react";
import { getProfile, upsertProfile } from "../lib/api";
import { Spinner, useToast } from "../components/ui";

const DEFAULT_LATEX = `\\documentclass[a4paper]{article}
\\usepackage{fullpage}
\\begin{document}
\\begin{center}
    {\\Huge \\scshape {Your Name}} \\\\
    Street Address, City, State ZIP $\\cdot$ you@email.com $\\cdot$ 123-456-7890
\\end{center}

\\section{Experience}
\\textbf{Role Name} \\hfill Location \\\\
\\textit{Company Name} \\hfill Dates \\\\
\\begin{itemize}
    \\item Item 1
    \\item Item 2
\\end{itemize}

\\end{document}`;

export default function ResumePage() {
  const [profile, setProfile] = useState(null);
  const [latex, setLatex] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { showToast, ToastComponent } = useToast();

  useEffect(() => {
    async function load() {
      try {
        const p = await getProfile("user1");
        setProfile(p);
        setLatex(p.resume_latex || DEFAULT_LATEX);
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await upsertProfile({ ...profile, resume_latex: latex });
      showToast("Base resume saved!");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([latex], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resume.tex";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>;

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col">
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Base Resume Template</h1>
          <p className="text-[#8a8ca0] text-sm italic">Define your core resume in LaTeX. AI will use this as the anchor for all applications.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleDownload}
            className="px-6 py-2 bg-white/5 border border-white/10 text-white font-bold rounded-xl hover:bg-white/10 transition-all"
          >
            Download .tex
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2 bg-[var(--accent)] text-white font-bold rounded-xl shadow-lg shadow-[var(--accent)]/20 hover:scale-105 transition-all disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Template"}
          </button>
        </div>
      </div>

      <div className="glass-card flex-1 flex flex-col overflow-hidden border-[#7c5cfc]/20 bg-black/40 shadow-2xl">
        <div className="px-6 py-3 border-b border-white/5 bg-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-widest text-[#5a5c72]">main.tex (Source Editor)</span>
          </div>
          <span className="text-[10px] font-mono text-[#5a5c72]">LaTeX 2e</span>
        </div>
        <textarea
          value={latex}
          onChange={(e) => setLatex(e.target.value)}
          className="flex-1 p-8 bg-transparent text-sm font-mono text-[#d0d3e2] outline-none resize-none selection:bg-[var(--accent)]/30"
          spellCheck="false"
          placeholder="Paste your LaTeX here..."
        />
        <div className="px-6 py-3 bg-[var(--accent)]/5 border-t border-white/5 text-center">
          <p className="text-[9px] font-bold text-[var(--accent)] uppercase tracking-[0.2em] opacity-60">Ready for AI Tailoring</p>
        </div>
      </div>
      
      {ToastComponent}
    </div>
  );
}

"use client";

/* ========================================
   CommandInput — URL Input Hero
   Internal-tool style: focused input bar
   with tier selector and verdict mode.
   Replaces marketing HeroSection.
   ======================================== */

import { PanelChrome } from "@/components/layout/PanelChrome";
import { ArrowRight, Loader2, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TIERS = [
  { id: "quick_scan", label: "QUICK", time: "~60s", pages: "1-3 pages" },
  { id: "standard_audit", label: "STANDARD", time: "~3min", pages: "5 pages" },
  { id: "deep_forensic", label: "DEEP", time: "~5min", pages: "10 pages" },
  { id: "darknet_investigation", label: "DARKNET", time: "~8min", pages: "15 pages" },
] as const;

export function CommandInput() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [tier, setTier] = useState("standard_audit");
  const [verdictMode, setVerdictMode] = useState("expert");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError("");

    try {
      const targetUrl = url.startsWith("http") ? url : `https://${url}`;
      const res = await fetch(`${API_URL}/api/audit/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: targetUrl, tier, verdict_mode: verdictMode }),
      });

      if (!res.ok) throw new Error("Failed to start audit");

      const data = await res.json();
      router.push(`/audit/${data.audit_id}?url=${encodeURIComponent(targetUrl)}&tier=${tier}&verdict=${verdictMode}`);
    } catch {
      setError("Could not connect to Veritas backend. Ensure the server is running.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Brand mark */}
      <div className="text-center mb-6">
        <h1 className="text-[28px] font-bold tracking-tight text-[var(--v-text)]">
          VERITAS
        </h1>
        <p className="text-[12px] font-mono text-[var(--v-text-tertiary)] uppercase tracking-[0.2em]">
          Autonomous Forensic Web Auditor
        </p>
      </div>

      {/* Input bar */}
      <form onSubmit={handleSubmit}>
        <div className="relative group">
          <div className="absolute -inset-[1px] bg-gradient-to-r from-cyan-500/20 to-purple-600/20 rounded-lg opacity-0 group-focus-within:opacity-100 blur-sm transition-opacity" />
          <div className="relative flex items-center bg-[var(--elev-2,var(--v-surface))] rounded-lg border border-[rgba(255,255,255,0.08)] focus-within:border-cyan-500/40 transition-colors">
            <Search className="ml-4 w-4 h-4 text-[var(--v-text-tertiary)]" />
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter URL to audit..."
              className="flex-1 bg-transparent px-3 py-3.5 text-[14px] font-mono text-[var(--v-text)] placeholder:text-[var(--v-text-tertiary)] focus:outline-none"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="mr-2 px-4 py-2 rounded-md bg-cyan-500 text-[var(--v-deep)] font-mono font-bold text-[11px] uppercase tracking-wider flex items-center gap-1.5 hover:bg-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <>
                  ANALYZE
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <p className="mt-2 text-[11px] font-mono text-red-400">{error}</p>
        )}

        {/* Tier + Verdict selectors */}
        <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          {/* Tier pills */}
          <div className="flex items-center gap-1">
            <span className="text-[9px] font-mono uppercase tracking-wider text-[var(--v-text-tertiary)] mr-2">
              TIER
            </span>
            {TIERS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTier(t.id)}
                className={cn(
                  "px-2.5 py-1.5 rounded text-[10px] font-mono border transition-colors",
                  tier === t.id
                    ? "border-cyan-500/40 text-cyan-400 bg-cyan-500/10"
                    : "border-[rgba(255,255,255,0.06)] text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] hover:border-[rgba(255,255,255,0.1)]"
                )}
              >
                {t.label}
                <span className="ml-1 opacity-60">{t.time}</span>
              </button>
            ))}
          </div>

          {/* Verdict mode */}
          <div className="flex items-center gap-1">
            <span className="text-[9px] font-mono uppercase tracking-wider text-[var(--v-text-tertiary)] mr-2">
              VERDICT
            </span>
            {(["simple", "expert"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setVerdictMode(m)}
                className={cn(
                  "px-2.5 py-1.5 rounded text-[10px] font-mono border transition-colors",
                  verdictMode === m
                    ? "border-purple-500/40 text-purple-400 bg-purple-500/10"
                    : "border-[rgba(255,255,255,0.06)] text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
                )}
              >
                {m.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
}

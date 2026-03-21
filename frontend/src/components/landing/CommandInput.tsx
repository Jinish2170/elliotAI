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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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

    const targetUrl = url.startsWith("http") ? url : `https://${url}`;
    
    // Strict pre-flight browser URL validation
    try {
      const parsed = new URL(targetUrl);
      if (!parsed.hostname.includes(".")) {
         throw new Error("Invalid TLD");
      }
    } catch (err) {
      setError("[SYS.ERR] INSUFFICIENT TARGET: Provide a valid FQDN or IP");
      setLoading(false);
      return;
    }

    try {
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
    <div className="max-w-3xl mx-auto w-full">
      {/* Brand mark */}
      <div className="text-center mb-8">
        <h1 className="text-[32px] font-bold tracking-widest text-[#00FF41] glitch-text relative inline-block">
          VERITAS
        </h1>
        <p className="text-[12px] font-mono text-[var(--t-dim)] uppercase tracking-[0.3em] mt-2">
          Autonomous Forensic Web Auditor
        </p>
      </div>

      {/* Input bar */}
      <form onSubmit={handleSubmit} className="border border-[var(--t-border)] p-4 bg-[#050505] relative shadow-[0_0_15px_rgba(0,255,65,0.05)]">
        {/* Corner Accents */}
        <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[#00FF41]" />
        <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-[#00FF41]" />
        <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-[#00FF41]" />
        <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[#00FF41]" />
        
        <div className="relative group flex items-center bg-[#0a0a0a] border border-[#222] focus-within:border-[#00FF41] transition-colors h-14">
            <span className="text-[#00FF41] font-mono pl-4 animate-pulse select-none">{'>'}</span>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="TARGET_URI_STREAM..."
              className="flex-1 bg-transparent px-3 py-3.5 text-[14px] font-mono text-[var(--t-text)] placeholder:text-[var(--t-dim)] focus:outline-none placeholder:opacity-50"
              disabled={loading}
              autoFocus
            />
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="h-full px-6 bg-[var(--t-border)] text-[var(--t-text)] font-mono font-bold text-[11px] uppercase tracking-widest flex items-center gap-2 hover:bg-[#00FF41] hover:text-[#050505] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <>
                  <span className="animate-pulse">BOOTING</span>
                </>
              ) : (
                "INITIATE_AUDIT"
              )}
            </button>
        </div>

        {error && (
          <div className="mt-3 p-2 border border-[var(--t-red)] bg-[#1a0505] text-[11px] font-mono text-[var(--t-red)] glitch-text">
            {error}
          </div>
        )}

        {/* Tier + Verdict selectors */}
        <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center gap-6 justify-between border-t border-[var(--t-border)] pt-4">
          {/* Tier pills */}
          <div className="flex items-center gap-1 w-full justify-between sm:w-auto sm:justify-start">
            <span className="text-[10px] font-mono uppercase tracking-widest text-[var(--t-dim)] mr-2">
              TIER.SELECT:
            </span>
            {TIERS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTier(t.id)}
                className={cn(
                  "px-3 py-1 text-[10px] font-mono border transition-colors uppercase tracking-wider",
                  tier === t.id
                    ? "border-[#00FF41] text-[#00FF41] bg-[#00FF41]/10 shadow-[0_0_8px_rgba(0,255,65,0.2)]"
                    : "border-[#333] text-[var(--t-dim)] hover:text-[var(--t-text)] hover:border-[#555]"
                )}
              >
                {t.label} 
              </button>
            ))}
          </div>

          {/* Verdict mode */}
          <div className="flex items-center gap-1 w-full justify-between sm:w-auto sm:justify-start">
            <span className="text-[10px] font-mono uppercase tracking-widest text-[var(--t-dim)] mr-2">
              VERDICT.MODE:
            </span>
            {(["simple", "expert"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setVerdictMode(m)}
                className={cn(
                  "px-3 py-1 text-[10px] font-mono border transition-colors uppercase tracking-wider",
                  verdictMode === m
                    ? "border-[#FF003C] text-[#FF003C] bg-[#FF003C]/10 shadow-[0_0_8px_rgba(255,0,60,0.2)]"
                    : "border-[#333] text-[var(--t-dim)] hover:text-[var(--t-text)] hover:border-[#555]"
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

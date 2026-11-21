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
  {
    id: "quick_scan",
    label: "QUICK SCAN",
    time: "~2-3 min",
    pages: "2 pages",
    blurb: "Homepage check: security headers, TLS, WHOIS, visual dark-pattern scan, trust score.",
  },
  {
    id: "standard_audit",
    label: "FULL AUDIT",
    time: "~3-5 min",
    pages: "up to 8 pages",
    blurb: "Crawls up to 8 pages with the full 5-agent pipeline: security modules, vision AI, OSINT claim checks, judge.",
  },
  {
    id: "darknet_investigation",
    label: "DARKNET INTEL",
    time: "~10-15 min",
    pages: "up to 20 pages",
    blurb:
      "Full audit, extended to 20 pages and 8 vision passes, plus darknet threat intelligence: .onion references, " +
      "marketplace and exit-scam threat feeds, Tor2Web exposure. Read-only OSINT: it never crawls the dark web.",
  },
] as const;

// Public deployments list the tiers their backend allows (NEXT_PUBLIC_ENABLED_TIERS=quick_scan,standard_audit).
// Unset = everything enabled (local development).
const ENABLED = (process.env.NEXT_PUBLIC_ENABLED_TIERS || "").split(",").map((t) => t.trim()).filter(Boolean);
const isEnabled = (id: string) => ENABLED.length === 0 || ENABLED.includes(id);

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

      if (!res.ok) {
        // Surface the server's reason (tier disabled, rate limit, blocked target)
        let detail = "";
        try { detail = (await res.json()).detail ?? ""; } catch {}
        setError(typeof detail === "string" && detail ? `[SYS.ERR] ${detail}` : `[SYS.ERR] Audit rejected (HTTP ${res.status})`);
        setLoading(false);
        return;
      }

      const data = await res.json();
      router.push(`/audit/${data.audit_id}?url=${encodeURIComponent(targetUrl)}&tier=${tier}&verdict=${verdictMode}`);
    } catch {
      setError("Could not connect to Elliot backend. Ensure the server is running.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto w-full">
      {/* Brand mark */}
      <div className="text-center mb-8">
        <h1 className="text-[32px] font-bold tracking-widest text-[#00FF41] glitch-text relative inline-block">
          ELLIOT
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
            {TIERS.map((t) => {
              const locked = !isEnabled(t.id);
              return (
                <button
                  key={t.id}
                  type="button"
                  disabled={locked}
                  title={locked ? "Disabled on the public demo (heavy tier). Run elliotAI locally to use it." : undefined}
                  onClick={() => setTier(t.id)}
                  className={cn(
                    "px-3 py-1 text-[10px] font-mono border transition-colors uppercase tracking-wider",
                    locked
                      ? "border-[#222] text-[#444] cursor-not-allowed"
                      : tier === t.id
                        ? "border-[#00FF41] text-[#00FF41] bg-[#00FF41]/10 shadow-[0_0_8px_rgba(0,255,65,0.2)]"
                        : "border-[#333] text-[var(--t-dim)] hover:text-[var(--t-text)] hover:border-[#555]"
                  )}
                >
                  {t.label}{locked ? " \u{1F512}" : ""}
                </button>
              );
            })}
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

        {/* Selected tier details */}
        {(() => {
          const t = TIERS.find((x) => x.id === tier) ?? TIERS[1];
          return (
            <div className="mt-3 border border-[var(--t-border)] bg-[#0a0a0a] p-3 text-[11px] font-mono leading-relaxed">
              <div className="flex gap-4 text-[10px] uppercase tracking-widest text-[var(--t-dim)] mb-1">
                <span className="text-[#00FF41]">{t.label}</span>
                <span>{t.time}</span>
                <span>{t.pages}</span>
              </div>
              <p className="text-[var(--t-text)] opacity-80">{t.blurb}</p>
              {!isEnabled("darknet_investigation") && (
                <p className="mt-2 text-[10px] text-[var(--t-dim)]">
                  {"\u{1F512}"} DARKNET INTEL is disabled on the public demo (it is the heaviest tier). Run elliotAI locally to use it.
                </p>
              )}
            </div>
          );
        })()}
      </form>
    </div>
  );
}

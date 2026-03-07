"use client";

import { motion } from "framer-motion";
import { ArrowRight, Loader2, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const tiers = [
  {
    id: "quick",
    label: "Quick Scan",
    time: "~60 seconds",
    duration: "60s",
    pages: "1-3 pages",
    credits: "~5 credits",
    description: "DNS, headers, visible patterns"
  },
  {
    id: "standard_audit",
    label: "Standard Audit",
    time: "~3 minutes",
    duration: "3min",
    pages: "5 pages",
    credits: "~20 credits",
    description: "Full 5-agent pipeline, screenshots, scoring"
  },
  {
    id: "deep_forensic",
    label: "Deep Forensic",
    time: "~5 minutes",
    duration: "5min",
    pages: "10 pages",
    credits: "~50 credits",
    description: "Temporal analysis, extended crawl, graph"
  },
];

export function HeroSection() {
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
      setError("Could not connect to Veritas backend. Make sure the server is running.");
      setLoading(false);
    }
  };

  return (
    <section className="relative min-h-[90vh] flex flex-col items-center justify-center px-4 pt-20">
      {/* Hero content */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="text-center max-w-3xl mx-auto z-10"
      >
        {/* Animated Logo Mark */}
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mx-auto mb-8 w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center animate-float"
        >
          <span className="text-3xl font-black text-white">V</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="text-5xl sm:text-6xl font-bold tracking-tight mb-4"
        >
          <span className="gradient-text">VERITAS</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.6 }}
          className="text-lg text-[var(--v-text-secondary)] mb-2"
        >
          Autonomous Forensic Web Auditor
        </motion.p>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="text-sm text-[var(--v-text-tertiary)] italic mb-10"
        >
          &ldquo;See what websites don&rsquo;t want you to see.&rdquo;
        </motion.p>

        {/* URL Input */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="relative max-w-2xl mx-auto mb-8"
        >
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl opacity-20 group-hover:opacity-40 blur transition-opacity" />
            <div className="relative flex items-center bg-[var(--v-surface)] rounded-xl border border-white/10 focus-within:border-cyan-500/50 transition-colors">
              <Search className="ml-4 w-5 h-5 text-[var(--v-text-tertiary)]" />
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter website URL to audit..."
                className="flex-1 bg-transparent px-4 py-4 text-[var(--v-text)] placeholder:text-[var(--v-text-tertiary)] focus:outline-none text-sm"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !url.trim()}
                className="mr-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-cyan-600 text-[var(--v-deep)] font-semibold text-sm flex items-center gap-2 hover:from-cyan-400 hover:to-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    Analyze
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
          {error && (
            <p className="mt-3 text-xs text-red-400">{error}</p>
          )}
        </motion.form>

        {/* Tier Selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.75, duration: 0.6 }}
          className="flex flex-wrap justify-center gap-4 max-w-3xl mx-auto"
        >
          {tiers.map((t) => (
            <button
              key={t.id}
              onClick={() => setTier(t.id)}
              className={`
                relative px-5 py-4 rounded-xl border text-left transition-all duration-300 min-w-[200px]
                ${
                  tier === t.id
                    ? "border-cyan-500/50 bg-cyan-500/10 glow-cyan shadow-lg shadow-cyan-500/10"
                    : "border-white/5 bg-[var(--v-surface)] hover:border-white/10"
                }
              `}
            >
              {/* Radio indicator */}
              <div className="flex items-center gap-2 mb-2">
                <div
                  className={`w-4 h-4 rounded-full border-2 flex items-center justify-center transition-colors ${
                    tier === t.id
                      ? "border-cyan-500"
                      : "border-[var(--v-text-tertiary)]"
                  }`}
                >
                  {tier === t.id && (
                    <div className="w-2 h-2 rounded-full bg-cyan-500" />
                  )}
                </div>
                <span className="text-sm font-medium text-[var(--v-text)]">
                  {t.label}
                </span>
              </div>
              <div className="mb-2">
                <p className="text-xs text-[var(--v-text-secondary)]">{t.time}</p>
                <p className="text-xs text-[var(--v-text-tertiary)]">{t.description}</p>
              </div>
              {/* Stats */}
              <div className="flex gap-3 text-xs text-[var(--v-text-secondary)] ml-6">
                <span>{t.pages}</span>
                <span>•</span>
                <span>{t.credits}</span>
              </div>
              {/* Badge for selected tier */}
              {tier === t.id && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="absolute -top-2 -right-2 px-2 py-0.5 bg-cyan-500 text-[var(--v-deep)] text-[10px] font-bold rounded-full"
                >
                  SELECTED
                </motion.div>
              )}
            </button>
          ))}
        </motion.div>

        {/* Verdict Mode Toggle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="flex items-center justify-center gap-6 mt-6"
        >
          <label className="text-sm text-[var(--v-text-secondary)]">Verdict Mode:</label>
          <div className="flex gap-2">
            <button
              onClick={() => setVerdictMode("simple")}
              className={`
                px-4 py-2 rounded-lg border text-sm transition-colors
                ${verdictMode === "simple"
                  ? "border-purple-500/50 bg-purple-500/10 text-purple-400"
                  : "border-white/5 bg-[var(--v-surface)] text-[var(--v-text-secondary)] hover:border-white/10"
                }
              `}
            >
              Simple
            </button>
            <button
              onClick={() => setVerdictMode("expert")}
              className={`
                px-4 py-2 rounded-lg border text-sm transition-colors
                ${verdictMode === "expert"
                  ? "border-purple-500/50 bg-purple-500/10 text-purple-400"
                  : "border-white/5 bg-[var(--v-surface)] text-[var(--v-text-secondary)] hover:border-white/10"
                }
              `}
            >
              Expert
            </button>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}

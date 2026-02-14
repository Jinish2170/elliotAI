"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Search, ArrowRight, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const tiers = [
  {
    id: "quick_scan",
    label: "Quick Scan",
    time: "~60 seconds",
    desc: "Basic checks & surface-level analysis",
  },
  {
    id: "standard_audit",
    label: "Standard Audit",
    time: "~3 minutes",
    desc: "Full multi-agent investigation",
  },
  {
    id: "deep_forensic",
    label: "Deep Forensic",
    time: "~5 minutes",
    desc: "Maximum depth — every signal checked",
  },
];

export function HeroSection() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [tier, setTier] = useState("standard_audit");
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
        body: JSON.stringify({ url: targetUrl, tier, verdict_mode: "expert" }),
      });

      if (!res.ok) throw new Error("Failed to start audit");

      const data = await res.json();
      router.push(`/audit/${data.audit_id}?url=${encodeURIComponent(targetUrl)}&tier=${tier}`);
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
          className="flex flex-wrap justify-center gap-3 max-w-2xl mx-auto"
        >
          {tiers.map((t) => (
            <button
              key={t.id}
              onClick={() => setTier(t.id)}
              className={`
                px-5 py-3 rounded-xl border text-left transition-all duration-300 min-w-[180px]
                ${
                  tier === t.id
                    ? "border-cyan-500/50 bg-cyan-500/10 glow-cyan"
                    : "border-white/5 bg-[var(--v-surface)] hover:border-white/10"
                }
              `}
            >
              <div className="flex items-center gap-2 mb-1">
                <div
                  className={`w-3 h-3 rounded-full border-2 ${
                    tier === t.id
                      ? "border-cyan-500 bg-cyan-500"
                      : "border-[var(--v-text-tertiary)]"
                  }`}
                />
                <span className="text-sm font-medium text-[var(--v-text)]">
                  {t.label}
                </span>
              </div>
              <p className="text-xs text-[var(--v-text-tertiary)] ml-5">{t.time}</p>
            </button>
          ))}
        </motion.div>
      </motion.div>
    </section>
  );
}

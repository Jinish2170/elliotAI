"use client";

import { ParticleField } from "@/components/ambient/ParticleField";
import { AnimatedAgentTheater, TrustScoreReveal } from "@/components/audit/theater";
import { AuditHeader } from "@/components/audit/AuditHeader";
import { CompletionOverlay } from "@/components/audit/CompletionOverlay";
import { EvidencePanel } from "@/components/audit/EvidencePanel";
import { ForensicLog } from "@/components/audit/ForensicLog";
import { NarrativeFeed } from "@/components/audit/NarrativeFeed";
import { useAuditStream } from "@/hooks/useAuditStream";
import { AnimatePresence } from "framer-motion";
import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";

/**
 * VERITAS Theater Audit Page - The "Out Theater" Experience
 *
 * A completely overhauled audit page with:
 * - Dramatic stage layout for agents
 * - Cinematic animations and transitions
 * - Immersive particle effects
 * - Theater-themed storytelling
 * - Aggressive visual presentation
 * - Premium quality UX
 */

// Phase-dependent colors for dramatic effects
const THEATER_COLORS: Record<string, { primary: string; secondary: string; particle: string }> = {
  scout: {
    primary: "cyan",
    secondary: "blue",
    particle: "cyan",
  },
  security: {
    primary: "emerald",
    secondary: "green",
    particle: "emerald",
  },
  vision: {
    primary: "purple",
    secondary: "pink",
    particle: "purple",
  },
  graph: {
    primary: "amber",
    secondary: "orange",
    particle: "amber",
  },
  judge: {
    primary: "rose",
    secondary: "pink",
    particle: "rose",
  },
};

function TheaterAuditPageContent({ id }: { id: string }) {
  const searchParams = useSearchParams();
  const url = searchParams.get("url") || undefined;
  const tier = searchParams.get("tier") || undefined;
  const store = useAuditStream(id, url, tier);
  const [showOverlay, setShowOverlay] = useState(true);
  const [theaterView, setTheaterView] = useState(true);

  const particleColor = store.currentPhase
    ? THEATER_COLORS[store.currentPhase]?.primary || "cyan"
    : "cyan";

  // Get current agent colors
  const getCurrentAgentColors = () => {
    if (store.currentPhase && store.currentPhase !== "init") {
      return THEATER_COLORS[store.currentPhase] || THEATER_COLORS.scout;
    }
    return THEATER_COLORS.scout;
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
      {/* Immersive Particle Background */}
      <ParticleField color={particleColor} particleCount={50} />

      {/* Main Content */}
      <main className="relative z-10 pt-8 px-4 lg:px-6 pb-4 max-w-[1800px] mx-auto">
        {/* Theater Header */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-8"
        >
          <motion.h1
            className="text-5xl font-bold tracking-tight mb-2"
            animate={{
              scale: [1, 1.05, 1],
              textShadow: "0 0 40px rgba(34, 211, 238, 0.3)",
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-500 via-pink-500 to-rose-500 bg-300% bg-gradient-to-r">
              🔬 VERITAS
            </span>
            <span className="text-white/50 text-4xl ml-2">THEATER</span>
          </motion.h1>

          <motion.div
            className="text-base text-[var(--v-text-secondary)] tracking-wider"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Autonomous Forensic Web Auditor — Live Agent Performance
          </motion.div>

          {/* Toggle View Button */}
          <motion.button
            onClick={() => setTheaterView(!theaterView)}
            className="mt-4 px-6 py-2 rounded-full bg-white/10 border border-white/20 hover:bg-white/20 hover:border-white/40 transition-all text-sm"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            whileHover={{ scale: 1.05 }}
          >
            {theaterView ? "🎭 Theater View" : "📊 Dashboard View"}
          </motion.button>
        </motion.div>

        {/* Toggle Content Based on View Mode */}
        <AnimatePresence mode="wait">
          {theaterView ? (
            <TheaterLayout
              store={store}
              url={store.url}
              auditId={store.auditId}
              elapsed={store.stats.elapsed_seconds}
              setShowOverlay={setShowOverlay}
            />
          ) : (
            <DashboardLayout
              store={store}
              url={store.url}
              auditId={store.auditId}
              elapsed={store.stats.elapsed_seconds}
              setShowOverlay={setShowOverlay}
            />
          )}
        </AnimatePresence>
      </main>

      {/* Completion Overlay */}
      <AnimatePresence>
        {store.status === "complete" && store.result && showOverlay && (
          <CompletionOverlay
            trustScore={store.result.trust_score}
            riskLevel={store.result.risk_level}
            auditId={id}
            onDismiss={() => setShowOverlay(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Theater View - Immersive stage-based presentation
 */
function TheaterLayout({
  store,
  url,
  auditId,
  elapsed,
  setShowOverlay,
}: TheaterLayoutProps & { setShowOverlay: (v: boolean) => void }) {
  const [showTrustReveal, setShowTrustReveal] = useState(false);

  // Automatically show trust reveal when audit completes
  useEffect(() => {
    if (store.status === "complete" && store.result?.trust_score) {
      setShowTrustReveal(true);
    }
  }, [store.status, store.result]);

  const currentAgentColors = getCurrentAgentColors();

  return (
    <div className="space-y-6">
      {/* Hero Section - Dramatic Entrance */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        className="glass-card rounded-2xl p-8 border border-white/10 backdrop-blur-md relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-purple-500/5 to-pink-500/5 opacity-20 animate-gradient" />

        <div className="relative z-10 text-center">
          <motion.div
            className="text-6xl mb-4"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 10 }}
          >
            {trustRevealStore(store.status, store.status === "complete") ?
              "⭐" : "🎭"}
          </motion.div>

          <motion.div
            className="text-2xl font-semibold text-[var(--v-text)] mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            The {store.status === "running" ? "Performance is Live!" : "Final Verdict"}
          </motion.div>

          {store.url && (
            <motion.a
              href={store.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300 text-sm mt-2 block truncate max-w-md mx-auto"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              {store.url}
            </motion.a>
          )}

          {store.status === "running" && (
            <motion.div
              className="mt-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
            >
              <div className="inline-flex items-center gap-2">
                <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" />
                <span className="text-sm text-cyan-400">
                  Agents are performing their analysis...
                </span>
              </div>
            </motion.div>
          )}
        </div>

        {/* Trust Score Reveal - Dramatic Presentation */}
        {showTrustReveal && store.result && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, type: "spring", stiffness: 200 }}
          >
            <TrustScoreReveal
              trustScore={store.result.trust_score}
              riskLevel={store.result.risk_level}
              greenFlags={store.result.green_flags}
              verdict={store.result.narrative}
            />
          </motion.div>
        )}
      </motion.div>

      {/* Agent Theater Stage */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.3 }}
        className="glass-card rounded-2xl border border-white/10 backdrop-blur-md"
      >
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="p-6 border-b border-white/10"
        >
          <h3 className="text-xl font-bold text-[var(--v-text)] mb-2">
            🎭 Live Agent Performance
          </h3>
          <p className="text-sm text-[var(--v-text-secondary)]">
            Watch our autonomous agents perform forensic analysis in real-time
          </p>
        </motion.div>

        <div className="p-6 min-h-[400px]">
          <AnimatedAgentTheater
            phases={store.phases}
            currentPhase={store.currentPhase}
            trustScore={store.result?.trust_score}
          />
        </div>
      </motion.div>

      {/* Narrative Feed - Stories from the Agents */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.4 }}
        className="glass-card rounded-2xl border border-white/10 backdrop-blur-md"
      >
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="p-6 border-b border-white/10"
        >
          <h3 className="text-xl font-bold text-[var(--v-text)] mb-2">
            📜 Agent Stories
          </h3>
          <p className="text-sm text-[var(--v-text-secondary)]">
            Real-time updates and discoveries
          </p>
        </motion.div>

        <div className="p-6 min-h-[300px]">
          <NarrativeFeed
            currentPhase={store.currentPhase}
            findings={store.findings}
            screenshots={store.screenshots}
            logs={store.logs}
            status={store.status}
            trustScore={store.result?.trust_score}
            greenFlags={store.result?.green_flags}
          />
        </div>
      </motion.div>

      {/* Bottom Section - Running Log + Evidence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="glass-card rounded-2xl border border-white/10 backdrop-blur-md"
        >
          <div className="p-6 border-b border-white/10">
            <h3 className="text-lg font-bold text-[var(--v-text)] mb-2">
              🎭 Performance Log
            </h3>
          </div>
          <div className="p-4">
            <ForensicLog logs={store.logs} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.6 }}
          className="glass-card rounded-2xl border border-white/10 backdrop-blur-md"
        >
          <div className="p-6 border-b border-white/10">
            <h3 className="text-lg font-bold text-[var(--v-text)] mb-2">
              🔬 Evidence Gallery
            </h3>
          </div>
          <div className="p-4">
            <EvidencePanel
              screenshots={store.screenshots}
              findings={store.findings}
              stats={store.stats}
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
}

/**
 * Dashboard View - Traditional audit presentation
 */
function DashboardLayout({
  store,
  url,
  auditId,
  elapsed,
  setShowOverlay,
}: DashboardLayoutProps & { setShowOverlay: (v: boolean) => void }) {
  return (
    <div className="space-y-6">
      {/* Hero with trust score reveal */}
      {store.result && store.result.trust_score && (
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="glass-card rounded-2xl border border-white/10 backdrop-blur-md p-8"
        >
          <TrustScoreReveal
            trustScore={store.result.trust_score}
            riskLevel={store.result.risk_level}
            greenFlags={store.result.green_flags}
            verdict={store.result.narrative}
          />
        </motion.div>
      )}

      {/* Three-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_320px] gap-6 mb-6">
        {/* Left: Agent Pipeline */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1 }}
          className="glass-card rounded-2xl border border-white/10 backdrop-blur-md p-6"
        >
          <h3 className="text-lg font-bold text-[var(--v-text)] mb-4">
            Pipeline Status
          </h3>
          <div className="space-y-3">
            {(Object.entries(store.phases) as [Phase, PhaseState][]).map(([phase, state]) => (
              <div
                key={phase}
                className={`flex items-center gap-3 p-3 rounded-lg border ${
                  state.status === "active"
                    ? "border-cyan-500/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/10"
                    : state.status === "complete"
                      ? "border-emerald-500/30 bg-emerald-500/10"
                      : state.status === "error"
                        ? "border-red-500/30 bg-red-500/10"
                        : "border-white/10 hover:border-white/20"
                } transition-all duration-300`}
              >
                <div className={`text-2xl ${state.status === "complete" ? "" : state.status === "error" ? "" : "animate-pulse"}`}>
                  {state.status === "complete" ? "✅" : state.status === "error" ? "❌" : PHASE_META[phase]?.icon || "⏳"}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-[var(--v-text)] capitalize">{phase}</div>
                  {state.message && (
                    <div className="text-xs text-[var(--v-text-secondary)] mt-0.5">{state.message}</div>
                  )}
                </div>
                {state.pct > 0 && (
                  <div className="w-16 h-1.5 bg-white/20 rounded-full">
                    <motion.div
                      className="h-full bg-gradient-to-r from-cyan-500 to-purple-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${state.pct}%` }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>

        {/* Center: Narrative Feed */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="glass-card rounded-2xl border border-white/10 backdrop-blur-md min-h-[500px]"
        >
          <div className="p-6 border-b border-white/10">
            <h3 className="text-lg font-bold text-[var(--v-text)] mb-2">
              📜 Audit Progress
            </h3>
          </div>
          <div className="p-4">
            <NarrativeFeed
              currentPhase={store.currentPhase}
              findings={store.findings}
              screenshots={store.screenshots}
              logs={store.logs}
              status={store.status}
              trustScore={store.result?.trust_score}
              greenFlags={store.result?.green_flags}
            />
          </div>
        </motion.div>

        {/* Right: Evidence Panel */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, delay:0.4 }}
          className="glass-card rounded-2xl border border-white/10 backdrop-blur-md"
        >
          <EvidencePanel
            screenshots={store.screenshots}
            findings={store.findings}
            stats={store.stats}
          />
        </motion.div>
      </div>

      {/* Bottom: Forensic Log */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.6 }}
        className="glass-card rounded-2xl border border-white/10 backdrop-blur-md"
      >
        <ForensicLog logs={store.logs} />
      </motion.div>
    </div>
  );
}

// Helper function for trust reveal timing
function trustRevealStore(status: string, isComplete: boolean): boolean {
  return status === "complete" || isComplete;
}

// Gradient animation for shimmer effect
const gradientStyle = `
  @keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  .animate-gradient {
    animation: gradient 8s ease infinite;
    background-size: 400% 400%;
  }
`;

export default function TheaterAuditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-cyan-500" />
      </div>
    }>
      <TheaterAuditPageContent id={id} />
    </Suspense>
  );
}

"use client";

import { useAuditStore } from "@/lib/store";
import type { Phase, PhaseState } from "@/lib/types";
import { AGENT_PERSONALITIES, getPersonalityMessage } from "@/config/agent_personalities";
import { PHASE_META } from "@/lib/types";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef } from "react";

interface AnimatedAgentTheaterProps {
  phases: Record<Phase, PhaseState>;
  currentPhase: Phase | null;
  trustScore?: number;
}

/**
 * AnimatedAgentTheater - The "Out Theater" experience
 *
 * A dramatic stage-like presentation where each agent performs their role with:
 * - Spotlight effects for active agent
 * - Cinematic entrance/exit animations
 * - Stage position-based layout
 * - Personality-driven messaging
 * - Dramatic progress visualization
 */
export function AnimatedAgentTheater({ phases, currentPhase, trustScore = 0 }: AnimatedAgentTheaterProps) {
  const store = useAuditStore();
  const containerRef = useRef<HTMLDivElement>(null);

  // Theater layout: agents positioned on a stage
  const THEATER_POSITIONS: Record<Phase, { x: number; y: number; scale: number }> = {
    scout: { x: 20, y: 60, scale: 1 },      // Left stage
    security: { x: 100, y: 60, scale: 1 },  // Center left
    vision: { x: 180, y: 60, scale: 1 },  // Center
    graph: { x: 260, y: 60, scale: 1 },   // Center right
    judge: { x: 340, y: 60, scale: 1 },    // Right stage
  };

  // Calculate active agent spotlight
  const spotlightAgent = currentPhase && currentPhase !== "init" ? currentPhase : null;

  // Determine theater theme based on phase
  const theaterTheme = useMemo(() => {
    if (!currentPhase || currentPhase === "init") return "dark";
    return AGENT_PERSONALITIES[currentPhase as Exclude<Phase, "init">]?.color || "cyan";
  }, [currentPhase]);

  // Background particle effect based on trust score
  const particleIntensity = useMemo(() => {
    if (trustScore >= 80) return 50;
    if (trustScore >= 60) return 30;
    if (trustScore >= 40) return 20;
    return 10;
  }, [trustScore]);

  return (
    <div className="relative h-full min-h-[300px] flex flex-col">
      {/* Theater Stage Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="text-center mb-6"
      >
        <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 animate-gradient bg-300% bg-gradient-to-r">
          🔬 VERITAS AGENT THEATER
        </h2>
        <motion.div
          className="text-xs text-[var(--v-text-tertiary)] tracking-widest"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          LIVE AUTONOMOUS AUDIT EXPERIENCE
        </motion.div>
      </motion.div>

      {/* Main Theater Stage */}
      <div
        ref={containerRef}
        className="relative flex-1 overflow-hidden perspective-1000"
        style={{
          transformStyle: "preserve-3d",
        }}
      >
        {/* Animated Background */}
        <motion.div
          className="absolute inset-0 pointer-events-none"
          animate={{
            backgroundColor: [
              "rgba(15, 23, 42, 0.3)",
              "rgba(34, 20, 50, 0.2)",
              "rgba(15, 23, 42, 0.3)",
            ],
          }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Stage Floor */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ duration: 1, delay: 0.3 }}
          className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[90%] h-1 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"
          style={{ transformOrigin: "center" }}
        />

        {/* Spotlight Effect */}
        <AnimatePresence>
          {spotlightAgent && (
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{
                opacity: [0.3, 0.6, 0.3],
                scale: [1.5, 1.8, 1.5],
              }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              className="absolute pointer-events-none"
              style={{
                left: `${THEATER_POSITIONS[spotlightAgent].x}%`,
                top: `${THEATER_POSITIONS[spotlightAgent].y}%`,
                transform: "translate(-50%, -50%)",
              }}
            >
              <div
                className="w-32 h-32 rounded-full bg-gradient-radial from-cyan-500/30 via-purple-500/20 to-transparent"
                style={{
                  filter: "blur(20px)",
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Agents on Stage */}
        {(Object.entries(THEATER_POSITIONS) as [Phase, { x: number; y: number; scale: number }][]).map(([phase, pos]) => {
          const state = phases[phase];
          const persona = phase !== "init" ? AGENT_PERSONALITIES[phase as Exclude<Phase, "init">] : null;
          const isActive = phase === currentPhase;
          const isComplete = state?.status === "complete";
          const isError = state?.status === "error";

          return (
            <motion.div
              key={phase}
              className={`absolute transform-gpu`}
              style={{
                left: `${pos.x}%`,
                top: `${pos.y}%`,
                transform: `translate(-50%, -50%) scale(${pos.scale})`,
              }}
              animate={isActive ? {
                scale: pos.scale * 1.2,
                y: pos.y - 10,
              } : isComplete ? {
                scale: pos.scale * 0.95,
                opacity: 0.7,
                y: pos.y + 5,
              } : {
                scale: pos.scale,
                y: pos.y,
              }}
              transition={{ duration: 0.5, type: "spring", stiffness: 200 }}
            >
              {/* Agent Avatar */}
              <motion.div
                className={`relative w-24 h-24 rounded-2xl flex items-center justify-center text-4xl border-2 transition-all duration-300 ${
                  isActive
                    ? "border-cyan-400 shadow-lg shadow-cyan-500/50 bg-cyan-500/20"
                    : isComplete
                      ? "border-emerald-400 bg-emerald-500/10"
                      : isError
                        ? "border-red-400 bg-red-500/10"
                        : "border-white/10 bg-white/5 hover:border-white/20"
                }`}
                animate={isActive ? {
                  rotate: [0, 5, -5, 0],
                  scale: [1, 1.1, 1.1, 1],
                } : {}}
                transition={{ duration: 2, repeat: isActive ? Infinity : 0 }}
              >
                {persona ? (
                  <>
                    <span className="animate-pulse">{persona.emoji}</span>
                    {isActive && (
                      <motion.div
                        className="absolute inset-0 rounded-2xl border-2 border-cyan-400 animate-ping"
                        transition={{ duration: 1, repeat: Infinity }}
                      />
                    )}
                  </>
                ) : (
                  <span>⚙️</span>
                )}
              </motion.div>

              {/* Agent Name and Status */}
              {phase !== "init" && persona && (
                <motion.div
                  className={`absolute -bottom-8 left-1/2 -translate-x-1/2 text-center w-max ${
                    isActive ? "text-cyan-400" : "text-[var(--v-text-secondary)]"
                  }`}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <div className="text-[10px] font-semibold">{persona.name}</div>
                  <div className="text-[8px] capitalize opacity-75">
                    {state?.status === "active" ? "PERFORMING" : state?.status?.toLowerCase()}
                  </div>
                  {isActive && state?.message && (
                    <motion.div
                      className="text-[8px] mt-1"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      transition={{ delay: 0.3 }}
                    >
                      {state.message}
                    </motion.div>
                  )}
                  {isComplete && (
                    <div className="text-[8px] mt-1 text-emerald-400">✓ COMPLETE</div>
                  )}
                </motion.div>
              )}

              {/* Completion Effect */}
              <AnimatePresence>
                {isComplete && (
                  <motion.div
                    className="absolute inset-0 rounded-2xl"
                    initial={{ scale: 0, opacity: 1 }}
                    animate={{ scale: 2, opacity: 0 }}
                    exit={{ scale: 2, opacity: 0 }}
                    transition={{ duration: 1 }}
                  >
                    <div className="w-full h-full rounded-2xl border-2 border-emerald-400" />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      {/* Theater Progress Bar - Dramatic Bottom Bar */}
      <motion.div
        className="mt-6 h-1 bg-white/10 rounded-full overflow-hidden"
        initial={{ width: 0 }}
        animate={{ width: `${store.pct}%` }}
        transition={{ duration: 0.8, ease: "circOut" }}
      >
        <motion.div
          className="h-full bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500"
          animate={{
            backgroundPosition: ["0%", "100%", "0%"],
          }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          style={{
            backgroundSize: "200% 100%",
          }}
        />
      </motion.div>

      {/* Current Personality Message - Featured Large Display */}
      {spotlightAgent && spotlightAgent !== "init" && currentPhase !== "init" && (
        <motion.div
          key={`personality-${spotlightAgent}`}
          className="mt-4 text-center"
          initial={{ opacity: 0, scale: 0.8, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8, y: -20 }}
          transition={{ duration: 0.6 }}
        >
          <motion.div
            className={`text-2xl font-bold inline-block px-4 py-2 rounded-lg ${
              theaterTheme === "cyan"
                ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                : theaterTheme === "purple"
                ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                : theaterTheme === "emerald"
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-pink-500/20 text-pink-400 border border-pink-500/30"
            }`}
          >
            <motion.span
              className="inline-block mr-2"
              animate={{ rotate: [0, 10, -10, 0], scale: [1, 1.2, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              {AGENT_PERSONALITIES[spotlightAgent as Exclude<Phase, "init">]?.emoji}
            </motion.span>
            {getPersonalityMessage(spotlightAgent, "active")}
          </motion.div>
        </motion.div>
      )}

      {/* Trust Score Teaser - Dramatic Reveal */}
      {trustScore > 0 && (
        <motion.div
          className="mt-4 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <motion.div
            className="text-sm text-[var(--v-text-tertiary)]"
            animate={{
              opacity: [0.5, 1, 0.5],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            Analyzing evidence and computing trust score...
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}

// Gradient animation for background
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

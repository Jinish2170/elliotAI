"use client";

import { motion } from "framer-motion";
import type { Phase, PhaseState } from "@/lib/types";
import { PHASE_META } from "@/lib/types";

interface AgentCardProps {
  phase: Phase;
  state: PhaseState;
  isActive: boolean;
}

const STATUS_STYLES = {
  waiting: "border-white/10 border-dashed",
  active: "border-cyan-500/60 shadow-[0_0_20px_rgba(6,182,212,0.15)]",
  complete: "border-emerald-500/40",
  error: "border-red-500/40",
};

export function AgentCard({ phase, state, isActive }: AgentCardProps) {
  const meta = PHASE_META[phase];
  if (!meta || phase === "init") return null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`relative rounded-xl border p-3 transition-all duration-500 ${STATUS_STYLES[state.status]} ${
        isActive ? "bg-[var(--v-surface)]" : "bg-[var(--v-deep)]"
      }`}
    >
      {/* Active glow */}
      {state.status === "active" && (
        <div className="absolute inset-0 rounded-xl bg-cyan-500/5 animate-pulse" />
      )}

      <div className="relative flex items-center gap-3">
        {/* Icon */}
        <div className={`text-xl flex-shrink-0 ${state.status === "active" ? "animate-pulse" : ""}`}>
          {state.status === "complete" ? "✅" : state.status === "error" ? "❌" : meta.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-[var(--v-text)] truncate">{meta.label}</h4>
            <StatusPill status={state.status} />
          </div>

          {/* Progress bar */}
          {state.status === "active" && (
            <div className="mt-1.5 h-1 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-purple-500"
                initial={{ width: "0%" }}
                animate={{ width: `${Math.min(state.pct, 100)}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          )}

          {/* Summary when complete */}
          {state.status === "complete" && state.message && (
            <p className="text-[10px] text-[var(--v-text-tertiary)] mt-1 truncate">
              {state.message}
            </p>
          )}

          {/* Error message */}
          {state.status === "error" && state.error && (
            <p className="text-[10px] text-red-400 mt-1 truncate">{state.error}</p>
          )}
        </div>
      </div>

      {/* Connector line */}
      {phase !== "judge" && (
        <div className="absolute left-5 -bottom-4 w-px h-4 bg-gradient-to-b from-white/10 to-transparent" />
      )}
    </motion.div>
  );
}

function StatusPill({ status }: { status: string }) {
  const cfg: Record<string, { bg: string; text: string; label: string }> = {
    waiting: { bg: "bg-white/5", text: "text-[var(--v-text-tertiary)]", label: "Waiting" },
    active: { bg: "bg-cyan-500/10", text: "text-cyan-400", label: "Active" },
    complete: { bg: "bg-emerald-500/10", text: "text-emerald-400", label: "Done" },
    error: { bg: "bg-red-500/10", text: "text-red-400", label: "Error" },
  };
  const c = cfg[status] || cfg.waiting;
  return (
    <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  );
}

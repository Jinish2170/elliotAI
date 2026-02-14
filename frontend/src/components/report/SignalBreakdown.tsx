"use client";

import { SignalBar } from "@/components/data-display/SignalBar";
import { SignalRadarChart } from "@/components/data-display/SignalRadarChart";
import { motion } from "framer-motion";

const SIGNAL_META: Record<string, { label: string; icon: string }> = {
  visual: { label: "Visual Intelligence", icon: "👁️" },
  structural: { label: "Page Structure", icon: "🔍" },
  temporal: { label: "Time Analysis", icon: "⏱️" },
  graph: { label: "Identity Verification", icon: "🌐" },
  meta: { label: "Basic Verification", icon: "🔒" },
  security: { label: "Security Audit", icon: "🛡️" },
};

interface SignalBreakdownProps {
  scores: Record<string, number>;
}

export function SignalBreakdown({ scores }: SignalBreakdownProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.1 }}
      className="glass-card rounded-2xl p-8 mb-6"
    >
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold mb-6">
        Signal Breakdown
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Radar chart */}
        <div>
          <SignalRadarChart scores={scores} />
        </div>

        {/* Signal bars */}
        <div className="space-y-4 flex flex-col justify-center">
          {Object.entries(SIGNAL_META).map(([key, meta], i) => (
            <SignalBar
              key={key}
              label={meta.label}
              icon={meta.icon}
              score={scores[key] ?? 0}
              delay={i * 0.1}
            />
          ))}
        </div>
      </div>
    </motion.section>
  );
}

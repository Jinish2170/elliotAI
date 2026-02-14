"use client";

import { motion } from "framer-motion";

interface RecommendationsProps {
  recommendations: string[];
}

const PRIORITY_ICONS: Record<number, { icon: string; color: string; label: string }> = {
  0: { icon: "🔴", color: "border-red-500/30", label: "HIGH" },
  1: { icon: "🔴", color: "border-red-500/30", label: "HIGH" },
  2: { icon: "🟡", color: "border-amber-500/30", label: "MEDIUM" },
  3: { icon: "🟡", color: "border-amber-500/30", label: "MEDIUM" },
  4: { icon: "🟢", color: "border-emerald-500/30", label: "LOW" },
};

export function Recommendations({ recommendations }: RecommendationsProps) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.5 }}
      className="glass-card rounded-2xl p-8 mb-6"
    >
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold mb-6">
        Recommendations
      </h2>

      <div className="space-y-3">
        {recommendations.map((rec, i) => {
          const priority = PRIORITY_ICONS[Math.min(i, 4)];
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
              className={`flex items-start gap-3 p-3 rounded-xl border ${priority.color} bg-white/[0.02]`}
            >
              <span className="text-lg flex-shrink-0 mt-0.5">{priority.icon}</span>
              <div>
                <span className="text-[9px] font-bold tracking-wider text-[var(--v-text-tertiary)]">
                  {priority.label}
                </span>
                <p className="text-sm text-[var(--v-text-secondary)] mt-0.5">{rec}</p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.section>
  );
}

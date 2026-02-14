"use client";

import { motion } from "framer-motion";

interface SignalBarProps {
  label: string;
  score: number;
  icon?: string;
  delay?: number;
}

function getBarColor(score: number): string {
  if (score >= 80) return "from-emerald-500 to-emerald-400";
  if (score >= 60) return "from-cyan-500 to-cyan-400";
  if (score >= 40) return "from-amber-500 to-amber-400";
  if (score >= 20) return "from-orange-500 to-orange-400";
  return "from-red-500 to-red-400";
}

export function SignalBar({ label, score, icon, delay = 0 }: SignalBarProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-[var(--v-text-secondary)] flex items-center gap-2">
          {icon && <span>{icon}</span>}
          {label}
        </span>
        <span className="text-sm font-mono font-bold text-[var(--v-text)] tabular-nums">
          {score}/100
        </span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, delay, ease: [0.4, 0, 0.2, 1] }}
          className={`h-full rounded-full bg-gradient-to-r ${getBarColor(score)}`}
        />
      </div>
    </div>
  );
}

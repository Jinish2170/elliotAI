"use client";

import { motion } from "framer-motion";
import Link from "next/link";

interface CompletionOverlayProps {
  trustScore: number;
  riskLevel: string;
  auditId: string;
  onDismiss: () => void;
}

export function CompletionOverlay({ trustScore, riskLevel, auditId, onDismiss }: CompletionOverlayProps) {
  const color =
    trustScore >= 90
      ? "#10B981"
      : trustScore >= 70
      ? "#06B6D4"
      : trustScore >= 40
      ? "#F59E0B"
      : trustScore >= 20
      ? "#F97316"
      : "#EF4444";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onDismiss}
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="glass-card rounded-2xl p-8 text-center max-w-sm mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Celebration for safe sites */}
        {trustScore >= 85 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
            className="text-5xl mb-4"
          >
            🎉
          </motion.div>
        )}

        <h2 className="text-xl font-bold text-[var(--v-text)] mb-2">Audit Complete</h2>

        <motion.div
          initial={{ scale: 0.5 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-6xl font-bold font-mono mb-1"
          style={{ color }}
        >
          {trustScore}
        </motion.div>
        <p className="text-xs text-[var(--v-text-tertiary)] mb-1">/100 Trust Score</p>
        <p className="text-sm font-semibold mb-6" style={{ color }}>
          {riskLevel.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
        </p>

        <Link
          href={`/report/${auditId}`}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm text-white transition-all animate-shimmer"
          style={{
            background: `linear-gradient(135deg, ${color}, #8B5CF6)`,
          }}
        >
          View Full Report →
        </Link>
      </motion.div>
    </motion.div>
  );
}

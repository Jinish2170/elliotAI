"use client";

import confetti from "canvas-confetti";
import type { GreenFlag } from "@/lib/types";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, X, Sparkles } from "lucide-react";
import { useEffect, useMemo } from "react";

interface GreenFlagCelebrationProps {
  trustScore: number;
  greenFlags: GreenFlag[];
  onDismiss?: () => void;
}

export function GreenFlagCelebration({ trustScore, greenFlags, onDismiss }: GreenFlagCelebrationProps) {
  // Only display if trustScore >= 80
  if (trustScore < 80) return null;

  // Trigger confetti on mount
  useEffect(() => {
    const triggerConfetti = () => {
      confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 },
        colors: ["#10B981", "#06B6D4", "#8B5CF6", "#34D399"],
        disableForReducedMotion: true,
        resize: true,
        useWorker: true,
      } as any);
    };

    // Initial confetti burst
    const timeout1 = setTimeout(triggerConfetti, 300);

    // Second burst after delay
    const timeout2 = setTimeout(() => {
      confetti({
        particleCount: 100,
        spread: 90,
        origin: { y: 0.5 },
        colors: ["#10B981", "#06B6D4", "#8B5CF6"],
        disableForReducedMotion: true,
      } as any);
    }, 1200);

    return () => {
      clearTimeout(timeout1);
      clearTimeout(timeout2);
    };
  }, []);

  // Re-trigger confetti function (for replay button if needed)
  const reTriggerConfetti = () => {
    confetti({
      particleCount: 120,
      spread: 100,
      origin: { y: 0.7 },
      colors: ["#10B981", "#06B6D4", "#8B5CF6", "#34D399"],
      disableForReducedMotion: true,
    } as any);
  };

  // Group green flags by category
  const groupedFlags = useMemo(() => {
    const groups: Record<string, GreenFlag[]> = {
      security: [],
      privacy: [],
      compliance: [],
      trust: [],
    };
    greenFlags.forEach((flag) => {
      groups[flag.category].push(flag);
    });
    return groups;
  }, [greenFlags]);

  // Category color mapping
  const categoryColors: Record<GreenFlag["category"], string> = {
    security: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    privacy: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    compliance: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    trust: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  };

  return (
    <motion.div
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: -100, opacity: 0 }}
      transition={{ type: "spring", damping: 20, stiffness: 300 }}
      className="glass-card rounded-xl overflow-hidden border-2 border-emerald-500/30 shadow-lg shadow-emerald-500/10"
    >
      {/* Banner Header */}
      <div className="bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 px-6 py-4 border-b border-emerald-500/20">
        <div className="flex items-start justify-between">
          <div className="text-center flex-1">
            <motion.div
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 300 }}
              className="text-3xl mb-1"
            >
              🎉
            </motion.div>
            <motion.h3
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-lg font-bold text-emerald-400 mb-1"
            >
              Congratulations!
            </motion.h3>
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="flex items-center justify-center gap-2 mb-2"
            >
              <motion.span
                className="text-4xl font-bold font-mono text-emerald-400"
                animate={{
                  scale: [1, 1.1, 1],
                  textShadow: [
                    "0 0 20px rgba(16, 185, 129, 0.5)",
                    "0 0 30px rgba(16, 185, 129, 0.8)",
                    "0 0 20px rgba(16, 185, 129, 0.5)",
                  ],
                }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                {trustScore}
              </motion.span>
              <span className="text-sm text-emerald-400/80 mt-2">/ 100 Trust Score</span>
            </motion.div>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="text-sm text-emerald-300/90"
            >
              This site appears trustworthy!
            </motion.p>
          </div>
          {onDismiss && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              onClick={onDismiss}
              className="text-white/60 hover:text-white transition-colors"
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </motion.button>
          )}
        </div>
      </div>

      {/* Green Flags Grid */}
      <div className="p-4 space-y-3">
        {greenFlags.length > 0 ? (
          <div className="space-y-3">
            {/* Security flags */}
            {groupedFlags.security.length > 0 && (
              <FlagGroup
                title="Security"
                color="emerald"
                flags={groupedFlags.security}
                categoryColors={categoryColors}
              />
            )}

            {/* Privacy flags */}
            {groupedFlags.privacy.length > 0 && (
              <FlagGroup
                title="Privacy"
                color="cyan"
                flags={groupedFlags.privacy}
                categoryColors={categoryColors}
              />
            )}

            {/* Compliance flags */}
            {groupedFlags.compliance.length > 0 && (
              <FlagGroup
                title="Compliance"
                color="purple"
                flags={groupedFlags.compliance}
                categoryColors={categoryColors}
              />
            )}

            {/* Trust flags */}
            {groupedFlags.trust.length > 0 && (
              <FlagGroup
                title="Trust"
                color="blue"
                flags={groupedFlags.trust}
                categoryColors={categoryColors}
              />
            )}
          </div>
        ) : (
          <p className="text-sm text-[var(--v-text-tertiary)] text-center py-4">
            No specific green flags detected, but overall trust score is high.
          </p>
        )}

        {/* Replay confetti button */}
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          onClick={reTriggerConfetti}
          className="w-full mt-2 py-2 px-4 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-400 text-sm font-medium transition-all flex items-center justify-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          Celebrate Again
        </motion.button>
      </div>
    </motion.div>
  );
}

// Flag group component for organized display
interface FlagGroupProps {
  title: string;
  color: string;
  flags: GreenFlag[];
  categoryColors: Record<GreenFlag["category"], string>;
}

function FlagGroup({ title, color, flags, categoryColors }: FlagGroupProps) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle2 className={`w-4 h-4 text-${color}-400`} />
        <span className="text-xs font-semibold text-[var(--v-text)] uppercase tracking-wider">
          {title}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {flags.map((flag, idx) => {
          const categoryColor = categoryColors[flag.category];
          return (
            <motion.div
              key={flag.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + idx * 0.08 }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${categoryColor}`}
            >
              <span className="text-lg">{flag.icon}</span>
              <span className="text-xs font-medium text-[var(--v-text)]">{flag.label}</span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

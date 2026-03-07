"use client";

import { AnimatePresence, motion } from "framer-motion";
import confetti from "canvas-confetti";
import type { GreenFlag } from "@/lib/types";
import { COMMON_GREEN_FLAGS } from "@/lib/types";
import { useEffect, useState } from "react";

interface TrustScoreRevealProps {
  trustScore: number;
  riskLevel: string;
  greenFlags?: GreenFlag[];
  verdict?: string;
}

/**
 * TrustScoreReveal - Dramatic cinematic trust score reveal animation
 *
 * Features:
 * - Multi-stage dramatic countdown
 * - Particle explosion on reveal
 * - Color-coded tier reveal based on score
 * - Green flag celebration for high scores
 * - Shimmer/glow effects
 */
export function TrustScoreReveal({
  trustScore,
  riskLevel,
  greenFlags = [],
  verdict,
}: TrustScoreRevealProps) {
  const [isRevealed, setIsRevealed] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);

  // Trigger reveal on mount
  useEffect(() => {
    const timer = setTimeout(() => setIsRevealed(true), 500);
    return () => clearTimeout(timer);
  }, []);

  // Confetti for high scores
  useEffect(() => {
    if (isRevealed && trustScore >= 80 && !showConfetti) {
      setShowConfetti(true);

      // Initial burst
      confetti({
        particleCount: 150,
        spread: 90,
        origin: { y: 0.6 },
        colors: ["#10B981", "#06B6D4", "#8B5CF6", "#EFB815"],
        disableForReducedMotion: true,
        resize: true,
        useWorker: true,
      });

      // Second burst after delay
      setTimeout(() => {
        confetti({
          particleCount: 100,
          spread: 120,
          origin: { y: 0.4 },
          colors: ["#10B981", "#06B6D4", "#8B5CF6"],
          disableForReducedMotion: true,
        });
      }, 1500);

      // Third celebration burst
      setTimeout(() => {
        confetti({
          particleCount: 80,
          spread: 100,
          origin: { y: 0.5 },
          angles: [30, 60, 90, 120, 150],
          colors: ["#10B981", "#06B6D4", "#EFB815"],
          disableForReducedMotion: true,
        });
      }, 3000);
    }
  }, [isRevealed, trustScore, showConfetti]);

  // Determine score tier and styling
  const scoreTier = useMemo(() => {
    if (trustScore >= 90) return { tier: "Exceptional", color: "from-emerald-400 to-cyan-400", emoji: "🏆", bgClass: "bg-gradient-to-r from-emerald-500/20" };
    if (trustScore >= 80) return { tier: "Excellent", color: "from-emerald-400 to-green-400", emoji: "🎉", bgClass: "bg-gradient-to-r from-green-500/20" };
    if (trustScore >= 70) return { tier: "Good", color: "from-cyan-400 to-blue-400", emoji: "✅", bgClass: "bg-gradient-to-r from-cyan-500/20" };
    if (trustScore >= 50) return { tier: "Moderate", color: "from-amber-400 to-orange-400", emoji: "⚠️", bgClass: "bg-gradient-to-r from-amber-500/20" };
    if (trustScore >= 30) return { tier: "Low", color: "from-orange-400 to-red-400", emoji: "🚨", bgClass: "bg-gradient-to-r from-orange-500/20" };
    return { tier: "Very Low", color: "from-red-500 to-pink-500", emoji: "⛔", bgClass: "bg-gradient-to-r from-red-500/20" };
  }, [trustScore]);

  const tier = scoreTier;

  // Count up animation
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    if (isRevealed) {
      const duration = 2000; // 2 seconds countdown
      const startValue = 0;
      const endValue = trustScore;
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function for dramatic effect
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = Math.floor(startValue + (endValue - startValue) * easeOutQuart);

        setDisplayScore(current);

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          setDisplayScore(endValue);
        }
      };

      requestAnimationFrame(animate);
    }
  }, [isRevealed, trustScore]);

  return (
    <div className="relative py-8 px-4 text-center">
      {/* Dramatic Stage Entrance */}
      <AnimatePresence mode="wait">
        {!isRevealed ? (
          <motion.div
            key="countdown"
            className="text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="inline-block w-20 h-20 rounded-full border-2 border-cyan-500/50"
              animate={{
                scale: [0.8, 1, 0.8],
                borderColor: ["rgba(34, 211, 238, 0.5)", "rgba(34, 211, 238, 0.2)", "rgba(34, 211, 238, 0.5)"],
              }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              <motion.div
                className="w-full h-full rounded-full bg-cyan-500/20 animate-ping"
                style={{
                  animationDelay: "0.5s",
                  animationDuration: "1s",
                }}
              />
            </motion.div>
            <motion.p
              className="text-lg text-cyan-400 mt-4"
              animate={{
                opacity: [0.5, 1, 0.5],
              }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              Computing final verdict...
            </motion.p>
          </motion.div>
        ) : (
          <motion.div
            key="reveal"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, type: "spring", stiffness: 200, damping: 20 }}
          >
            {/* Score Container with Dramatic Background */}
            <motion.div
              className={`inline-block relative px-12 py-8 rounded-3xl ${tier.bgClass} border-2 backdrop-blur-md`}
              animate={{
                borderColor: [
                  "rgba(255, 255, 255, 0.1)",
                  "rgba(255, 255, 255, 0.3)",
                  "rgba(255, 255, 255, 0.1)",
                ],
              }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{
                transform: "perspective(1000px) rotateX(0deg)",
                backgroundSize: "200% 100%",
              }}
            >
              {/* Tier Label */}
              <motion.div
                className={`text-xs uppercase tracking-widest mb-2 font-bold ${tier.color.split(" ")[0]}`}
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                FINAL VERDICT
              </motion.div>

              {/* Dramatic Score Number */}
              <motion.div className="relative mb-4">
                {/* Glow Effect */}
                <motion.div
                  className={`absolute inset-0 rounded-full ${tier.color.split(" ")[0]} animate-blur-lg`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0.3, 0.6, 0.3] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />

                {/* Score Number */}
                <motion.div
                  className={`relative text-7xl font-black font-mono bg-gradient-to-r ${tier.color} bg-clip-text text-transparent ${
                    trustScore >= 80 ? "animate-shimmer" : ""
                  }`}
                  style={{
                    textShadow: trustScore >= 80
                      ? "0 0 30px rgba(16, 185, 129, 0.5), 0 0 60px rgba(16, 185, 129, 0.3)"
                      : "",
                  }}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.4, type: "spring", stiffness: 300, damping: 15 }}
                >
                  {displayScore}
                </motion.div>

                <motion.span className="text-4xl font-bold text-[var(--v-text)] opacity-50">
                  /100
                </motion.span>

                {/* Tier Label */}
                <motion.div
                  className={`text-2xl font-bold ${tier.color.split(" ")[0]} ml-2 inline-block`}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.6 }}
                >
                  {tier.tier}
                </motion.div>
              </motion.div>

              {/* Risk Level */}
              <motion.div
                className={`text-sm uppercase tracking-wider mt-2 ${
                  trustScore < 50 ? "text-red-400" : trustScore < 70 ? "text-amber-400" : "text-[var(--v-text-secondary)]"
                }`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
              >
                Risk: {riskLevel.replace(/_/g, " ").toUpperCase()}
              </motion.div>

              {/* Trust Score Badge */}
              {trustScore >= 70 && (
                <motion.div
                  className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm"
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 1 }}
                >
                  <span className="text-green-400 font-semibold">TRUSTWORTHY</span>
                  {trustScore >= 90 && <span className="text-8xl">💎</span>}
                </motion.div>
              )}
            </motion.div>

            {/* Verdict Text */}
            {verdict && (
              <motion.p
                className="mt-4 text-sm text-[var(--v-text-secondary)] max-w-md mx-auto italic"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.2 }}
              >
                "{verdict}"
              </motion.p>
            )}

            {/* Green Flags Celebration */}
            {trustScore >= 80 && greenFlags.length > 0 && (
              <motion.div
                className="mt-6"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.5 }}
              >
                <motion.div
                  className="flex items-center justify-center gap-2 mb-3"
                >
                  <span className="text-2xl">✨</span>
                  <span className="text-sm font-semibold text-emerald-400">Positive Indicators Detected</span>
                </motion.div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {greenFlags.map((flag, idx) => (
                    <motion.div
                      key={flag.id}
                      className={`px-3 py-2 rounded-lg border text-center text-xs ${
                        flag.category === "security"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : flag.category === "privacy"
                            ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/30"
                            : flag.category === "compliance"
                              ? "bg-purple-500/20 text-purple-400 border-purple-500/30"
                              : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                      }`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1.6 + idx * 0.1 }}
                    >
                      <div className="text-lg mb-1">{flag.icon}</div>
                      <div className="font-medium text-[var(--v-text)]">{flag.label}</div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

"use client";

/* ========================================
   VerdictReveal — 3-Second Overlay Sequence
   Institutional verdict: dim → count-up → classification → CTA.
   No confetti. Click/ESC dismisses instantly.
   ======================================== */

import { cn } from "@/lib/utils";
import { getVerdictLabel, getVerdictLevel, VERDICT_COLORS } from "@/config/agents";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

interface VerdictRevealProps {
  trustScore: number;
  riskLevel: string;
  auditId: string;
  onDismiss: () => void;
}

type RevealPhase = "dim" | "label" | "counting" | "stamp" | "cta" | "done";

export function VerdictReveal({
  trustScore,
  riskLevel,
  auditId,
  onDismiss,
}: VerdictRevealProps) {
  const [phase, setPhase] = useState<RevealPhase>("dim");
  const [displayScore, setDisplayScore] = useState(0);
  const rafRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  // Score color
  const verdictLevel = getVerdictLevel(trustScore);
  const verdictLabel = getVerdictLabel(trustScore);
  const verdictColor = VERDICT_COLORS[verdictLevel]?.text || "#F59E0B";

  // Reduced motion check
  const prefersReducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Timed sequence
  useEffect(() => {
    if (prefersReducedMotion) {
      setDisplayScore(trustScore);
      setPhase("done");
      return;
    }

    const timers: ReturnType<typeof setTimeout>[] = [];

    // T=0.5s — "ANALYSIS COMPLETE" label
    timers.push(setTimeout(() => setPhase("label"), 500));

    // T=1.0s — Start score count-up
    timers.push(
      setTimeout(() => {
        setPhase("counting");
        startTimeRef.current = performance.now();

        const countDuration = Math.min(trustScore * 8, 800); // max 800ms

        const tick = (now: number) => {
          const elapsed = now - startTimeRef.current;
          const progress = Math.min(elapsed / countDuration, 1);
          const current = Math.round(progress * trustScore);
          setDisplayScore(current);

          if (progress < 1) {
            rafRef.current = requestAnimationFrame(tick);
          } else {
            setDisplayScore(trustScore);
            // T=2.0s — Classification stamp
            setTimeout(() => setPhase("stamp"), 200);
            // T=2.5s — CTA
            setTimeout(() => setPhase("cta"), 700);
            // T=3.0s — Done
            setTimeout(() => setPhase("done"), 1200);
          }
        };

        rafRef.current = requestAnimationFrame(tick);
      }, 1000)
    );

    return () => {
      timers.forEach(clearTimeout);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [trustScore, prefersReducedMotion]);

  // Dismiss on ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDismiss();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onDismiss]);

  const showLabel = phase !== "dim";
  const showScore = ["counting", "stamp", "cta", "done"].includes(phase);
  const showStamp = ["stamp", "cta", "done"].includes(phase);
  const showCta = ["cta", "done"].includes(phase);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center cursor-pointer"
      onClick={onDismiss}
      role="dialog"
      aria-label="Audit verdict"
    >
      {/* Backdrop — dims all panels */}
      <div
        className={cn(
          "absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity duration-500",
          phase === "dim" ? "opacity-0" : "opacity-100"
        )}
      />

      {/* Content */}
      <div
        className="relative z-10 flex flex-col items-center gap-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* "ANALYSIS COMPLETE" */}
        <div
          className={cn(
            "transition-all duration-500",
            showLabel
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-2"
          )}
        >
          <span className="text-[16px] font-mono font-semibold tracking-[0.12em] text-[var(--v-text-secondary)]">
            ANALYSIS COMPLETE
          </span>
        </div>

        {/* Score counter */}
        <div
          className={cn(
            "transition-all duration-300",
            showScore
              ? "opacity-100 scale-100"
              : "opacity-0 scale-90"
          )}
        >
          <span
            className="text-[72px] font-mono font-bold leading-none tabular-nums"
            style={{ color: verdictColor }}
          >
            {displayScore}
          </span>
          <div className="text-center mt-1">
            <span className="text-[12px] font-mono text-[var(--v-text-tertiary)]">
              /100 TRUST SCORE
            </span>
          </div>
        </div>

        {/* Classification stamp */}
        <div
          className={cn(
            "transition-all duration-300",
            showStamp
              ? "opacity-100 scale-100"
              : "opacity-0 scale-[0.8]"
          )}
        >
          <div
            className="px-6 py-2 rounded-md border-2 font-mono font-bold text-[18px] tracking-[0.1em]"
            style={{
              borderColor: verdictColor,
              color: verdictColor,
              boxShadow: `0 0 30px ${verdictColor}40`,
            }}
          >
            {verdictLabel}
          </div>
        </div>

        {/* CTA */}
        <div
          className={cn(
            "transition-all duration-300 mt-4",
            showCta
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-4"
          )}
        >
          <Link
            href={`/report/${auditId}`}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-md font-mono font-semibold text-[13px] text-white transition-all hover:brightness-110"
            style={{
              background: verdictColor,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            VIEW FULL REPORT →
          </Link>
        </div>

        {/* Dismiss hint */}
        <span className="text-[10px] font-mono text-[var(--v-text-tertiary)] mt-6">
          Click anywhere or press ESC to dismiss
        </span>
      </div>
    </div>
  );
}

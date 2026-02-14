"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface TrustGaugeProps {
  score: number; // 0-100
  size?: number;
  animate?: boolean;
}

function getColor(score: number): string {
  if (score >= 90) return "#10B981";
  if (score >= 70) return "#06B6D4";
  if (score >= 40) return "#F59E0B";
  if (score >= 20) return "#F97316";
  return "#EF4444";
}

function getLabel(score: number): string {
  if (score >= 90) return "Trusted";
  if (score >= 70) return "Probably Safe";
  if (score >= 40) return "Suspicious";
  if (score >= 20) return "High Risk";
  return "Likely Fraudulent";
}

export function TrustGauge({ score, size = 200, animate = true }: TrustGaugeProps) {
  const [displayScore, setDisplayScore] = useState(animate ? 0 : score);
  const color = getColor(score);
  const label = getLabel(score);

  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  // Use 270 degree arc (3/4 circle)
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - (arcLength * (displayScore / 100));

  useEffect(() => {
    if (!animate) {
      setDisplayScore(score);
      return;
    }

    const startTime = performance.now();
    const duration = 1500;

    const tick = (now: number) => {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplayScore(Math.round(score * eased));
      if (t < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  }, [score, animate]);

  const cx = size / 2;
  const cy = size / 2;

  return (
    <div className="relative inline-flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background arc */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={10}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform={`rotate(135 ${cx} ${cy})`}
        />

        {/* Score arc */}
        <motion.circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform={`rotate(135 ${cx} ${cy})`}
          style={{
            filter: `drop-shadow(0 0 8px ${color}40)`,
            transition: "stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        />
      </svg>

      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold font-mono tabular-nums" style={{ color }}>
          {displayScore}
        </span>
        <span className="text-xs text-[var(--v-text-tertiary)]">/100</span>
      </div>

      {/* Label below */}
      <div
        className="mt-[-10px] text-sm font-semibold"
        style={{ color }}
      >
        {label}
      </div>
    </div>
  );
}

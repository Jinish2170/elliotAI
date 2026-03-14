"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";

export function VerdictPanel({
  verdict,
  trustScore,
}: {
  verdict: Record<string, any> | null;
  trustScore: number | undefined;
}) {
  if (!verdict && trustScore === undefined) {
    return <GhostPanel message="AWAITING VERDICT STREAM..." />;
  }

  const score = trustScore ?? (verdict?.verdict_technical?.trust_score || 0);
  const isHighRisk = score < 40;
  const isMedium = score >= 40 && score < 70;
  const colorClass = isHighRisk
    ? "text-[var(--t-red)] glow-text-red"
    : isMedium
    ? "text-[var(--t-amber)] glow-text-amber"
    : "text-[var(--t-green)] glow-text-green";

  const riskLevel =
    verdict?.verdict_technical?.risk_level?.toUpperCase() ||
    (isHighRisk ? "CRITICAL RISK" : isMedium ? "MODERATE RISK" : "NOMINAL");

  const summaryStr =
    verdict?.verdict_nontechnical?.executive_summary ||
    "Awaiting continuous synthesis...";

  return (
    <div className="flex w-full h-full p-4 items-center justify-center gap-6">
      {/* SCORE BLOCK */}
      <div className="flex flex-col items-center min-w-[120px]">
        <div className="text-[var(--t-dim)] text-[10px] uppercase mb-1 tracking-widest">
          [ TRUST_IDX ]
        </div>
        <div className={`text-[72px] font-bold leading-none ${colorClass}`}>
          {score.toFixed(1)}
        </div>
        <div className={`text-[12px] font-bold mt-1 ${colorClass} tracking-widest`}>
          {riskLevel}
        </div>
      </div>

      {/* SUMMARY BLOCK */}
      <div className="flex-1 flex flex-col pl-6 border-l border-[var(--t-border)] h-full justify-center">
        <div className="text-[var(--t-dim)] text-[10px] uppercase mb-2 tracking-widest shrink-0">
          [ EXEC.SUMMARY_SYNTHESIS ]
        </div>
        <div className="text-[12px] leading-relaxed text-[var(--t-text)] overflow-y-auto pr-2" style={{ maxHeight: "80%" }}>
          {summaryStr}
        </div>
      </div>
    </div>
  );
}

"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { DarkPatternFinding, TemporalFinding } from "@/lib/types";

interface Props {
  darkPatterns: DarkPatternFinding[];
  temporal: TemporalFinding[];
  status?: string;
}

export function VisionIntelligence({ darkPatterns, temporal, status }: Props) {
  const isEmpty = !darkPatterns?.length && !temporal?.length;
  if (isEmpty) {
    if (status === "complete") {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-[var(--t-green)]/5">
          <span className="text-[var(--t-green)]/50 font-mono text-[10px] uppercase tracking-widest">[ NO DECEPTIVE UX DETECTED ]</span>
        </div>
      );
    }
    return <GhostPanel message="VISION ACTIVE - MONITORING DECEPTIVE UX" />;
  }

  return (
    <div className="w-full h-full overflow-y-auto p-3 flex flex-row gap-4 align-top items-start">
      {/* Dark Patterns Column */}
      <div className="flex-1 flex flex-col gap-2 min-w-0">
        <div className="text-[10px] text-[var(--t-red)] border-b border-[var(--t-red)] pb-1 shrink-0">
          DARK_PATTERNS <span className="opacity-70">[{darkPatterns?.length || 0}]</span>
        </div>
        <div className="flex flex-col gap-1 overflow-y-auto pr-1">
          {!darkPatterns?.length && <span className="text-[10px] text-[var(--t-dim)]">NO DATA</span>}
          {darkPatterns?.map((dp, i) => (
            <div key={i} className="text-[10px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-red)] shrink-0">
              <span className="font-bold">{dp.pattern_type.toUpperCase()}</span>
              <span className="opacity-70 truncate">{dp.evidence}</span>
              <span className="text-[var(--t-amber)] mt-1">CONF: {Math.round(dp.confidence * 100)}% | SEV: {dp.severity.toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Temporal Findings Column */}
      <div className="flex-1 flex flex-col gap-2 min-w-0 border-l border-[var(--t-border)] pl-4">
        <div className="text-[10px] text-[var(--t-amber)] border-b border-[var(--t-amber)] pb-1 shrink-0">
          TEMPORAL_FINDINGS <span className="opacity-70">[{temporal?.length || 0}]</span>
        </div>
        <div className="flex flex-col gap-1 overflow-y-auto pr-1">
          {!temporal?.length && <span className="text-[10px] text-[var(--t-dim)]">NO DATA</span>}
          {temporal?.map((t, i) => (
            <div key={i} className="text-[10px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-amber)] shrink-0">
              <span className="font-bold text-[var(--t-amber)]">{t.finding_type.toUpperCase()}</span>
              <span className="opacity-70 truncate">{t.explanation}</span>
              <span className="text-[var(--t-dim)] mt-1">T0: {t.value_at_t0} &rarr; +{t.delta_seconds}s: {t.value_at_t_delay}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

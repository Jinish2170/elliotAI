"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { DarkPatternFinding, TemporalFinding } from "@/lib/types";

interface Props {
  darkPatterns: DarkPatternFinding[];
  temporal: TemporalFinding[];
  status?: string;
  /** Latest per-page progress line from the Vision agent, if any. */
  progress?: string;
  aiCalls?: number;
  phase?: string | null;
}

// The five families the vision model checks every analysed page for
// (elliot/config/dark_patterns.py → DARK_PATTERN_TAXONOMY).
const CATEGORIES = [
  ["Visual interference", "hidden cancel buttons, misleading click targets, disguised ads"],
  ["False urgency", "fake countdowns, fake scarcity, fake expiring offers"],
  ["Forced continuity", "hidden cancellation, confirmshaming, forced sign-up"],
  ["Sneaking", "hidden costs, pre-selected add-ons, bait and switch"],
  ["Fake trust", "fake reviews, fake badges, fake authority claims"],
];

export function VisionIntelligence({ darkPatterns, temporal, status, progress, aiCalls, phase }: Props) {
  const isEmpty = !darkPatterns?.length && !temporal?.length;
  if (isEmpty) {
    const done = status === "complete";
    const visionStarted = done || !!progress || ["vision", "graph", "judge"].includes(phase || "");
    if (!visionStarted) return <GhostPanel message="WAITING FOR SCOUT SCREENSHOTS" />;
    return (
      <div className="w-full h-full overflow-y-auto p-3 font-mono text-[11px]">
        <div className={done ? "text-[var(--t-green)] font-bold mb-1" : "text-[var(--t-amber)] font-bold mb-1"}>
          {done ? "No manipulative design found" : "Vision AI is checking each page for:"}
        </div>
        {(progress || done) && (
          <div className="text-[10px] text-[var(--t-dim)] mb-2">
            {progress || `Analysis complete${aiCalls ? ` · ${aiCalls} AI calls` : ""}.`}
          </div>
        )}
        <div className="flex flex-col gap-1">
          {CATEGORIES.map(([name, examples]) => (
            <div key={name} className="flex gap-2 items-start">
              <span className={done ? "text-[var(--t-green)]" : "text-[var(--t-amber)] animate-pulse"}>{done ? "✓" : "…"}</span>
              <span>
                <span className="text-[var(--t-text)]">{name}</span>
                <span className="text-[var(--t-dim)]"> · {examples}</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-y-auto p-3 flex flex-row gap-4 align-top items-start">
      {/* Dark Patterns Column */}
      <div className="flex-1 flex flex-col gap-2 min-w-0">
        <div className="text-[11px] text-[var(--t-red)] border-b border-[var(--t-red)] pb-1 shrink-0">
          DARK_PATTERNS <span className="opacity-70">[{darkPatterns?.length || 0}]</span>
        </div>
        <div className="flex flex-col gap-1 overflow-y-auto pr-1">
          {!darkPatterns?.length && <span className="text-[11px] text-[var(--t-dim)]">NO DATA</span>}
          {darkPatterns?.map((dp, i) => (
            <div key={i} className="text-[11px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-red)] shrink-0">
              <span className="font-bold">{dp.pattern_type.toUpperCase()}</span>
              <span className="opacity-70 truncate">{dp.evidence}</span>
              <span className="text-[var(--t-amber)] mt-1">CONF: {Math.round(dp.confidence * 100)}% | SEV: {dp.severity.toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Temporal Findings Column */}
      <div className="flex-1 flex flex-col gap-2 min-w-0 border-l border-[var(--t-border)] pl-4">
        <div className="text-[11px] text-[var(--t-amber)] border-b border-[var(--t-amber)] pb-1 shrink-0">
          TEMPORAL_FINDINGS <span className="opacity-70">[{temporal?.length || 0}]</span>
        </div>
        <div className="flex flex-col gap-1 overflow-y-auto pr-1">
          {!temporal?.length && <span className="text-[11px] text-[var(--t-dim)]">NO DATA</span>}
          {temporal?.map((t, i) => (
            <div key={i} className="text-[11px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-amber)] shrink-0">
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

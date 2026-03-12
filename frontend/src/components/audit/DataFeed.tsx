"use client";

/* ========================================
   DataFeed — Structured Typed Entries
   Replaces chat-like NarrativeFeed with structured,
   Bloomberg-style data entries with severity stripes.
   ======================================== */

import { cn } from "@/lib/utils";
import { FindingRow } from "@/components/audit/FindingRow";
import { AGENT_CONFIGS, type AgentId } from "@/config/agents";
import type { Finding, Phase, LogEntry, Screenshot } from "@/lib/types";
import { useMemo, useRef, useEffect } from "react";

interface DataFeedProps {
  currentPhase: Phase | null;
  findings: Finding[];
  screenshots: Screenshot[];
  logs: LogEntry[];
  status: string;
  className?: string;
}

type FeedEntry =
  | { kind: "phase"; phase: Phase; ts: number }
  | { kind: "finding"; data: Finding; ts: number }
  | { kind: "screenshot"; data: Screenshot; ts: number }
  | { kind: "system"; message: string; level: "info" | "warn" | "error"; ts: number };

export function DataFeed({
  currentPhase,
  findings,
  screenshots,
  logs,
  status,
  className,
}: DataFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null);

  // Build unified, chronological feed from all data sources
  const entries = useMemo<FeedEntry[]>(() => {
    const items: FeedEntry[] = [];

    // Track phases from logs
    const seenPhases = new Set<string>();
    logs.forEach((log, i) => {
      // Phase transitions
      if (log.agent && !seenPhases.has(log.agent) && 
          ["scout", "security", "vision", "graph", "judge"].includes(log.agent.toLowerCase())) {
        const phase = log.agent.toLowerCase() as Phase;
        seenPhases.add(phase);
        items.push({ kind: "phase", phase, ts: i * 100 });
      }
    });

    // Findings
    findings.forEach((f, i) => {
      items.push({ kind: "finding", data: f, ts: 50000 + i * 10 });
    });

    // Screenshots
    screenshots.forEach((ss, i) => {
      items.push({ kind: "screenshot", data: ss, ts: 30000 + i * 10 });
    });

    // Sort by insertion order (timestamp proxy)
    items.sort((a, b) => a.ts - b.ts);
    return items;
  }, [findings, screenshots, logs]);

  // Auto-scroll
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [entries.length]);

  const isEmpty = entries.length === 0;

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div
        ref={feedRef}
        className="flex-1 overflow-y-auto space-y-1 pr-1 scrollbar-thin"
      >
        {isEmpty && status !== "complete" && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-8 h-8 rounded-lg bg-[rgba(255,255,255,0.04)] flex items-center justify-center mb-3">
              <div className="w-2 h-2 rounded-full bg-[var(--agent-primary)] animate-pulse" />
            </div>
            <p className="text-[12px] text-[var(--v-text-tertiary)] font-mono">
              AWAITING DATA STREAM...
            </p>
          </div>
        )}

        {entries.map((entry, i) => {
          switch (entry.kind) {
            case "phase":
              return <PhaseMarker key={`phase-${entry.phase}`} phase={entry.phase} />;
            case "finding":
              return (
                <FindingRow
                  key={entry.data.id || `finding-${i}`}
                  severity={entry.data.severity === "critical" ? "critical" : entry.data.severity === "high" ? "high" : entry.data.severity === "medium" ? "medium" : "low"}
                  title={entry.data.pattern_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  description={entry.data.plain_english || entry.data.description}
                  agent={entry.data.category}
                  checkType={entry.data.pattern_type}
                  index={i}
                />
              );
            case "screenshot":
              return (
                <ScreenshotEntry
                  key={`ss-${entry.data.index}`}
                  label={entry.data.label || entry.data.url}
                  index={entry.data.index}
                  hasData={!!entry.data.data}
                />
              );
            default:
              return null;
          }
        })}

        {status === "complete" && (
          <div className="flex items-center gap-2 px-3 py-2 mt-2 rounded bg-[rgba(16,185,129,0.08)] border border-[rgba(16,185,129,0.2)]">
            <div className="w-2 h-2 rounded-full bg-[var(--v-safe)]" />
            <span className="text-[11px] font-mono text-[var(--v-safe)]">
              ANALYSIS COMPLETE — ALL AGENTS FINISHED
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Phase marker ── */

function PhaseMarker({ phase }: { phase: Phase }) {
  const agent = phase as AgentId;
  const config = AGENT_CONFIGS[agent];
  const PIPELINE_PHASES: Phase[] = ["scout", "security", "vision", "graph", "judge"];
  const phaseNum = PIPELINE_PHASES.indexOf(phase) + 1;

  return (
    <div className="flex items-center gap-2 py-2 px-1">
      <div className="h-[1px] flex-1 bg-[rgba(255,255,255,0.06)]" />
      <div className="flex items-center gap-1.5">
        <div
          className="w-1.5 h-1.5 rounded-full"
          style={{ background: config?.color.primary || "#06B6D4" }}
        />
        <span
          className="text-[9px] font-mono font-semibold tracking-[0.12em] uppercase"
          style={{ color: config?.color.primary || "#06B6D4" }}
        >
          PHASE {phaseNum} · {phase.toUpperCase()}
        </span>
      </div>
      <div className="h-[1px] flex-1 bg-[rgba(255,255,255,0.06)]" />
    </div>
  );
}

/* ── Screenshot entry ── */

function ScreenshotEntry({
  label,
  index,
  hasData,
}: {
  label: string;
  index: number;
  hasData: boolean;
}) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-[rgba(139,92,246,0.04)] border border-[rgba(139,92,246,0.1)]">
      <span className="text-[10px] font-mono text-[var(--v-purple)]">📸</span>
      <span className="text-[11px] font-mono text-[var(--v-text-secondary)] truncate flex-1">
        Screenshot #{index + 1}: {label}
      </span>
      {hasData && (
        <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
          CAPTURED
        </span>
      )}
    </div>
  );
}

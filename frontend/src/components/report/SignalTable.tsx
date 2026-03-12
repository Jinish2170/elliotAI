"use client";

/* ========================================
   SignalTable — Table-based Signal Analysis
   Score vs. threshold columns with pass/fail status.
   Replaces card-based SignalBreakdown.
   ======================================== */

import { cn } from "@/lib/utils";
import { PanelChrome } from "@/components/layout/PanelChrome";
import { CheckCircle2, XCircle } from "lucide-react";

interface Signal {
  name: string;
  score: number;
  threshold?: number;
  detail?: string;
}

interface SignalTableProps {
  signals: Signal[];
  className?: string;
}

const DEFAULT_THRESHOLD = 60;

export function SignalTable({ signals, className }: SignalTableProps) {
  const belowCount = signals.filter(
    (s) => s.score < (s.threshold ?? DEFAULT_THRESHOLD)
  ).length;

  return (
    <PanelChrome
      title="Signal Analysis"
      count={signals.length}
      elevation={2}
      className={className}
      titleActions={
        <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
          {belowCount} of {signals.length} below threshold
        </span>
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[rgba(255,255,255,0.06)]">
              <th className="text-left px-4 py-2 text-data-label">SIGNAL</th>
              <th className="text-right px-4 py-2 text-data-label w-[80px]">SCORE</th>
              <th className="text-right px-4 py-2 text-data-label w-[80px]">THRESHOLD</th>
              <th className="text-center px-4 py-2 text-data-label w-[60px]">STATUS</th>
              <th className="text-left px-4 py-2 text-data-label">DETAIL</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((signal) => {
              const threshold = signal.threshold ?? DEFAULT_THRESHOLD;
              const pass = signal.score >= threshold;

              return (
                <tr
                  key={signal.name}
                  className="border-b border-[rgba(255,255,255,0.03)] hover:bg-[rgba(255,255,255,0.02)] transition-colors"
                >
                  <td className="px-4 py-2 text-[13px] text-[var(--v-text)]">
                    {signal.name}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {/* Mini bar */}
                      <div className="w-16 h-1.5 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(signal.score, 100)}%`,
                            background: pass ? "#10B981" : signal.score < 30 ? "#EF4444" : "#F59E0B",
                          }}
                        />
                      </div>
                      <span className="text-[13px] font-mono font-bold text-[var(--v-text)] tabular-nums w-8 text-right">
                        {signal.score}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-right text-[12px] font-mono text-[var(--v-text-tertiary)] tabular-nums">
                    {threshold}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {pass ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[var(--v-safe)]">
                        <CheckCircle2 className="w-3 h-3" /> PASS
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[var(--v-danger)]">
                        <XCircle className="w-3 h-3" /> FAIL
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-[12px] text-[var(--v-text-secondary)] max-w-[200px] truncate">
                    {signal.detail || "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </PanelChrome>
  );
}

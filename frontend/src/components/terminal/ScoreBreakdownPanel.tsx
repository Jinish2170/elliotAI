"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { ScoreBreakdown } from "@/lib/types";

/* Answers "why X and not 100?" with the exact arithmetic the backend used.
   Lost points are split into two different stories for the reader:
   "found a problem" vs "could not verify" (no evidence either way). */

const LABEL: Record<string, string> = {
  graph: "Background check",
  visual: "Manipulative design",
  security: "Security setup",
  structural: "Page structure",
  meta: "Domain records",
  temporal: "Fake timers",
};

const pts = (n: number) => (Math.round(n * 10) / 10).toFixed(1);

export function ScoreBreakdownPanel({ breakdown, status }: { breakdown?: ScoreBreakdown | null; status?: string }) {
  if (!breakdown?.signals?.length) {
    return (
      <GhostPanel
        message={status === "complete" ? "NO SCORE BREAKDOWN FOR THIS AUDIT (RUN BEFORE THIS FEATURE)" : "AWAITING VERDICT"}
      />
    );
  }

  const rows = [...breakdown.signals].sort(
    (a, b) => b.lost_to_findings + b.lost_to_uncertainty - (a.lost_to_findings + a.lost_to_uncertainty)
  );
  const found = rows.reduce((s, r) => s + r.lost_to_findings, 0);
  const unverified = rows.reduce((s, r) => s + r.lost_to_uncertainty, 0);
  const rules = breakdown.overrides.reduce((s, o) => s + o.points, 0);

  return (
    <div className="w-full h-full overflow-y-auto p-3 font-mono text-[11px] text-[var(--t-text)]">
      <div className="mb-2">
        <span className="text-[13px] font-bold">
          Why {breakdown.final_score}, not 100
        </span>
        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
          <span className="text-[var(--t-red)]">−{pts(found)} problems found</span>
          <span className="text-[var(--t-amber)]">−{pts(unverified)} could not verify</span>
          {rules > 0 && <span className="text-[var(--t-red)]">−{rules} safety rules</span>}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {rows.map((r) => {
          const lost = r.lost_to_findings + r.lost_to_uncertainty;
          const earnedPct = r.max_points ? (r.earned_points / r.max_points) * 100 : 0;
          const foundPct = r.max_points ? (r.lost_to_findings / r.max_points) * 100 : 0;
          return (
            <div key={r.signal}>
              <div className="flex justify-between gap-2">
                <span className="font-bold">{LABEL[r.signal] ?? r.signal}</span>
                <span className="whitespace-nowrap">
                  {pts(r.earned_points)} / {pts(r.max_points)}
                  {lost >= 0.05 && <span className="text-[var(--t-dim)]"> (−{pts(lost)})</span>}
                </span>
              </div>
              {/* earned | lost to findings | lost to uncertainty */}
              <div className="mt-1 flex h-[6px] w-full gap-[2px] bg-transparent">
                <div style={{ width: `${earnedPct}%` }} className="bg-[var(--t-green)] rounded-l-[3px]" />
                {foundPct > 0 && <div style={{ width: `${foundPct}%` }} className="bg-[var(--t-red)]" />}
                <div className="flex-1 bg-[var(--t-amber)]/40 rounded-r-[3px]" />
              </div>
              {r.reason && <div className="mt-1 text-[10px] text-[var(--t-dim)] leading-snug">{r.reason}</div>}
            </div>
          );
        })}
      </div>

      {breakdown.overrides.length > 0 && (
        <div className="mt-3 border-t border-[var(--t-border)] pt-2">
          {breakdown.overrides.map((o) => (
            <div key={o.name} className="text-[10px]">
              <span className="text-[var(--t-red)] font-bold">−{o.points}</span> {o.description}
            </div>
          ))}
        </div>
      )}

      <div className="mt-3 border-t border-[var(--t-border)] pt-2 text-[10px] text-[var(--t-dim)] leading-relaxed">
        Each check is worth a fixed share of 100. A problem found costs points in proportion to how sure we are.
        A check we could not verify costs {Math.round((1 - breakdown.prior) * 100)}% of its share: unknown is not
        proof of safety. The score is computed by code from this evidence, not by an AI model.
      </div>
    </div>
  );
}

"use client";

/* ========================================
   RecentAudits — Recent Audit History Table
   Shows last few audits if available in
   localStorage. Table layout with inline
   score indicators.
   ======================================== */

import { PanelChrome } from "@/components/layout/PanelChrome";
import { getVerdictLevel, VERDICT_COLORS } from "@/config/agents";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

interface AuditRecord {
  id: string;
  url: string;
  score: number;
  riskLevel: string;
  date: string;
  tier: string;
}

const STORAGE_KEY = "veritas_recent_audits";

export function RecentAudits() {
  const [audits, setAudits] = useState<AuditRecord[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setAudits(JSON.parse(stored));
      }
    } catch {
      // silently handle
    }
  }, []);

  if (audits.length === 0) {
    return (
      <PanelChrome title="Recent Audits" elevation={2}>
        <div className="text-center py-8">
          <p className="text-[12px] text-[var(--v-text-tertiary)]">
            No recent audits. Start one above.
          </p>
        </div>
      </PanelChrome>
    );
  }

  return (
    <PanelChrome title="Recent Audits" count={audits.length} elevation={2}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[rgba(255,255,255,0.06)]">
              <th className="text-left px-3 py-2 text-data-label">URL</th>
              <th className="text-right px-3 py-2 text-data-label w-[70px]">SCORE</th>
              <th className="text-left px-3 py-2 text-data-label w-[90px]">RISK</th>
              <th className="text-left px-3 py-2 text-data-label w-[80px]">TIER</th>
              <th className="text-left px-3 py-2 text-data-label w-[120px]">DATE</th>
              <th className="w-[40px]" />
            </tr>
          </thead>
          <tbody>
            {audits.map((audit) => {
              const level = getVerdictLevel(audit.score);
              const colors = VERDICT_COLORS[level];

              return (
                <tr
                  key={audit.id}
                  className="border-b border-[rgba(255,255,255,0.03)] hover:bg-[rgba(255,255,255,0.02)] transition-colors"
                >
                  <td className="px-3 py-2">
                    <span className="text-[13px] font-mono text-[var(--v-text)] truncate block max-w-[300px]">
                      {audit.url}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {/* Mini score bar */}
                      <div className="w-10 h-1.5 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min(audit.score, 100)}%`,
                            background: colors.text,
                          }}
                        />
                      </div>
                      <span
                        className="text-[13px] font-mono font-bold tabular-nums w-6 text-right"
                        style={{ color: colors.text }}
                      >
                        {audit.score}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className="text-[10px] font-mono font-bold uppercase"
                      style={{ color: colors.text }}
                    >
                      {audit.riskLevel}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-[11px] font-mono text-[var(--v-text-tertiary)]">
                    {audit.tier.replace(/_/g, " ")}
                  </td>
                  <td className="px-3 py-2 text-[11px] font-mono text-[var(--v-text-tertiary)]">
                    {audit.date}
                  </td>
                  <td className="px-3 py-2">
                    <Link
                      href={`/report/${audit.id}`}
                      className="p-1 rounded hover:bg-[rgba(255,255,255,0.05)] text-[var(--v-text-tertiary)] hover:text-[var(--v-text)] transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
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

/** Call this to save an audit record after completion */
export function saveAuditToHistory(record: AuditRecord) {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    const existing: AuditRecord[] = stored ? JSON.parse(stored) : [];
    // Dedupe by id
    const filtered = existing.filter((a) => a.id !== record.id);
    // Prepend (newest first), keep max 20
    const updated = [record, ...filtered].slice(0, 20);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // silently handle
  }
}

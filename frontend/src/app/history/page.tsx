"use client";

import { PanelChrome } from "@/components/layout/PanelChrome";
import { getVerdictLevel, VERDICT_COLORS } from "@/config/agents";
import { ArrowRight, ExternalLink, Search, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AuditHistoryItem {
  audit_id: string;
  url: string;
  status: string;
  audit_tier: string;
  verdict_mode: string;
  trust_score: number | null;
  risk_level: string | null;
  site_type: string | null;
  created_at: string;
}

export default function HistoryPage() {
  const router = useRouter();
  const [audits, setAudits] = useState<AuditHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await fetch(`${API_URL}/api/audits/history?limit=50`);
        if (!res.ok) throw new Error("Failed to fetch history");
        const data = await res.json();
        setAudits(data.audits || []);
      } catch (e) {
        console.error(e);
        setError("Could not load audit history. Ensure backend is running.");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  const toggleSelection = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
      }).format(new Date(dateStr));
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen bg-[var(--v-deep)] pt-16 px-4 lg:px-8 pb-16">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[18px] font-bold text-[var(--v-text)]">Audit History</h1>
            <p className="text-[11px] font-mono text-[var(--v-text-tertiary)]">
              {audits.length} audits recorded
            </p>
          </div>

          {selectedIds.size >= 2 && (
            <button
              onClick={() => {
                const ids = Array.from(selectedIds).join(",");
                router.push(`/compare/${ids}`);
              }}
              className="px-3 py-1.5 rounded text-[11px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/30 hover:bg-purple-500/20 transition-colors"
            >
              COMPARE ({selectedIds.size})
            </button>
          )}
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-5 h-5 border-2 border-[var(--v-text-tertiary)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <PanelChrome title="Error" elevation={2}>
            <div className="flex items-center gap-3 py-4 text-red-400">
              <ShieldAlert className="w-5 h-5" />
              <p className="text-[13px]">{error}</p>
            </div>
          </PanelChrome>
        ) : audits.length === 0 ? (
          <PanelChrome title="History" elevation={2}>
            <div className="text-center py-12">
              <Search className="w-6 h-6 text-[var(--v-text-tertiary)] mx-auto mb-3" />
              <p className="text-[13px] text-[var(--v-text-secondary)] mb-4">No audits found</p>
              <Link
                href="/"
                className="text-[11px] font-mono text-cyan-400 hover:underline"
              >
                START NEW AUDIT →
              </Link>
            </div>
          </PanelChrome>
        ) : (
          <PanelChrome title="Audit Log" count={audits.length} elevation={2}>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[rgba(255,255,255,0.06)]">
                    <th className="w-[32px] px-3 py-2" />
                    <th className="text-left px-3 py-2 text-data-label">TARGET</th>
                    <th className="text-left px-3 py-2 text-data-label w-[80px]">RISK</th>
                    <th className="text-right px-3 py-2 text-data-label w-[70px]">SCORE</th>
                    <th className="text-left px-3 py-2 text-data-label w-[100px]">DATE</th>
                    <th className="text-left px-3 py-2 text-data-label w-[80px]">TIER</th>
                    <th className="w-[40px]" />
                  </tr>
                </thead>
                <tbody>
                  {audits.map((audit) => {
                    const isCompleted = audit.status === "completed";
                    const isSelected = selectedIds.has(audit.audit_id);
                    const score = audit.trust_score;
                    const level = score != null ? getVerdictLevel(score) : null;
                    const colors = level ? VERDICT_COLORS[level] : null;

                    return (
                      <tr
                        key={audit.audit_id}
                        onClick={() =>
                          isCompleted
                            ? router.push(`/report/${audit.audit_id}`)
                            : router.push(`/audit/${audit.audit_id}`)
                        }
                        className={cn(
                          "border-b border-[rgba(255,255,255,0.03)] transition-colors cursor-pointer",
                          isSelected
                            ? "bg-purple-500/5 hover:bg-purple-500/8"
                            : "hover:bg-[rgba(255,255,255,0.02)]",
                          !isCompleted && "opacity-60"
                        )}
                      >
                        {/* Selection checkbox */}
                        <td className="px-3 py-2">
                          <div
                            onClick={(e) => toggleSelection(audit.audit_id, e)}
                            className={cn(
                              "w-4 h-4 rounded-sm border flex items-center justify-center cursor-pointer transition-colors",
                              isSelected
                                ? "bg-purple-500 border-purple-500"
                                : "border-[rgba(255,255,255,0.15)] hover:border-[rgba(255,255,255,0.3)]"
                            )}
                          >
                            {isSelected && (
                              <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                                <path d="M10 3L4.5 8.5L2 6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                            )}
                          </div>
                        </td>

                        {/* URL */}
                        <td className="px-3 py-2">
                          <div className="max-w-[300px]">
                            <span className="text-[13px] font-mono text-[var(--v-text)] truncate block">
                              {audit.url}
                            </span>
                            <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
                              {audit.site_type || "unknown"}
                            </span>
                          </div>
                        </td>

                        {/* Risk */}
                        <td className="px-3 py-2">
                          {isCompleted && colors ? (
                            <span
                              className="text-[10px] font-mono font-bold uppercase"
                              style={{ color: colors.text }}
                            >
                              {audit.risk_level || "—"}
                            </span>
                          ) : (
                            <span className="text-[10px] font-mono text-amber-400">
                              {audit.status}
                            </span>
                          )}
                        </td>

                        {/* Score */}
                        <td className="px-3 py-2 text-right">
                          {score != null && colors ? (
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-8 h-1.5 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden">
                                <div
                                  className="h-full rounded-full"
                                  style={{
                                    width: `${Math.min(score, 100)}%`,
                                    background: colors.text,
                                  }}
                                />
                              </div>
                              <span
                                className="text-[13px] font-mono font-bold tabular-nums"
                                style={{ color: colors.text }}
                              >
                                {score}
                              </span>
                            </div>
                          ) : (
                            <span className="text-[13px] font-mono text-[var(--v-text-tertiary)]">—</span>
                          )}
                        </td>

                        {/* Date */}
                        <td className="px-3 py-2 text-[11px] font-mono text-[var(--v-text-tertiary)]">
                          {formatDate(audit.created_at)}
                        </td>

                        {/* Tier */}
                        <td className="px-3 py-2 text-[10px] font-mono text-[var(--v-text-tertiary)]">
                          {audit.audit_tier.replace(/_/g, " ")}
                        </td>

                        {/* Action */}
                        <td className="px-3 py-2">
                          {isCompleted ? (
                            <ArrowRight className="w-3.5 h-3.5 text-[var(--v-text-tertiary)]" />
                          ) : (
                            <Link
                              href={`/audit/${audit.audit_id}`}
                              onClick={(e) => e.stopPropagation()}
                              className="text-[9px] font-mono text-cyan-400"
                            >
                              LIVE
                            </Link>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </PanelChrome>
        )}
      </div>
    </div>
  );
}

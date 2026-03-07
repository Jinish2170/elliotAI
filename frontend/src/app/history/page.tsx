"use client";

import { motion } from "framer-motion";
import { ArrowRight, Globe, Search, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

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

  // Selection for comparison
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
        setError("Could not load audit history. Ensure Veritas backend is running.");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  const toggleSelection = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newSelection = new Set(selectedIds);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedIds(newSelection);
  };

  const navigateToCompare = () => {
    if (selectedIds.size < 2) return;
    const ids = Array.from(selectedIds).join(",");
    router.push(`/compare/${ids}`);
  };

  const getRiskIcon = (level: string | null) => {
    if (!level) return <ShieldQuestion className="w-5 h-5 text-gray-400" />;
    switch (level.toLowerCase()) {
      case "critical":
      case "high":
        return <ShieldAlert className="w-5 h-5 text-red-500" />;
      case "medium":
        return <ShieldAlert className="w-5 h-5 text-yellow-500" />;
      case "low":
      case "safe":
        return <ShieldCheck className="w-5 h-5 text-green-500" />;
      default:
        return <ShieldQuestion className="w-5 h-5 text-gray-400" />;
    }
  };

  const getRiskColor = (level: string | null) => {
    if (!level) return "text-gray-400";
    switch (level.toLowerCase()) {
      case "critical":
        return "text-red-500 bg-red-500/10 border-red-500/20";
      case "high":
        return "text-orange-500 bg-orange-500/10 border-orange-500/20";
      case "medium":
        return "text-yellow-500 bg-yellow-500/10 border-yellow-500/20";
      case "low":
      case "safe":
        return "text-green-500 bg-green-500/10 border-green-500/20";
      default:
        return "text-gray-400 bg-gray-500/10 border-gray-500/20";
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
      }).format(date);
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-24">
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--v-text)] mb-2">
            Audit History
          </h1>
          <p className="text-[var(--v-text-secondary)]">
            Review past forensic audits and compare changes over time.
          </p>
        </div>

        {/* Compare Action */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: selectedIds.size >= 2 ? 1 : 0.5, y: 0 }}
          className="flex items-center gap-3"
        >
          <span className="text-xs text-[var(--v-text-tertiary)]">
            {selectedIds.size} selected
          </span>
          <button
            onClick={navigateToCompare}
            disabled={selectedIds.size < 2}
            className="px-4 py-2 rounded-lg bg-purple-600/20 text-purple-400 border border-purple-500/30 hover:bg-purple-600/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-medium flex items-center gap-2"
          >
            Compare Audits
            <ArrowRight className="w-4 h-4" />
          </button>
        </motion.div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
        </div>
      ) : error ? (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-xl flex flex-col items-center justify-center text-center">
          <ShieldAlert className="w-8 h-8 mb-4 opacity-80" />
          <p>{error}</p>
        </div>
      ) : audits.length === 0 ? (
        <div className="bg-[var(--v-surface)] border border-white/5 p-12 rounded-xl flex flex-col items-center justify-center text-center">
          <Search className="w-12 h-12 text-[var(--v-text-tertiary)] mb-4" />
          <h3 className="text-xl font-medium text-[var(--v-text)] mb-2">No audits found</h3>
          <p className="text-[var(--v-text-secondary)] mb-6 max-w-md">
            You haven&apos;t run any audits yet, or the database is currently empty.
          </p>
          <Link
            href="/"
            className="px-6 py-3 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/20 transition-all font-medium"
          >
            Start New Audit
          </Link>
        </div>
      ) : (
        <div className="bg-[var(--v-surface)] rounded-xl border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-black/20 text-xs uppercase tracking-wider text-[var(--v-text-tertiary)]">
                  <th className="px-6 py-4 font-medium w-12"></th>
                  <th className="px-6 py-4 font-medium">Target URL</th>
                  <th className="px-6 py-4 font-medium">Risk Level</th>
                  <th className="px-6 py-4 font-medium">Trust Score</th>
                  <th className="px-6 py-4 font-medium">Date</th>
                  <th className="px-6 py-4 font-medium">Tier</th>
                  <th className="px-6 py-4 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {audits.map((audit) => {
                  const isSelected = selectedIds.has(audit.audit_id);
                  const isCompleted = audit.status === "completed";

                  return (
                    <tr
                      key={audit.audit_id}
                      onClick={() => isCompleted && router.push(`/report/${audit.audit_id}`)}
                      className={`
                        group transition-colors
                        ${isCompleted ? "cursor-pointer hover:bg-white/[0.02]" : "opacity-60"}
                        ${isSelected ? "bg-purple-500/5 hover:bg-purple-500/10" : ""}
                      `}
                    >
                      <td className="px-6 py-4">
                        <div
                          onClick={(e) => toggleSelection(audit.audit_id, e)}
                          className={`
                            w-5 h-5 rounded border flex items-center justify-center cursor-pointer transition-colors
                            ${isSelected
                              ? "bg-purple-500 border-purple-500 text-white"
                              : "border-[var(--v-text-tertiary)] group-hover:border-[var(--v-text-secondary)]"
                            }
                          `}
                        >
                          {isSelected && (
                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center flex-shrink-0">
                            <Globe className="w-4 h-4 text-[var(--v-text-secondary)]" />
                          </div>
                          <div className="flex flex-col max-w-[200px] sm:max-w-xs md:max-w-sm">
                            <span className="font-medium text-[var(--v-text)] truncate" title={audit.url}>
                              {audit.url}
                            </span>
                            <span className="text-xs text-[var(--v-text-tertiary)] truncate">
                              {audit.site_type || "Unknown Type"}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {isCompleted ? (
                          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${getRiskColor(audit.risk_level)}`}>
                            {getRiskIcon(audit.risk_level)}
                            <span className="capitalize">{audit.risk_level || "Unknown"}</span>
                          </div>
                        ) : (
                          <span className="text-xs text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded-full border border-yellow-500/20">
                            {audit.status}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {isCompleted ? (
                          <div className="flex items-center gap-2">
                            <div className="font-mono font-medium text-[var(--v-text)]">
                              {audit.trust_score !== null ? audit.trust_score : "--"}
                            </div>
                            <div className="text-xs text-[var(--v-text-tertiary)]">/ 100</div>
                          </div>
                        ) : (
                          <span className="text-[var(--v-text-tertiary)] text-sm">--</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-[var(--v-text-secondary)]">
                          {formatDate(audit.created_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-xs text-[var(--v-text-secondary)] font-mono bg-white/5 px-2 py-1 rounded w-fit capitalize">
                          {audit.audit_tier.replace(/_/g, " ")}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {isCompleted ? (
                          <ArrowRight className="w-4 h-4 text-[var(--v-text-tertiary)] group-hover:text-cyan-400 group-hover:translate-x-1 transition-all inline-block" />
                        ) : (
                          <Link
                            href={`/audit/${audit.audit_id}`}
                            className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                          >
                            View Live
                          </Link>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

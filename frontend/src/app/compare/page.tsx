"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  X,
  Activity,
  Clock,
} from "lucide-react";
import React, { Suspense } from "react";

// Disable static generation
export const dynamic = "force-dynamic";

interface AuditSummary {
  audit_id: string;
  url: string;
  status: string;
  trust_score: number;
  risk_level: string;
  site_type: string;
  created_at: string;
  completed_at: string;
  findings_summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  screenshots_count: number;
}

interface ComparisonResult {
  audits: AuditSummary[];
  trust_score_deltas: Array<{
    from_audit_id: string;
    to_audit_id: string;
    delta: number;
    percentage_change: number | null;
  }>;
  risk_level_changes: Array<{
    from_audit_id: string;
    to_audit_id: string;
    from: string;
    to: string;
  }>;
}

const RISK_COLORS: Record<string, string> = {
  trusted: "text-emerald-500 bg-emerald-500/10",
  probably_safe: "text-cyan-500 bg-cyan-500/10",
  suspicious: "text-amber-500 bg-amber-500/10",
  high_risk: "text-orange-500 bg-orange-500/10",
  likely_fraudulent: "text-red-500 bg-red-500/10",
  unknown: "text-gray-400 bg-gray-500/10",
};

const RISK_ORDER = ["likely_fraudulent", "high_risk", "suspicious", "probably_safe", "trusted"];

const RISK_LABELS: Record<string, string> = {
  trusted: "Trusted",
  probably_safe: "Probably Safe",
  suspicious: "Suspicious",
  high_risk: "High Risk",
  likely_fraudulent: "Likely Fraudulent",
  unknown: "Unknown",
};

function getRiskLevelColor(level: string): string {
  return RISK_COLORS[level] || RISK_COLORS.unknown;
}

function getRiskLevelLabel(level: string): string {
  return RISK_LABELS[level] || level.replace("_", " ");
}

function formatScoreColor(delta: number): string {
  if (delta > 0) return "text-emerald-400";
  if (delta < 0) return "text-red-400";
  return "text-gray-400";
}

function formatDate(isoString: string | null): string {
  if (!isoString) return "N/A";
  return new Date(isoString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AuditComparisonPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[var(--v-deep)] flex items-center justify-center">
        <Activity className="w-8 h-8 text-cyan-500 animate-spin" />
      </div>
    }>
      <AuditComparisonPageContent />
    </Suspense>
  );
}

function AuditComparisonPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [allAudits, setAllAudits] = useState<AuditSummary[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string>("");
  const [expandedPanel, setExpandedPanel] = useState<"audits" | "deltas" | "risks" | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  const idsParam = searchParams.get("ids");

  useEffect(() => {
    setIsMounted(true);
    if (idsParam) {
      const ids = idsParam.split(",").filter(Boolean);
      setSelectedIds(ids);
    }
    fetchAllAudits();
  }, [idsParam]);

  const fetchAllAudits = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/audits/history?limit=100");
      if (!response.ok) throw new Error("Failed to fetch audits");
      const data = await response.json();
      setAllAudits(data.audits || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audits");
    } finally {
      setLoading(false);
    }
  };

  const runComparison = async () => {
    if (selectedIds.length < 2) return;

    setComparing(true);
    setError("");

    try {
      const response = await fetch("/api/audits/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audit_ids: selectedIds }),
      });

      if (!response.ok) throw new Error("Failed to compare audits");

      const data = await response.json();
      setComparison(data);
      setExpandedPanel("deltas");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to compare audits");
    } finally {
      setComparing(false);
    }
  };

  const toggleAuditSelection = useCallback((auditId: string) => {
    if (selectedIds.includes(auditId)) {
      setSelectedIds(selectedIds.filter((id) => id !== auditId));
    } else if (selectedIds.length < 5) {
      setSelectedIds([...selectedIds, auditId]);
    }
  }, [selectedIds]);

  const clearAll = useCallback(() => {
    setSelectedIds([]);
    setComparison(null);
    router.push("/compare");
  }, [router]);

  const removeAudit = useCallback((auditId: string) => {
    setSelectedIds(selectedIds.filter((id) => id !== auditId));
    if (comparison) {
      setComparison(null);
    }
  }, [selectedIds, comparison, router]);

  // During SSR, show loading
  if (!isMounted) {
    return (
      <div className="min-h-screen bg-[var(--v-deep)] flex items-center justify-center">
        <Activity className="w-8 h-8 text-cyan-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--v-deep)]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        {/* Header */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <Link
            href="/history"
            className="inline-flex items-center gap-2 text-sm text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to History
          </Link>

          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white">Audit Comparison</h1>
            <BarChart3 className="w-6 h-6 text-cyan-500" />
          </div>
          <p className="text-[var(--v-text-secondary)] mt-2">
            Compare multiple audits of the same URL to detect changes over time
          </p>
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400"
          >
            {error}
          </motion.div>
        )}

        {/* Selected Audits */}
        {selectedIds.length > 0 && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="mb-6"
          >
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white font-medium">
                  Selected Audits ({selectedIds.length})
                </h3>
                <button
                  onClick={clearAll}
                  className="text-xs text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
                >
                  Clear All
                </button>
              </div>

              <div className="flex flex-wrap gap-3">
                {selectedIds.map((id) => {
                  const audit = allAudits.find((a) => a.audit_id === id);
                  if (!audit) return null;
                  return (
                    <div
                      key={id}
                      className="relative bg-white/5 border border-cyan-500/30 rounded-lg p-3 pr-8"
                    >
                      <div className="text-xs text-[var(--v-text-secondary)] truncate max-w-[200px]">
                        {audit.url}
                      </div>
                      <div className="text-lg font-bold text-white mt-1">
                        {audit.trust_score}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeAudit(id);
                        }}
                        className="absolute top-1 right-1 text-[var(--v-text-tertiary)] hover:text-red-400 transition-colors"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  );
                })}
              </div>

              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={runComparison}
                disabled={selectedIds.length < 2 || comparing}
                className="mt-3 px-6 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed text-[var(--v-deep)] font-medium rounded-lg flex items-center gap-2"
              >
                {comparing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[var(--v-deep)] border-t-transparent rounded-full animate-spin" />
                    Comparing...
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-4 h-4" />
                    Compare Audits
                  </>
                )}
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* Comparison Results */}
        {comparison && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="space-y-6"
          >
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                <div className="text-[var(--v-text-secondary)] text-sm mb-2">
                  Audits Compared
                </div>
                <div className="text-3xl font-bold text-white">
                  {comparison.audits.length}
                </div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                <div className="text-[var(--v-text-secondary)] text-sm mb-2">
                  Score Range
                </div>
                <div className="text-3xl font-bold text-white">
                  {Math.min(...comparison.audits.map((a) => a.trust_score))} -{" "}
                  {Math.max(...comparison.audits.map((a) => a.trust_score))}
                </div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                <div className="text-[var(--v-text-secondary)] text-sm mb-2">
                  Total Findings
                </div>
                <div className="text-3xl font-bold text-white">
                  {comparison.audits.reduce(
                    (sum, a) => sum + a.findings_summary.total,
                    0
                  )}
                </div>
              </div>
            </div>

            {/* Trust Score Deltas */}
            <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
              <button
                onClick={() =>
                  setExpandedPanel(expandedPanel === "deltas" ? null : "deltas")
                }
                className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5 text-cyan-500" />
                  <h3 className="text-white font-medium">Trust Score Changes</h3>
                </div>
                {expandedPanel === "deltas" ? (
                  <ChevronUp className="text-[var(--v-text-secondary)]" />
                ) : (
                  <ChevronDown className="text-[var(--v-text-secondary)]" />
                )}
              </button>

              {expandedPanel === "deltas" && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  className="border-t border-white/10 p-6 space-y-4"
                >
                  {comparison.trust_score_deltas.map((delta) => {
                    const fromAudit = comparison.audits.find(
                      (a) => a.audit_id === delta.from_audit_id
                    );
                    const toAudit = comparison.audits.find(
                      (a) => a.audit_id === delta.to_audit_id
                    );

                    return (
                      <div
                        key={`${delta.from_audit_id}-${delta.to_audit_id}`}
                        className="bg-white/5 rounded-lg p-4"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <div className="text-xs text-[var(--v-text-secondary)]">
                                {fromAudit?.completed_at ? formatDate(fromAudit.completed_at) : "N/A"}
                              </div>
                              <div className="text-white font-bold">{fromAudit?.trust_score || "—"}</div>
                            </div>
                            <div className={`text-2xl ${formatScoreColor(delta.delta)}`}>
                              {delta.delta >= 0 ? "+" : ""}{delta.delta}
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-[var(--v-text-secondary)]">
                                {toAudit?.completed_at ? formatDate(toAudit.completed_at) : "N/A"}
                              </div>
                              <div className="text-white font-bold">{toAudit?.trust_score || "—"}</div>
                            </div>
                          </div>
                          {delta.percentage_change !== null && (
                            <div
                              className={`text-sm ${delta.percentage_change >= 0
                                  ? "text-emerald-400"
                                  : "text-red-400"
                                }`}
                            >
                              {delta.percentage_change >= 0 ? "+" : ""}
                              {delta.percentage_change.toFixed(1)}% change
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {/* Score Chart */}
                  <div className="mt-6 pt-6 border-t border-white/10">
                    <div className="flex items-end justify-between h-32 gap-2">
                      {comparison.audits
                        .sort(
                          (a, b) =>
                            new Date(a.created_at).getTime() -
                            new Date(b.created_at).getTime()
                        )
                        .map((audit) => (
                          <div key={audit.audit_id} className="flex-1 flex flex-col items-center">
                            <div
                              className={`w-full rounded-t ${audit.trust_score >= 70
                                  ? "bg-emerald-500"
                                  : audit.trust_score >= 40
                                    ? "bg-amber-500"
                                    : "bg-red-500"
                                }`}
                              style={{ height: `${audit.trust_score}%` }}
                            />
                            <div className="text-xs text-[var(--v-text-tertiary)] mt-2 truncate max-w-full text-center">
                              {new Date(audit.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Risk Level Changes */}
            {comparison.risk_level_changes.length > 0 && (
              <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                <button
                  onClick={() =>
                    setExpandedPanel(expandedPanel === "risks" ? null : "risks")
                  }
                  className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-500" />
                    <h3 className="text-white font-medium">Risk Level Changes</h3>
                    <span className="px-2 py-0.5 bg-white/10 rounded-full text-xs text-[var(--v-text-secondary)]">
                      {comparison.risk_level_changes.length}
                    </span>
                  </div>
                  {expandedPanel === "risks" ? (
                    <ChevronUp className="text-[var(--v-text-secondary)]" />
                  ) : (
                    <ChevronDown className="text-[var(--v-text-secondary)]" />
                  )}
                </button>

                {expandedPanel === "risks" && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    className="border-t border-white/10 p-6 space-y-3"
                  >
                    {comparison.risk_level_changes.map((change) => (
                      <div
                        key={`${change.from_audit_id}-${change.to_audit_id}`}
                        className="flex items-center gap-4 bg-white/5 rounded-lg p-4"
                      >
                        <span
                          className={`px-3 py-1.5 rounded-lg text-sm font-medium ${RISK_COLORS[change.from]}`}
                        >
                          {getRiskLevelLabel(change.from)}
                        </span>
                        <TrendingUp className="text-[var(--v-text-secondary)]" />
                        <span
                          className={`px-3 py-1.5 rounded-lg text-sm font-medium ${RISK_COLORS[change.to]}`}
                        >
                          {getRiskLevelLabel(change.to)}
                        </span>
                      </div>
                    ))}
                  </motion.div>
                )}
              </div>
            )}

            {/* Full Audit Details */}
            <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
              <button
                onClick={() =>
                  setExpandedPanel(expandedPanel === "audits" ? null : "audits")
                }
                className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <BarChart3 className="w-5 h-5 text-purple-500" />
                  <h3 className="text-white font-medium">Audit Details</h3>
                </div>
                {expandedPanel === "audits" ? (
                  <ChevronUp className="text-[var(--v-text-secondary)]" />
                ) : (
                  <ChevronDown className="text-[var(--v-text-secondary)]" />
                )}
              </button>

              {expandedPanel === "audits" && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  className="border-t border-white/10"
                >
                  <div className="divide-y divide-white/10">
                    {comparison.audits
                      .sort(
                        (a, b) =>
                          new Date(b.created_at).getTime() -
                          new Date(a.created_at).getTime()
                      )
                      .map((audit) => (
                        <div
                          key={audit.audit_id}
                          className="p-6 hover:bg-white/5 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-6">
                            <div className="flex-1 min-w-0">
                              <div className="text-white truncate mb-2">
                                {audit.url}
                              </div>
                              <div className="flex flex-wrap gap-4 text-sm text-[var(--v-text-secondary)]">
                                <span>
                                  {audit.completed_at ? formatDate(audit.completed_at) : "In Progress"}
                                </span>
                                <span>•</span>
                                <span>{audit.screenshots_count} screenshots</span>
                                <span>•</span>
                                <span>{audit.findings_summary.total} findings</span>
                              </div>
                            </div>

                            <div className="text-center">
                              <div
                                className={`text-3xl font-bold ${audit.trust_score >= 70
                                    ? "text-emerald-500"
                                    : audit.trust_score >= 40
                                      ? "text-amber-500"
                                      : "text-red-500"
                                  }`}
                              >
                                {audit.trust_score}
                              </div>
                              <div
                                className={`text-xs px-2 py-1 rounded mt-1 ${getRiskLevelColor(
                                  audit.risk_level
                                )}`}
                              >
                                {getRiskLevelLabel(audit.risk_level)}
                              </div>
                            </div>
                          </div>

                          {/* Findings Breakdown */}
                          <div className="flex gap-2 mt-4">
                            {Object.entries(audit.findings_summary)
                              .filter(([key]) => key !== "total")
                              .map(([severity, count]) => {
                                if (count === 0) return null;
                                const severityColor =
                                  severity === "critical"
                                    ? "bg-red-500/20 text-red-400 border-red-500/30"
                                    : severity === "high"
                                      ? "bg-orange-500/20 text-orange-400 border-orange-500/30"
                                      : severity === "medium"
                                        ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                                        : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
                                return (
                                  <span
                                    key={severity}
                                    className={`px-2 py-1 rounded text-xs border ${severityColor}`}
                                  >
                                    {count} {severity}
                                  </span>
                                );
                              })}
                          </div>

                          <Link
                            href={`/report/${audit.audit_id}`}
                            className="mt-4 inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
                          >
                            View Full Report
                            <ArrowLeft className="w-4 h-4 rotate-180" />
                          </Link>
                        </div>
                      ))}
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}

        {/* Select Audits Dialog */}
        {selectedIds.length < 5 && allAudits.length > 0 && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-xl font-bold text-white mb-4">
              Select Audits to Compare
            </h2>

            {/* Group by URL */}
            {Array.from(
              new Set(allAudits.map((a) => a.url))
            ).map((url) => {
              const urlAudits = allAudits
                .filter((a) => a.url === url)
                .sort(
                  (a, b) =>
                    new Date(b.created_at).getTime() -
                    new Date(a.created_at).getTime()
                );

              if (urlAudits.length < 2) return null; // Only show URLs with multiple audits

              return (
                <div key={url} className="mb-6">
                  <div className="text-sm text-[var(--v-text-secondary)] mb-2 truncate">
                    {url}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {urlAudits.map((audit) => (
                      <div
                        key={audit.audit_id}
                        onClick={() => toggleAuditSelection(audit.audit_id)}
                        className={`cursor-pointer rounded-lg p-4 border-2 transition-all ${selectedIds.includes(audit.audit_id)
                            ? "border-cyan-500 bg-cyan-500/10"
                            : "border-white/10 bg-white/5 hover:border-white/20"
                          }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs text-[var(--v-text-secondary)]">
                            {formatDate(audit.completed_at || audit.created_at)}
                          </span>
                          {audit.status === "completed" ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          ) : (
                            <Activity className="w-4 h-4 text-amber-500" />
                          )}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-2xl font-bold text-white">
                            {audit.trust_score}
                          </span>
                          <span
                            className={`text-xs px-2 py-1 rounded ${getRiskLevelColor(
                              audit.risk_level
                            )}`}
                          >
                            {getRiskLevelLabel(audit.risk_level)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}

            {allAudits.filter((a) => a.status === "completed").length <
              2 && (
                <div className="text-center text-[var(--v-text-secondary)] py-10">
                  <div className="mb-2">
                    You need at least 2 completed audits of the same URL to compare.
                  </div>
                  <Link
                    href="/"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-[var(--v-deep)] rounded-lg text-sm font-medium"
                  >
                    Run New Audit
                  </Link>
                </div>
              )}
          </motion.div>
        )}
      </main>
    </div>
  );
}

function Navbar() {
  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[var(--v-deep)]/80 backdrop-blur-xl"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <a href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white">
            V
          </div>
          <span className="font-bold text-sm tracking-widest text-[var(--v-text)]">
            VERITAS
          </span>
        </a>

        <div className="flex items-center gap-6">
          <a
            href="/history"
            className="text-xs text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
          >
            History
          </a>
          <a
            href="/"
            className="text-xs text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
          >
            New Audit
          </a>
        </div>
      </div>
    </motion.nav>
  );
}

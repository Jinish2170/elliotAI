"use client";

import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { StatCounter } from "@/components/data-display/StatCounter";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CompareData {
    audits: Array<{
        audit_id: string;
        url: string;
        status: string;
        trust_score: number | null;
        risk_level: string | null;
        site_type: string | null;
        created_at: string | null;
        completed_at: string | null;
        findings_summary: {
            total: number;
            critical: number;
            high: number;
            medium: number;
            low: number;
        };
        screenshots_count: number;
    }>;
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

export default function ComparePage() {
    const params = useParams();
    const idsParam = Array.isArray(params?.ids) ? params.ids.join(",") : params?.ids;
    const ids = idsParam ? decodeURIComponent(idsParam as string).split(",") : [];

    const [data, setData] = useState<CompareData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function fetchComparison() {
            if (ids.length < 2) {
                setError("At least two audits are required for comparison.");
                setLoading(false);
                return;
            }

            try {
                const res = await fetch(`${API_URL}/api/audits/compare`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ audit_ids: ids }),
                });

                if (!res.ok) {
                    throw new Error("Failed to fetch comparison data.");
                }

                const result = await res.json();
                setData(result);
            } catch (err) {
                console.error(err);
                setError("Error loading comparison. Ensure the backend is running and IDs are valid.");
            } finally {
                setLoading(false);
            }
        }

        fetchComparison();
    }, [idsParam]); // eslint-disable-line react-hooks/exhaustive-deps

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

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return "N/A";
        try {
            const date = new Date(dateStr);
            return new Intl.DateTimeFormat("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
                hour: "numeric",
                minute: "numeric",
            }).format(date);
        } catch {
            return dateStr;
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen pt-24 px-4 flex justify-center items-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="min-h-screen pt-24 px-4 flex flex-col items-center">
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-8 rounded-xl max-w-lg text-center mt-12">
                    <ShieldAlert className="w-12 h-12 mb-4 mx-auto opacity-80" />
                    <h2 className="text-xl font-bold mb-2">Error connecting to data</h2>
                    <p className="mb-6">{error || "No data received."}</p>
                    <Link
                        href="/history"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to History
                    </Link>
                </div>
            </div>
        );
    }

    // Ensure audits are chronological
    const sortedAudits = [...data.audits].sort((a, b) => {
        return new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
    });

    return (
        <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-24">
            <div className="mb-8">
                <Link
                    href="/history"
                    className="inline-flex items-center gap-2 text-sm text-[var(--v-text-tertiary)] hover:text-[var(--v-text)] transition-colors mb-6"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to History
                </Link>
                <h1 className="text-3xl font-bold tracking-tight text-[var(--v-text)] mb-2">
                    Audit Comparison
                </h1>
                <p className="text-[var(--v-text-secondary)]">
                    Analyzing delta and progression between {sortedAudits.length} selected audits.
                </p>
            </div>

            {sortedAudits.length > 0 && (
                <div className="mb-10 p-6 bg-[var(--v-surface)] rounded-xl border border-white/5">
                    <div className="text-sm text-[var(--v-text-secondary)] font-medium mb-1">Target URL</div>
                    <div className="text-xl text-[var(--v-text)] font-semibold truncate">{sortedAudits[0].url}</div>
                </div>
            )}

            {/* Core comparison stats block */}
            <div className="space-y-10">

                {/* Deltas & Changes (if any) */}
                {data.trust_score_deltas.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {data.trust_score_deltas.map((delta, i) => (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 }}
                                key={i}
                                className="bg-black/20 rounded-xl border border-white/5 p-6 flex flex-col"
                            >
                                <div className="text-[var(--v-text-tertiary)] text-xs font-medium mb-4 uppercase tracking-wider">
                                    Trust Score Change
                                </div>
                                <div className="flex items-center justify-center gap-6 mt-auto mb-auto">
                                    <div className="text-center">
                                        <div className="text-sm text-[var(--v-text-secondary)] mb-1">Before</div>
                                        <div className="text-3xl font-bold font-mono">{sortedAudits[i].trust_score || "--"}</div>
                                    </div>

                                    <div className="flex flex-col items-center">
                                        <ArrowRight className="w-5 h-5 text-[var(--v-text-tertiary)] mb-2" />
                                        <div className={`px-2 py-1 rounded-full text-xs font-bold ${delta.delta > 0 ? "bg-green-500/20 text-green-400" :
                                                delta.delta < 0 ? "bg-red-500/20 text-red-400" : "bg-white/10 text-white/70"
                                            }`}>
                                            {delta.delta > 0 ? "+" : ""}{delta.delta.toFixed(1)}
                                        </div>
                                    </div>

                                    <div className="text-center">
                                        <div className="text-sm text-[var(--v-text-secondary)] mb-1">After</div>
                                        <div className="text-3xl font-bold font-mono glow-text">{sortedAudits[i + 1].trust_score || "--"}</div>
                                    </div>
                                </div>
                            </motion.div>
                        ))}

                        {data.risk_level_changes.map((change, i) => (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 + 0.1 }}
                                key={i}
                                className="bg-black/20 rounded-xl border border-white/5 p-6 flex flex-col"
                            >
                                <div className="text-[var(--v-text-tertiary)] text-xs font-medium mb-4 uppercase tracking-wider">
                                    Risk Level Change
                                </div>
                                <div className="flex items-center justify-center gap-6 mt-auto mb-auto">
                                    <div className="flex flex-col items-center">
                                        <div className={`w-12 h-12 rounded-full border flex items-center justify-center mb-3 ${getRiskColor(change.from)}`}>
                                            {getRiskIcon(change.from)}
                                        </div>
                                        <div className="font-semibold capitalize">{change.from}</div>
                                    </div>

                                    <ArrowRight className="w-5 h-5 text-[var(--v-text-tertiary)]" />

                                    <div className="flex flex-col items-center">
                                        <div className={`w-12 h-12 rounded-full border flex items-center justify-center mb-3 ${getRiskColor(change.to)}`}>
                                            {getRiskIcon(change.to)}
                                        </div>
                                        <div className="font-semibold capitalize">{change.to}</div>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}

                {/* Side-by-Side Detailed Breakdown */}
                <div>
                    <h3 className="text-xl font-bold text-[var(--v-text)] mb-6">Detailed Breakdown</h3>
                    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                        {sortedAudits.map((audit, i) => (
                            <motion.div
                                key={audit.audit_id}
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: i * 0.1 + 0.2 }}
                                className="bg-[var(--v-surface)] rounded-xl border border-white/5 overflow-hidden flex flex-col"
                            >
                                <div className="p-5 border-b border-white/5 bg-black/20">
                                    <div className="text-xs text-[var(--v-text-tertiary)] mb-1">
                                        Audit {i + 1} of {sortedAudits.length}
                                    </div>
                                    <div className="font-medium text-[var(--v-text-secondary)]">
                                        {formatDate(audit.created_at)}
                                    </div>
                                </div>

                                <div className="p-6 space-y-6 flex-1">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-[var(--v-text-secondary)]">Trust Score</span>
                                        <span className="text-2xl font-mono font-bold">{audit.trust_score !== null ? audit.trust_score : "--"}</span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-[var(--v-text-secondary)]">Risk Level</span>
                                        <div className={`px-3 py-1 rounded-full text-xs font-semibold border flex items-center gap-1.5 ${getRiskColor(audit.risk_level)}`}>
                                            {getRiskIcon(audit.risk_level)}
                                            <span className="capitalize">{audit.risk_level || "Unknown"}</span>
                                        </div>
                                    </div>

                                    <div className="pt-4 border-t border-white/5">
                                        <span className="text-xs text-[var(--v-text-tertiary)] uppercase tracking-wider mb-4 block">Findings</span>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <div className="text-xs text-red-400 mb-1">Critical</div>
                                                <div className="text-xl font-semibold">{audit.findings_summary.critical}</div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-orange-400 mb-1">High</div>
                                                <div className="text-xl font-semibold">{audit.findings_summary.high}</div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-yellow-400 mb-1">Medium</div>
                                                <div className="text-lg font-semibold">{audit.findings_summary.medium}</div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-green-400 mb-1">Low</div>
                                                <div className="text-lg font-semibold">{audit.findings_summary.low}</div>
                                            </div>
                                        </div>
                                        <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center">
                                            <span className="text-sm text-[var(--v-text-secondary)]">Total Issues</span>
                                            <span className="text-xl font-bold">{audit.findings_summary.total}</span>
                                        </div>
                                    </div>

                                    <div className="pt-4 border-t border-white/5">
                                        <span className="text-sm text-[var(--v-text-secondary)] block mb-2">Meta</span>
                                        <div className="flex justify-between items-center text-xs mb-1">
                                            <span className="text-[var(--v-text-tertiary)]">Site Type:</span>
                                            <span className="text-[var(--v-text-secondary)]">{audit.site_type || "Unknown"}</span>
                                        </div>
                                        <div className="flex justify-between items-center text-xs">
                                            <span className="text-[var(--v-text-tertiary)]">Screenshots:</span>
                                            <span className="text-[var(--v-text-secondary)]">{audit.screenshots_count}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-4 border-t border-white/5 bg-black/10">
                                    <Link
                                        href={`/report/${audit.audit_id}`}
                                        className="block w-full py-2.5 text-center rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/20 transition-all font-medium text-sm"
                                    >
                                        View Full Report
                                    </Link>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

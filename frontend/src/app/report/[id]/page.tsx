"use client";

import { ExecSummary } from "@/components/report/ExecSummary";
import { SignalTable } from "@/components/report/SignalTable";
import { FindingsPanel } from "@/components/report/FindingsPanel";
import { SecurityMatrix } from "@/components/report/SecurityMatrix";
import { EntityIntel } from "@/components/report/EntityIntel";
import { EvidenceGallery } from "@/components/report/EvidenceGallery";
import { RecommendationsPanel } from "@/components/report/RecommendationsPanel";
import { MetadataGrid } from "@/components/report/MetadataGrid";
import { SectionNav } from "@/components/report/SectionNav";
import { JsonTreeViewer } from "@/components/data-display/JsonTreeViewer";
import { useAuditStore } from "@/lib/store";
import type { AuditResult } from "@/lib/types";
import { ArrowLeft, Download, Plus, FileText } from "lucide-react";
import Link from "next/link";
import { use, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const REPORT_SECTIONS = [
  { id: "exec-summary", label: "Executive Summary" },
  { id: "signals", label: "Signal Analysis" },
  { id: "findings", label: "Findings" },
  { id: "security", label: "Security Posture" },
  { id: "entity", label: "Entity Intelligence" },
  { id: "evidence", label: "Evidence Gallery" },
  { id: "recommendations", label: "Recommendations" },
  { id: "metadata", label: "Audit Metadata" },
  { id: "raw-data", label: "Raw Data" },
];

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const storeResult = useAuditStore((s) => s.result);
  const storeScreenshots = useAuditStore((s) => s.screenshots);
  const [result, setResult] = useState<AuditResult | null>(storeResult);
  const [mode, setMode] = useState<"simple" | "expert">("expert");
  const [loading, setLoading] = useState(!storeResult);

  useEffect(() => {
    if (storeResult) {
      setResult(storeResult);
      setLoading(false);
      return;
    }

    const fetchResult = async () => {
      try {
        const res = await fetch(`${API_URL}/api/audit/${id}/status`);
        if (res.ok) {
          const data = await res.json();
          if (data.result) {
            setResult(data.result);
          }
        }
      } catch {
        // silently handle
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [id, storeResult]);

  // Build signal data for SignalTable
  const signals = useMemo(() => {
    if (!result?.signal_scores) return [];
    const SIGNAL_META: Record<string, string> = {
      visual: "Visual Intelligence",
      structural: "Page Structure",
      temporal: "Time Analysis",
      graph: "Identity Verification",
      meta: "Basic Verification",
      security: "Security Audit",
    };
    return Object.entries(result.signal_scores).map(([key, score]) => ({
      name: SIGNAL_META[key] || key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      score: Math.round(score),
      threshold: 60,
    }));
  }, [result?.signal_scores]);

  // Filter active sections based on available data
  const activeSections = useMemo(() => {
    if (!result) return REPORT_SECTIONS;
    return REPORT_SECTIONS.filter((s) => {
      if (s.id === "findings" && (!result.findings || result.findings.length === 0)) return false;
      if (s.id === "recommendations" && (!result.recommendations || result.recommendations.length === 0)) return false;
      if (s.id === "evidence" && (!storeScreenshots || storeScreenshots.length === 0)) return false;
      return true;
    });
  }, [result, storeScreenshots]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--v-deep)] flex items-center justify-center">
        <div className="text-center">
          <div className="w-5 h-5 border-2 border-[var(--v-text-tertiary)] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-[11px] font-mono uppercase tracking-wider text-[var(--v-text-tertiary)]">
            Loading report...
          </p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-[var(--v-deep)] flex items-center justify-center">
        <div className="text-center">
          <FileText className="w-8 h-8 text-[var(--v-text-tertiary)] mx-auto mb-3" />
          <p className="text-[13px] text-[var(--v-text-secondary)]">
            Report not found. The audit may still be in progress.
          </p>
          <Link href="/" className="mt-3 inline-block text-[12px] font-mono text-cyan-400 hover:underline">
            ← Return Home
          </Link>
        </div>
      </div>
    );
  }

  const date = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="min-h-screen bg-[var(--v-deep)]">
      {/* Report Header Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-[var(--v-deep)]/80 border-b border-[rgba(255,255,255,0.04)]">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href={`/audit/${id}`}
              className="p-1.5 rounded border border-[rgba(255,255,255,0.08)] hover:border-[rgba(255,255,255,0.15)] text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-[13px] font-semibold text-[var(--v-text)]">
                Veritas Intelligence Report
              </h1>
              <p className="text-[10px] font-mono text-[var(--v-text-tertiary)]">
                {result.url} · {date}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Mode toggle */}
            <div className="flex rounded bg-[rgba(255,255,255,0.04)] p-0.5 border border-[rgba(255,255,255,0.06)]">
              <button
                onClick={() => setMode("simple")}
                className={`px-2.5 py-1 rounded text-[10px] font-mono transition-colors ${
                  mode === "simple"
                    ? "bg-[var(--v-surface)] text-[var(--v-text)]"
                    : "text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
                }`}
              >
                SIMPLE
              </button>
              <button
                onClick={() => setMode("expert")}
                className={`px-2.5 py-1 rounded text-[10px] font-mono transition-colors ${
                  mode === "expert"
                    ? "bg-[var(--v-surface)] text-[var(--v-text)]"
                    : "text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
                }`}
              >
                EXPERT
              </button>
            </div>

            <button className="p-2 rounded border border-[rgba(255,255,255,0.06)] hover:border-[rgba(255,255,255,0.12)] text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors">
              <Download className="w-3.5 h-3.5" />
            </button>
            <Link
              href="/"
              className="p-2 rounded border border-[rgba(255,255,255,0.06)] hover:border-[rgba(255,255,255,0.12)] text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Layout: SectionNav (left) + Content (center) */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 pt-8 pb-16">
        <div className="flex gap-8">
          {/* Left rail — hidden on mobile */}
          <aside className="hidden lg:block shrink-0">
            <SectionNav sections={activeSections} />
          </aside>

          {/* Main content */}
          <main className="flex-1 min-w-0 space-y-6">
            {/* Executive Summary */}
            <section id="exec-summary">
              <ExecSummary
                score={result.trust_score}
                riskLevel={result.risk_level}
                narrative={result.narrative}
                url={result.url}
                siteType={result.site_type}
                findingsCount={result.findings?.length ?? 0}
                screenshotsCount={result.screenshots_count ?? 0}
                elapsedSeconds={result.elapsed_seconds ?? 0}
              />
            </section>

            {/* Signal Analysis */}
            {signals.length > 0 && (
              <section id="signals">
                <SignalTable signals={signals} />
              </section>
            )}

            {/* Findings */}
            {(result.findings?.length ?? 0) > 0 && (
              <section id="findings">
                <FindingsPanel findings={result.findings ?? []} mode={mode} />
              </section>
            )}

            {/* Security Posture */}
            <section id="security">
              <SecurityMatrix securityResults={result.security_results ?? {}} />
            </section>

            {/* Entity Intelligence */}
            <section id="entity">
              <EntityIntel domainInfo={result.domain_info} url={result.url} />
            </section>

            {/* Evidence Gallery */}
            {(storeScreenshots?.length ?? 0) > 0 && (
              <section id="evidence">
                <EvidenceGallery
                  screenshots={storeScreenshots ?? []}
                  findings={result.findings ?? []}
                />
              </section>
            )}

            {/* Recommendations */}
            {(result.recommendations?.length ?? 0) > 0 && (
              <section id="recommendations">
                <RecommendationsPanel recommendations={result.recommendations ?? []} />
              </section>
            )}

            {/* Audit Metadata */}
            <section id="metadata">
              <MetadataGrid result={result} auditId={id} />
            </section>

            {/* Raw Data */}
            {mode === "expert" && (
              <section id="raw-data">
                <JsonTreeViewer
                  data={{
                    signal_scores: result.signal_scores,
                    security_results: result.security_results,
                    domain_info: result.domain_info,
                    dark_pattern_summary: result.dark_pattern_summary,
                    overrides: result.overrides,
                    errors: result.errors,
                  }}
                  label="Raw Audit Data"
                  defaultExpandDepth={1}
                />
              </section>
            )}
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[rgba(255,255,255,0.04)] py-6 text-center">
        <p className="text-[10px] font-mono text-[var(--v-text-tertiary)]">
          VERITAS · Trust, Verified · Report ID: {id}
        </p>
      </footer>
    </div>
  );
}

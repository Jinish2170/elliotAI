"use client";

import { use, useState, useEffect } from "react";
import { useAuditStore } from "@/lib/store";
import type { AuditResult } from "@/lib/types";
import { ParticleField } from "@/components/ambient/ParticleField";
import { ReportHeader } from "@/components/report/ReportHeader";
import { TrustScoreHero } from "@/components/report/TrustScoreHero";
import { SignalBreakdown } from "@/components/report/SignalBreakdown";
import { DarkPatternGrid } from "@/components/report/DarkPatternGrid";
import { EntityDetails } from "@/components/report/EntityDetails";
import { SecurityPanel } from "@/components/report/SecurityPanel";
import { Recommendations } from "@/components/report/Recommendations";
import { AuditMetadata } from "@/components/report/AuditMetadata";
import { SAFETY_TIPS } from "@/lib/education";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const storeResult = useAuditStore((s) => s.result);
  const [result, setResult] = useState<AuditResult | null>(storeResult);
  const [mode, setMode] = useState<"simple" | "expert">("simple");
  const [loading, setLoading] = useState(!storeResult);

  // If we have the result from the store (navigated from audit page), use it.
  // Otherwise, try to fetch from API.
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

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--v-deep)] flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-pulse">📋</div>
          <p className="text-sm text-[var(--v-text-secondary)]">Loading report...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-[var(--v-deep)] flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🔍</div>
          <p className="text-sm text-[var(--v-text-secondary)]">
            Report not found. The audit may still be in progress.
          </p>
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

  // Pick relevant safety tips
  const relevantTips = SAFETY_TIPS.slice(0, 3);

  return (
    <div className="relative min-h-screen bg-[var(--v-deep)]">
      <ParticleField color="cyan" particleCount={25} />

      <main className="relative z-10 pt-16 px-4 lg:px-8 pb-16 max-w-5xl mx-auto">
        <ReportHeader
          url={result.url}
          date={date}
          auditId={id}
          mode={mode}
          onToggleMode={() => setMode((m) => (m === "simple" ? "expert" : "simple"))}
        />

        <TrustScoreHero
          score={result.trust_score}
          riskLevel={result.risk_level}
          narrative={result.narrative}
        />

        <SignalBreakdown scores={result.signal_scores} />

        {result.findings.length > 0 && (
          <DarkPatternGrid findings={result.findings} mode={mode} />
        )}

        <EntityDetails domainInfo={result.domain_info} url={result.url} />

        <SecurityPanel
          securityResults={result.security_results}
          mode={mode}
        />

        {result.recommendations.length > 0 && (
          <Recommendations recommendations={result.recommendations} />
        )}

        <AuditMetadata result={result} auditId={id} />

        {/* Safety Tips */}
        <section className="glass-card rounded-2xl p-8">
          <h2 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold mb-4">
            Safety Tips
          </h2>
          <div className="space-y-3">
            {relevantTips.map((tip) => (
              <div key={tip.id} className="flex items-start gap-2">
                <span className="text-cyan-400 mt-0.5">💡</span>
                <p className="text-sm text-[var(--v-text-secondary)]">{tip.tip}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="mt-12 text-center">
          <p className="text-xs text-[var(--v-text-tertiary)]">
            Veritas — Trust, Verified. · Report ID: {id}
          </p>
        </footer>
      </main>
    </div>
  );
}

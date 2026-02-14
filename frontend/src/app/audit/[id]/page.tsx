"use client";

import { ParticleField } from "@/components/ambient/ParticleField";
import { AgentPipeline } from "@/components/audit/AgentPipeline";
import { AuditHeader } from "@/components/audit/AuditHeader";
import { CompletionOverlay } from "@/components/audit/CompletionOverlay";
import { EvidencePanel } from "@/components/audit/EvidencePanel";
import { ForensicLog } from "@/components/audit/ForensicLog";
import { NarrativeFeed } from "@/components/audit/NarrativeFeed";
import { useAuditStream } from "@/hooks/useAuditStream";
import { AnimatePresence } from "framer-motion";
import { use, useState } from "react";
import { useSearchParams } from "next/navigation";

// Phase-dependent particle colors
const PHASE_COLORS: Record<string, string> = {
  scout: "cyan",
  security: "cyan",
  vision: "purple",
  graph: "purple",
  judge: "cyan",
};

export default function AuditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const url = searchParams.get("url") || undefined;
  const tier = searchParams.get("tier") || undefined;
  const store = useAuditStream(id, url, tier);
  const [showOverlay, setShowOverlay] = useState(true);

  const particleColor = store.currentPhase
    ? PHASE_COLORS[store.currentPhase] || "cyan"
    : "cyan";

  return (
    <div className="relative min-h-screen bg-[var(--v-deep)]">
      <ParticleField color={particleColor} particleCount={30} />

      <main className="relative z-10 pt-16 px-4 lg:px-6 pb-4 max-w-[1600px] mx-auto">
        <AuditHeader
          url={store.url}
          status={store.status}
          auditId={store.auditId}
          elapsed={store.stats.elapsed_seconds}
        />

        {/* Three-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr_280px] gap-4 mb-4">
          {/* Left: Agent Pipeline */}
          <div className="hidden lg:block">
            <AgentPipeline
              phases={store.phases}
              currentPhase={store.currentPhase}
            />
          </div>

          {/* Mobile: horizontal agent pills */}
          <div className="lg:hidden flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
            {(["scout", "security", "vision", "graph", "judge"] as const).map((phase) => {
              const s = store.phases[phase];
              return (
                <div
                  key={phase}
                  className={`flex-shrink-0 px-3 py-1.5 rounded-full text-[10px] font-medium border ${
                    s.status === "active"
                      ? "border-cyan-500/50 text-cyan-400 bg-cyan-500/10"
                      : s.status === "complete"
                      ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10"
                      : "border-white/10 text-[var(--v-text-tertiary)]"
                  }`}
                >
                  {s.status === "complete" ? "✅" : s.status === "error" ? "❌" : ""}{" "}
                  {phase.charAt(0).toUpperCase() + phase.slice(1)}
                </div>
              );
            })}
          </div>

          {/* Center: Narrative Feed */}
          <div className="min-h-0">
            <NarrativeFeed
              currentPhase={store.currentPhase}
              findings={store.findings}
              screenshots={store.screenshots}
              logs={store.logs}
              status={store.status}
              trustScore={store.result?.trust_score}
            />
          </div>

          {/* Right: Evidence Panel */}
          <div className="hidden lg:block">
            <EvidencePanel
              screenshots={store.screenshots}
              findings={store.findings}
              stats={store.stats}
            />
          </div>
        </div>

        {/* Bottom: Forensic Log */}
        <ForensicLog logs={store.logs} />

        {/* Mobile evidence panel - bottom sheet style */}
        <div className="lg:hidden mt-4">
          <EvidencePanel
            screenshots={store.screenshots}
            findings={store.findings}
            stats={store.stats}
          />
        </div>
      </main>

      {/* Completion Overlay */}
      <AnimatePresence>
        {store.status === "complete" && store.result && showOverlay && (
          <CompletionOverlay
            trustScore={store.result.trust_score}
            riskLevel={store.result.risk_level}
            auditId={id}
            onDismiss={() => setShowOverlay(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

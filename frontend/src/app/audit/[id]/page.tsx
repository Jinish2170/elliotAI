"use client";

/* ========================================
   War Room — Audit Page (Bloomberg Layout)
   4-zone: Agent Stack | Active Intel | Evidence Stack | Event Log
   + Metric Ticker at top. ChromaticProvider wraps all.
   ======================================== */

import { ChromaticProvider } from "@/components/providers/ChromaticProvider";
import { ActiveIntel } from "@/components/audit/ActiveIntel";
import { AgentTile } from "@/components/audit/AgentTile";
import { AuditHeader } from "@/components/audit/AuditHeader";
import { EventLog } from "@/components/audit/EventLog";
import { EvidenceStack } from "@/components/audit/EvidenceStack";
import { MetricTicker, type TickerMetric } from "@/components/audit/MetricTicker";
import { VerdictReveal } from "@/components/audit/VerdictReveal";
import { PanelChrome } from "@/components/layout/PanelChrome";
import { AGENT_ORDER, type AgentId } from "@/config/agents";
import { useAuditStream } from "@/hooks/useAuditStream";
import type { Phase } from "@/lib/types";
import { use, useEffect, useMemo, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { saveAuditToHistory } from "@/components/landing/RecentAudits";

function AuditPageContent({ id }: { id: string }) {
  const searchParams = useSearchParams();
  const url = searchParams.get("url") || undefined;
  const tier = searchParams.get("tier") || undefined;
  const store = useAuditStream(id, url, tier);
  const [showOverlay, setShowOverlay] = useState(true);

  // Persist completed audit to localStorage for RecentAudits
  useEffect(() => {
    if (store.status === "complete" && store.result) {
      saveAuditToHistory({
        id,
        url: store.result.url,
        score: store.result.trust_score,
        riskLevel: store.result.risk_level,
        date: new Date().toISOString(),
        tier: tier || store.result.audit_tier || "standard",
      });
    }
  }, [store.status, store.result, id, tier]);

  // Map current phase to AgentId for chromatic provider
  const activeAgent: AgentId | undefined = useMemo(() => {
    if (!store.currentPhase || store.currentPhase === "init") return undefined;
    return store.currentPhase as AgentId;
  }, [store.currentPhase]);

  // Build ticker metrics from store stats + live arrays for real-time counts
  const tickerMetrics: TickerMetric[] = useMemo(
    () => [
      { label: "TRUST", value: store.dualVerdict?.trust_score ?? store.result?.trust_score ?? "—" },
      { label: "PAGES", value: store.stats.pages_scanned },
      { label: "FINDINGS", value: Math.max(store.findings.length, store.stats.findings) },
      { label: "SCREENSHOTS", value: Math.max(store.screenshots.length, store.stats.screenshots) },
      { label: "HEADERS", value: store.stats.security_checks > 0 ? "✓" : "—", status: store.stats.security_checks > 0 ? "pass" as const : undefined },
      { label: "AI CALLS", value: store.stats.ai_calls },
      { label: "SEC CHECKS", value: store.stats.security_checks },
    ],
    [store.stats, store.findings.length, store.screenshots.length, store.result]
  );

  return (
    <ChromaticProvider initialAgent={activeAgent}>
      <div className="relative min-h-screen bg-[var(--v-substrate)] flex flex-col">
        {/* Header bar */}
        <div className="relative z-20">
          <AuditHeader
            url={store.url}
            status={store.status}
            auditId={store.auditId}
            elapsed={store.stats.elapsed_seconds}
          />
        </div>

        {/* Metric ticker strip */}
        <div className="relative z-10 border-b border-[rgba(255,255,255,0.04)]">
          <MetricTicker metrics={tickerMetrics} />
        </div>

        {/* Main 4-zone War Room grid */}
        <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[200px_1fr_280px] gap-0 overflow-hidden">
          {/* Left: Agent Stack */}
          <div className="hidden lg:flex flex-col border-r border-[rgba(255,255,255,0.06)] overflow-y-auto bg-[var(--elev-1)]">
            <PanelChrome title="Agents" elevation={1} collapsible={false}>
              <div className="p-2 space-y-1">
                {AGENT_ORDER.map((agentId) => {
                  const phase = agentId as Phase;
                  const phaseState = store.phases[phase];
                  return (
                    <AgentTile
                      key={agentId}
                      agent={agentId}
                      status={phaseState?.status || "waiting"}
                      progress={phaseState?.pct || 0}
                      isActive={store.currentPhase === phase}
                      stat={
                        agentId === "scout"
                          ? `${store.stats.pages_scanned} pages`
                          : agentId === "security"
                          ? `${store.stats.security_checks} checks`
                          : agentId === "vision"
                          ? `${Math.max(store.screenshots.length, store.stats.screenshots)} screenshots`
                          : agentId === "graph"
                          ? `${store.osintResults.length} sources`
                          : agentId === "judge"
                          ? (store.dualVerdict?.trust_score ?? store.result?.trust_score)
                            ? `Score: ${store.dualVerdict?.trust_score ?? store.result?.trust_score}`
                            : "Waiting..."
                          : ""
                      }
                    />
                  );
                })}
              </div>
            </PanelChrome>
          </div>

          {/* Mobile: horizontal agent pills */}
          <div className="lg:hidden flex gap-1.5 overflow-x-auto px-3 py-2 bg-[var(--elev-1)] border-b border-[rgba(255,255,255,0.06)]">
            {AGENT_ORDER.map((agentId) => {
              const phase = agentId as Phase;
              const phaseState = store.phases[phase];
              const isActive = store.currentPhase === phase;
              return (
                <div
                  key={agentId}
                  className={`flex-shrink-0 px-3 py-1 rounded text-[10px] font-mono font-medium border transition-colors ${
                    isActive
                      ? "border-[var(--agent-border)] text-[var(--agent-text)] bg-[var(--agent-bg-subtle)]"
                      : phaseState?.status === "complete"
                      ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10"
                      : phaseState?.status === "error"
                      ? "border-red-500/30 text-red-400 bg-red-500/10"
                      : "border-white/10 text-[var(--v-text-tertiary)]"
                  }`}
                >
                  {agentId.toUpperCase()}
                </div>
              );
            })}
          </div>

          {/* Center: Active Intel */}
          <div className="min-h-0 overflow-hidden">
            <ActiveIntel
              currentPhase={store.currentPhase}
              phases={store.phases}
              findings={store.findings}
              screenshots={store.screenshots}
              logs={store.logs}
              status={store.status}
              trustScore={store.result?.trust_score}
              className="h-full"
            />
          </div>

          {/* Right: Evidence Stack */}
          <div className="hidden lg:block border-l border-[rgba(255,255,255,0.06)] overflow-y-auto bg-[var(--elev-1)]">
            <EvidenceStack
              screenshots={store.screenshots}
              findings={store.findings}
              stats={store.stats}
              osintResults={store.osintResults}
              trustScore={store.result?.trust_score}
              className="h-full"
            />
          </div>
        </div>

        {/* Bottom: Event Log */}
        <div className="border-t border-[rgba(255,255,255,0.06)]">
          <EventLog
            logs={store.logs}
            currentAgent={activeAgent}
          />
        </div>

        {/* Mobile evidence stack - bottom sheet */}
        <div className="lg:hidden border-t border-[rgba(255,255,255,0.06)]">
          <EvidenceStack
            screenshots={store.screenshots}
            findings={store.findings}
            stats={store.stats}
            osintResults={store.osintResults}
            trustScore={store.result?.trust_score}
          />
        </div>

        {/* Verdict Reveal Overlay */}
        {store.status === "complete" && store.result && showOverlay && (
          <VerdictReveal
            trustScore={store.result.trust_score}
            riskLevel={store.result.risk_level}
            auditId={id}
            onDismiss={() => setShowOverlay(false)}
          />
        )}
      </div>
    </ChromaticProvider>
  );
}

export default function AuditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[var(--v-substrate)] flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 rounded-lg border border-[rgba(255,255,255,0.1)] flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
            </div>
            <span className="text-[11px] font-mono text-[var(--v-text-tertiary)]">
              INITIALIZING WAR ROOM...
            </span>
          </div>
        </div>
      }
    >
      <AuditPageContent id={id} />
    </Suspense>
  );
}

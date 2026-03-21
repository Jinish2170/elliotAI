"use client";

import { use, useEffect, useMemo, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  TerminalPanel,
  GhostPanel,
  VerdictPanel,
  CvssRadar,
  MitreGrid,
  DarknetOsintGrid,
  SysLogStream,
  AgentProcState,
  ScoutImagery,
  KnowledgeGraph,
  ScoutTelemetry,
  VisionIntelligence,
  ThreatIntelligenceMatrix,
  FinalAuditReport
} from "@/components/terminal";
import { ChromaticProvider } from "@/components/providers/ChromaticProvider";
import { useAuditStream } from "@/hooks/useAuditStream";
import type { AgentId } from "@/config/agents";
import { saveAuditToHistory } from "@/components/landing/RecentAudits";

function TerminalHeader({ url, elapsed }: { url?: string, elapsed: number }) {
  return (
    <div className="h-10 shrink-0 border-b border-[var(--t-border)] flex items-center justify-between px-4 bg-[var(--t-panel)] text-[10px] uppercase tracking-widest text-[var(--t-dim)] font-mono">
      <div className="flex gap-4 items-center">
        <span className="text-[var(--t-text)] font-bold">VERITAS TERM /// 9.4.0</span>
        {url && (
          <>
            <span>TARGET:</span>
            <span className="text-[var(--t-green)]">{url}</span>
          </>
        )}
      </div>
      <div className="flex gap-4 items-center">
        <span>T+{elapsed.toFixed(1)}S</span>
        <div className="flex items-center gap-2">
          <span>NET_LNK</span>
          <div className="w-2 h-2 rounded-full bg-[var(--t-green)] animate-pulse" />
        </div>
      </div>
    </div>
  );
}

function MobileBlocker() {
  return (
    <div className="xl:hidden fixed inset-0 z-50 bg-[var(--t-base)] flex flex-col items-center justify-center p-8 text-center">
      <div className="border border-[var(--t-red)] p-6 bg-[var(--t-panel)] max-w-sm">
        <div className="text-[var(--t-red)] font-mono text-sm mb-4">[SYS.ERR] INSUFFICIENT VIEWPORT</div>
        <p className="text-[var(--t-text)] text-xs font-mono">
          VERITAS requires a full operator terminal display (min-width: 1280px).
          Please maximize your window or switch to a workstation to proceed with the audit overview.
        </p>
      </div>
    </div>
  );
}

function AuditPageContent({ id }: { id: string }) {
  const searchParams = useSearchParams();
  const url = searchParams.get("url") || undefined;
  const tier = searchParams.get("tier") || undefined;
  const store = useAuditStream(id, url, tier);
  const [showReport, setShowReport] = useState(false);

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

  const activeAgent: AgentId | undefined = useMemo(() => {
    if (!store.currentPhase || store.currentPhase === "init") return undefined;
    return store.currentPhase as AgentId;
  }, [store.currentPhase]);

  return (
    <ChromaticProvider initialAgent={activeAgent}>
      <MobileBlocker />

      {showReport && store.status === "complete" ? (
        <div className="fixed inset-0 z-50 bg-[#050505]">
          <FinalAuditReport 
            url={store.url || undefined}
            findings={store.findings || []}
            advancedData={{
              narrative: store.result?.narrative,
              verdict: store.dualVerdict?.non_technical || store.dualVerdict?.technical
            }}
            trustScore={store.dualVerdict?.trust_score ?? store.result?.trust_score}
            riskLevel={store.dualVerdict?.non_technical?.risk_level || store.result?.risk_level}
            onClose={() => setShowReport(false)}
          />
        </div>
      ) : null}

      <div className="veritas-terminal">
        {/* ZONE 1: TACTICAL HEADER */}
        <TerminalHeader url={store.url || undefined} elapsed={store.stats.elapsed_seconds} />

        {store.status === "complete" && !showReport && (
          <div className="absolute top-12 right-4 z-40">
            <button 
              onClick={() => setShowReport(true)}
              className="bg-[var(--t-cyan)] text-black px-4 py-2 text-[10px] font-bold tracking-widest uppercase animate-pulse border border-[var(--t-cyan)] hover:bg-black hover:text-[var(--t-cyan)] transition-colors shadow-[0_0_15px_rgba(0,180,255,0.4)]"
            >
              VIEW COMPREHENSIVE REPORT
            </button>
          </div>
        )}

        {/* ZONE 4 (Rails) & ZONES 2/3 (Center) contained in grid */}
        {/* ZONE 4 (Rails) & ZONES 2/3 (Center) contained in grid */}
        <div className="veritas-terminal-grid overflow-hidden">

          {/* Left Rail (Log Stream, Proc State) - High Importance */}
          <div className="flex flex-col gap-[2px] flex-[3] min-w-[300px]">
            <TerminalPanel title="SYS.LOG.STREAM" className="flex-1">
              <SysLogStream logs={store.logs} />
            </TerminalPanel>
            <TerminalPanel title="AGENT.PROC.STATE" className="h-[25%] shrink-0">
              <AgentProcState phases={store.phases} activePhase={store.currentPhase || undefined} status={store.status} />
            </TerminalPanel>
          </div>

          {/* Center Column (Verdict & Matrices) */}
          <div className="flex flex-col gap-[2px] flex-[5] overflow-y-auto pr-1 custom-scrollbar">
            {/* Zone 2: Verdict */}
            <TerminalPanel title="VERDICT.MATRIX" className="h-[20%] shrink-0 flex justify-center items-center">
              <VerdictPanel
                verdict={store.dualVerdict ? {
                  verdict_technical: {
                    trust_score: store.dualVerdict?.trust_score,
                    risk_level: store.dualVerdict?.non_technical?.risk_level || store.result?.risk_level || 'unknown'
                  },
                  verdict_nontechnical: {
                    summary: store.dualVerdict?.non_technical?.summary || store.result?.narrative || ''
                  }
                } : null}
                trustScore={store.dualVerdict?.trust_score ?? store.result?.trust_score}
                status={store.status}
                error={store.error}
              />
            </TerminalPanel>

            {/* GREEN FLAGS - Positive Indicators */}
            <TerminalPanel title="GREEN.FLAGS" className="shrink-0 min-h-[50px]">
              <div className="flex flex-wrap gap-2 p-2">
                {store.green_flags?.length ? (
                  store.green_flags.slice(0, 5).map((flag: any) => (
                    <span key={flag.id || flag.label} className="text-[var(--t-green)] text-[10px] font-mono bg-[var(--t-green)]/10 px-2 py-1 rounded border border-[var(--t-green)]/30">
                      {flag.icon || "✓"} {flag.label}
                    </span>
                  ))
                ) : (
                  <span className="text-[var(--t-dim)] text-[10px] italic py-1 px-2 border border-transparent">
                    {store.status === "complete" ? "No positive indicators detected" : "Analyzing indicators..."}
                  </span>
                )}
              </div>
            </TerminalPanel>

            <TerminalPanel title="SCOUT.TELEMETRY" className="h-[25%] shrink-0">
              <ScoutTelemetry 
                explorationPath={store.explorationPath}
                formDetections={store.formDetections || []}
                captchaResults={store.captchaResults || []}
                pagesScanned={store.stats.pages_scanned}
              />
            </TerminalPanel>

            {/* Zone 3: Investigative Matrix - Expands if space available */}
            <div className="flex-1 grid grid-cols-2 gap-[2px] bg-[var(--t-border)] min-h-[300px]">
              <TerminalPanel title="CVSS.RADAR" className="h-full">
                <CvssRadar 
                  metrics={store.cvssMetrics?.length ? store.cvssMetrics : ((store.result as any)?.security_results?.cvss_metrics as any[]) || []}
                  status={store.status}
                />
              </TerminalPanel>
              <TerminalPanel title="MITRE.ATTACK.GRID" className="h-full">
                <MitreGrid 
                  techniques={store.mitreTechniques?.length ? store.mitreTechniques : ((store.result as any)?.security_results?.mitre_mappings as any[]) || []}
                  status={store.status}
                />
              </TerminalPanel>
              <TerminalPanel title="THREAT.MATRIX" className="col-span-2 h-full">
                <ThreatIntelligenceMatrix
                  osintResults={store.osintResults || []}
                  marketplaceThreats={store.marketplaceThreats || []}
                  status={store.status}
                />
              </TerminalPanel>
            </div>
          </div>

          {/* Right Rail (Evidence, Graphs) */}
          <div className="flex flex-col gap-[2px] flex-[2.5] min-w-[250px]">
            <TerminalPanel title="SCOUT.IMAGERY" className="h-[25%] shrink-0">
              <ScoutImagery screenshots={store.screenshots} />
            </TerminalPanel>
            <TerminalPanel title="VISION.INTELLIGENCE" className="h-[35%] shrink-0">
              <VisionIntelligence
                 darkPatterns={store.darkPatternFindings || []}
                 temporal={store.temporalFindings || []}
                 status={store.status}
              />
            </TerminalPanel>
            <TerminalPanel title="KNOWLEDGE.GRAPH" className="flex-1">
              <KnowledgeGraph findings={store.findings || []} knowledgeGraph={store.knowledgeGraph} />
            </TerminalPanel>
          </div>

        </div>
      </div>
    </ChromaticProvider>
  );
}

export default function AuditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[var(--t-base)] flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <span className="text-[11px] font-mono text-[var(--t-dim)] animate-pulse">
              [ INITIALIZING TERMINAL... ]
            </span>
          </div>
        </div>
      }
    >
      <AuditPageContent id={id} />
    </Suspense>
  );
}
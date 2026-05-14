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
  FinalAuditReport,
  CorporateEntitiesPanel
} from "@/components/terminal";
import { ChromaticProvider } from "@/components/providers/ChromaticProvider";
import { useAuditStream } from "@/hooks/useAuditStream";
import type { AgentId } from "@/config/agents";
import { saveAuditToHistory } from "@/components/landing/RecentAudits";

function TerminalHeader({ url, elapsed }: { url?: string, elapsed: number }) {
  return (
    <div className="h-10 shrink-0 border-b border-[var(--t-border)] flex items-center justify-between px-4 bg-[var(--t-panel)] text-[11px] uppercase tracking-widest text-[var(--t-dim)] font-mono">
      <div className="flex gap-4 items-center">
        <span className="text-[var(--t-text)] font-bold">ELLIOT TERM /// 9.4.0</span>
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
        <p className="text-[var(--t-text)] text-sm font-mono">
          ELLIOT requires a full operator terminal display (min-width: 1280px).
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

      <div className="elliot-terminal">
        {/* ZONE 1: TACTICAL HEADER */}
        <TerminalHeader url={store.url || undefined} elapsed={store.stats.elapsed_seconds} />

        {store.status === "complete" && !showReport && (
          <div className="absolute top-2 right-4 z-40">
            <button 
              onClick={() => setShowReport(true)}
              className="bg-[var(--t-cyan)] text-black px-4 py-2 text-[11px] font-bold tracking-widest uppercase animate-pulse border border-[var(--t-cyan)] hover:bg-black hover:text-[var(--t-cyan)] transition-colors shadow-[0_0_15px_rgba(0,180,255,0.4)]"
            >
              VIEW COMPREHENSIVE REPORT
            </button>
          </div>
        )}

        {/* ZONE 4 (Rails) & ZONES 2/3 (Center) contained in grid */}
        <div className="elliot-terminal-grid overflow-hidden">

          {/* Left Rail (Investigative Matrices + Proc State) */}
          <div className="flex flex-col gap-2 flex-[3] min-w-0 min-h-0">
            <div className="flex-1 grid grid-rows-3 gap-2 min-h-0">
              {(!store.cvssMetrics?.length && store.corporateEntities?.length > 0) ? (
                <TerminalPanel title="CORP.INTEGRITY.VERIFICATION" className="min-h-0">
                  <CorporateEntitiesPanel entities={store.corporateEntities} status={store.status} />
                </TerminalPanel>
              ) : (
                <TerminalPanel title="CVSS.RADAR" className="min-h-0">
                  <CvssRadar 
                    metrics={store.cvssMetrics?.length ? store.cvssMetrics : ((store.result as any)?.security_results?.cvss_metrics as any[]) || []}
                    status={store.status}
                  />
                </TerminalPanel>
              )}
              
              <TerminalPanel title="MITRE.ATTACK.GRID" className="min-h-0">
                <MitreGrid
                  techniques={store.mitreTechniques?.length ? store.mitreTechniques : ((store.result as any)?.security_results?.mitre_mappings as any[]) || []}
                  status={store.status}
                />
              </TerminalPanel>
              <TerminalPanel title="THREAT.MATRIX" className="min-h-0">
                <ThreatIntelligenceMatrix
                  osintResults={store.osintResults || []}
                  marketplaceThreats={store.marketplaceThreats || []}
                  status={store.status}
                />
              </TerminalPanel>
            </div>
            <TerminalPanel title="AGENT.PROC.STATE" className="flex-none max-h-[180px]">
              <AgentProcState phases={store.phases} activePhase={store.currentPhase || undefined} status={store.status} />
            </TerminalPanel>
          </div>

          {/* Center Column (Verdict / Active Intel & SysLog.Stream) */}
          <div className="flex flex-col gap-2 flex-[5] min-w-0 min-h-0">

            {/* Dynamic Telemetry OR Verdict Matrix */}
            {store.status === "complete" ? (
              <TerminalPanel title="VERDICT.MATRIX" className="flex-[2] min-h-0">
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
            ) : (
              <TerminalPanel title="LIVE.TELEMETRY.STREAM" className="flex-none">
                <div className="flex w-full p-2 gap-4 justify-around items-center bg-[#050505]">
                  <div className="flex flex-col items-center justify-center p-3 border border-[var(--t-border)] bg-[#0a0a0a] rounded flex-1">
                    <span className="text-[var(--t-dim)] text-[11px] uppercase tracking-widest mb-2 font-bold">Findings Detected</span>
                    <span className="text-[var(--t-red)] font-mono text-3xl glow-text-red">{store.stats?.findings || 0}</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-3 border border-[var(--t-border)] bg-[#0a0a0a] rounded flex-1">
                    <span className="text-[var(--t-dim)] text-[11px] uppercase tracking-widest mb-2 font-bold">Pages Mapped</span>
                    <span className="text-[var(--t-cyan)] font-mono text-3xl" style={{textShadow: "0 0 5px var(--t-cyan)"}}>{store.stats?.pages_scanned || 0}</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-3 border border-[var(--t-border)] bg-[#0a0a0a] rounded flex-1">
                    <span className="text-[var(--t-dim)] text-[11px] uppercase tracking-widest mb-2 font-bold">Neural Casts</span>
                    <span className="text-[var(--t-green)] font-mono text-3xl glow-text-green">{store.stats?.ai_calls || 0}</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-3 border border-[var(--t-border)] bg-[#0a0a0a] rounded flex-1">
                    <span className="text-[var(--t-dim)] text-[11px] uppercase tracking-widest mb-2 font-bold">Sec Checks</span>
                    <span className="text-[var(--t-amber)] font-mono text-3xl glow-text-amber">{store.stats?.security_checks || 0}</span>
                  </div>
                </div>
                <div className="absolute top-2 right-4 text-[11px] text-[var(--t-amber)] font-mono animate-pulse">
                  [ CALIBRATING ]
                </div>
              </TerminalPanel>
            )}

            {/* GREEN FLAGS - Positive Indicators */}
            <TerminalPanel title="GREEN.FLAGS" className="flex-none">
              <div className="flex flex-wrap gap-2 p-2">
                {store.green_flags?.length ? (
                  store.green_flags.slice(0, 5).map((flag: any) => (
                    <span key={flag.id || flag.label} className="text-[var(--t-green)] text-[11px] font-mono bg-[var(--t-green)]/10 px-2 py-1 rounded border border-[var(--t-green)]/30">
                      {flag.icon || "✓"} {flag.label}
                    </span>
                  ))
                ) : (
                  <span className="text-[var(--t-dim)] text-[11px] italic py-1 px-2 border border-transparent">
                    {store.status === "complete" ? "No positive indicators detected" : "Analyzing indicators..."}
                  </span>
                )}
              </div>
            </TerminalPanel>

            <TerminalPanel title="SCOUT.TELEMETRY" className="flex-none h-[180px]">
              <ScoutTelemetry 
                explorationPath={store.explorationPath}
                formDetections={store.formDetections || []}
                captchaResults={store.captchaResults || []}
                pagesScanned={store.stats.pages_scanned}
                domHealth={store.domHealth}
              />
            </TerminalPanel>

            {/* Zone Center Bottom: Log Stream */}
            <TerminalPanel title="SYS.LOG.STREAM" className="flex-1 min-h-[120px]">
              <SysLogStream logs={store.logs} />
            </TerminalPanel>
          </div>

          {/* Right Rail (Evidence, Graphs) */}
          <div className="flex flex-col gap-2 flex-[2.5] min-w-0 min-h-0">
            <TerminalPanel title="SCOUT.IMAGERY" className="flex-none h-[220px]">
              <ScoutImagery screenshots={store.screenshots} />
            </TerminalPanel>
            <TerminalPanel title="VISION.INTELLIGENCE" className="flex-1 min-h-[160px]">
              <VisionIntelligence
                 darkPatterns={store.darkPatternFindings || []}
                 temporal={store.temporalFindings || []}
                 status={store.status}
              />
            </TerminalPanel>
            <TerminalPanel title="KNOWLEDGE.GRAPH" className="flex-1 min-h-[180px]">
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

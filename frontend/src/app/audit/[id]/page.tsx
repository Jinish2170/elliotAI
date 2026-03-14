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
  KnowledgeGraph
} from "@/components/terminal";
import { ChromaticProvider } from "@/components/providers/ChromaticProvider";   
import { useAuditStream } from "@/hooks/useAuditStream";
import type { AgentId } from "@/config/agents";
import { saveAuditToHistory } from "@/components/landing/RecentAudits";

function TerminalHeader({ url, elapsed }: { url?: string, elapsed: number }) {
  return (
    <div className="h-[5vh] border-b border-[var(--t-border)] flex items-center justify-between px-4 bg-[var(--t-panel)] text-[10px] uppercase tracking-widest text-[var(--t-dim)] font-mono">
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
      <div className="veritas-terminal">
        {/* ZONE 1: TACTICAL HEADER */}
        <TerminalHeader url={store.url || undefined} elapsed={store.stats.elapsed_seconds} />

        {/* ZONE 4 (Rails) & ZONES 2/3 (Center) contained in grid */}
        <div className="veritas-terminal-grid">
          
          {/* Left Rail (Log Stream, Tasks) */}
          <div className="flex flex-col gap-[2px]">
            <TerminalPanel title="SYS.LOG.STREAM" className="h-[65%]">
              <SysLogStream logs={store.logs} />
            </TerminalPanel>
            <TerminalPanel title="AGENT.PROC.STATE" className="h-[35%]">
               <AgentProcState phases={store.phases} activePhase={store.currentPhase || undefined} />
            </TerminalPanel>
          </div>

          {/* Center Column (Verdict & Matrix) */}
          <div className="flex flex-col gap-[2px]">
            {/* Zone 2: Verdict */}
            <TerminalPanel title="VERDICT.MATRIX" className="h-[25%] flex justify-center items-center">
              <VerdictPanel 
                verdict={store.result ? { 
                  status: store.status, 
                  risk_level: store.result.risk_level, 
                  narrative: store.result.narrative,
                  signal_scores: store.result.signal_scores
                } : null}
                trustScore={store.result?.trust_score}
              />
            </TerminalPanel>

            {/* Zone 3: Investigative Matrix */}
            <div className="flex-1 grid grid-cols-2 gap-[2px] bg-[var(--t-border)]">
               <TerminalPanel title="CVSS.RADAR" className="h-full">
                 <CvssRadar metrics={(store.result?.security_results?.cvss_metrics as any[]) || []} />
               </TerminalPanel>
               <TerminalPanel title="MITRE.ATTACK.GRID" className="h-full">
                 <MitreGrid techniques={(store.result?.security_results?.mitre_mappings as any[]) || []} />
               </TerminalPanel>
               <TerminalPanel title="DARKNET.OSINT" className="col-span-2 h-full">
                 <DarknetOsintGrid 
                   cves={(store.result?.security_results?.cve_detected as any[]) || []} 
                   tor={store.tor2WebThreats || []}
                   marketplace={store.marketplaceDetails || []}
                 />
               </TerminalPanel>
            </div>
          </div>

          {/* Right Rail (Evidence, Graphs) */}
          <div className="flex flex-col gap-[2px]">
            <TerminalPanel title="SCOUT.IMAGERY" className="h-1/2">
               <ScoutImagery screenshots={store.screenshots} />
            </TerminalPanel>
            <TerminalPanel title="KNOWLEDGE.GRAPH" className="flex-1">
               <KnowledgeGraph findings={store.findings || []} />
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

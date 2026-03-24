"use client";
import React, { useMemo } from "react";
import { GhostPanel } from "./TerminalPanel";
import type { OSINTResult, MarketplaceThreatData } from "@/lib/types";

interface Props {
  osintResults: OSINTResult[];
  marketplaceThreats: MarketplaceThreatData[];
  status?: string;
}

export function ThreatIntelligenceMatrix({ osintResults, marketplaceThreats, status }: Props) {
  const isEmpty = !osintResults?.length && !marketplaceThreats?.length;
  
  const groupedOsint = useMemo(() => {
    if (!osintResults) return [];
    const grouped = new Map<string, any>();
    osintResults.forEach(res => {
      const key = `${res.source}_${res.category}`;
      if (!grouped.has(key)) {
        grouped.set(key, { ...res, queries: [] });
      }
      grouped.get(key).queries.push(res);
    });
    return Array.from(grouped.values());
  }, [osintResults]);

  if (isEmpty) {
    if (status === "complete") {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-[var(--t-green)]/5">
          <span className="text-[var(--t-green)]/50 font-mono text-[11px] uppercase tracking-widest">[ NO EXTERNAL THREATS DETECTED ]</span>
        </div>
      );
    }
    return <GhostPanel message="THREAT MATRIX - DEEP SCANNING" />;
  }

  return (
    <div className="w-full h-full overflow-y-auto p-3 flex flex-col gap-4 align-top items-start">
      {/* OSINT Results */}
      {groupedOsint.length > 0 && (
        <div className="w-full flex-col gap-2 min-w-0">
          <div className="text-[11px] text-[var(--t-amber)] border-b border-[var(--t-amber)] pb-1 shrink-0 mb-2">
            OSINT_RESULTS <span className="opacity-70">[{osintResults.length}]</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {groupedOsint.map((group, i) => (
              <div key={i} className="text-[11px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-amber)] text-left justify-start relative group">
                <span className="font-bold text-[var(--t-amber)]">{(group?.source || "UNKNOWN").toUpperCase()} [{(group?.category || "UNKNOWN").toUpperCase()}]</span>
                <span className="opacity-70 truncate pt-1">{group.queries.length} queries executed</span>
                
                <div className="mt-2 flex flex-col gap-1 overflow-y-auto max-h-[80px]">
                  {group.queries.map((q: any, idx: number) => (
                    <div key={idx} className="flex flex-col border border-[var(--t-border)] p-1 bg-black/40">
                      <span className="text-[10px] text-[var(--t-cyan)] truncate">{q.query_value}</span>
                      <span className="text-[9px]">
                        {q.status.toUpperCase()}
                      </span>
                      {q.data && Object.keys(q.data).length > 0 && (
                        <div className="text-[9px] text-[var(--t-dim)] mt-1 whitespace-pre-wrap break-words">
                          {Object.entries(q.data).slice(0, 3).map(([k, v]) => (
                            <div key={k} className="truncate"><span className="opacity-50">{k}:</span> {String(v)}</div>
                          ))}
                        </div>
                      )}
                      {q.error_message && (
                        <span className="text-[var(--t-red)] text-[9px] truncate">{q.error_message}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Marketplace Threats */}
      {marketplaceThreats?.length > 0 && (
        <div className="w-full flex-col gap-2 min-w-0 mt-2">
          <div className="text-[11px] text-[var(--t-red)] border-b border-[var(--t-red)] pb-1 shrink-0 mb-2">
            MARKETPLACE_THREATS <span className="opacity-70">[{marketplaceThreats.length}]</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {marketplaceThreats.map((threat, i) => (
              <div key={i} className="text-[11px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-red)]">
                <span className="font-bold">{threat?.marketplace_name || "UNKNOWN"}</span>
                <span className="opacity-70 truncate">{threat?.description}</span>
                <span className="text-[var(--t-amber)] mt-1">RISK: {(threat?.threat_level || "UNKNOWN").toUpperCase()} | CONF: {Math.round((threat?.confidence || 0) * 100)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

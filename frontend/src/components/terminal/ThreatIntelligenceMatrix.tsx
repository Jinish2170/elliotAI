"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { OSINTResult, MarketplaceThreatData } from "@/lib/types";

interface Props {
  osintResults: OSINTResult[];
  marketplaceThreats: MarketplaceThreatData[];
  status?: string;
}

export function ThreatIntelligenceMatrix({ osintResults, marketplaceThreats, status }: Props) {
  const isEmpty = !osintResults?.length && !marketplaceThreats?.length;
  if (isEmpty) {
    if (status === "complete") {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-[var(--t-green)]/5">
          <span className="text-[var(--t-green)]/50 font-mono text-[10px] uppercase tracking-widest">[ NO EXTERNAL THREATS DETECTED ]</span>
        </div>
      );
    }
    return <GhostPanel message="THREAT MATRIX - DEEP SCANNING" />;
  }

  return (
    <div className="w-full h-full overflow-y-auto p-3 flex flex-col gap-4 align-top items-start">
      {/* OSINT Results */}
      {osintResults?.length > 0 && (
        <div className="w-full flex-col gap-2 min-w-0">
          <div className="text-[10px] text-[var(--t-amber)] border-b border-[var(--t-amber)] pb-1 shrink-0 mb-2">
            OSINT_RESULTS <span className="opacity-70">[{osintResults.length}]</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {osintResults.map((osint, i) => (
              <div key={i} className="text-[10px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-amber)]">
                <span className="font-bold">{osint.source.toUpperCase()} [{osint.category.toUpperCase()}]</span>
                <span className="opacity-70 truncate pt-1">{osint.query_value}</span>
                <span className={`text-[9px] mt-1 ${osint.status === "error" ? "text-[var(--t-red)]" : "text-[var(--t-green)]"}`}>
                  STATUS: {osint.status.toUpperCase()}
                </span>
                {osint.error_message && (
                  <span className="text-[var(--t-red)] truncate">{osint.error_message}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Marketplace Threats */}
      {marketplaceThreats?.length > 0 && (
        <div className="w-full flex-col gap-2 min-w-0 mt-2">
          <div className="text-[10px] text-[var(--t-red)] border-b border-[var(--t-red)] pb-1 shrink-0 mb-2">
            MARKETPLACE_THREATS <span className="opacity-70">[{marketplaceThreats.length}]</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {marketplaceThreats.map((threat, i) => (
              <div key={i} className="text-[10px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-red)]">
                <span className="font-bold">{threat.marketplace_name}</span>
                <span className="opacity-70 truncate">{threat.description}</span>
                <span className="text-[var(--t-amber)] mt-1">RISK: {threat.threat_level.toUpperCase()} | CONF: {Math.round(threat.confidence * 100)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

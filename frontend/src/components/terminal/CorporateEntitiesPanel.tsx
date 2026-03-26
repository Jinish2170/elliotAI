"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";

export function CorporateEntitiesPanel({ entities, status }: { entities: any[], status?: string }) {
  if (!entities || entities.length === 0) {
    if (status === "complete") {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-[var(--t-green)]/5">
          <span className="text-[var(--t-green)]/50 font-mono text-[11px] uppercase tracking-widest">[ NO ENTITIES VERIFIED ]</span>
        </div>
      );
    }
    return <GhostPanel message="AWAITING ENTITY VERIFICATION" />;
  }

  return (
    <div className="w-full h-full overflow-y-auto p-2">
      <div className="flex flex-col gap-2">
        {entities.map((entity, idx) => (
          <div key={idx} className="border border-[var(--t-dim)] bg-black/20 p-2 text-[10px]">
            <div className="flex justify-between items-start mb-1">
              <span className="text-[var(--t-green)] font-bold">{entity.entity_type}</span>
              <span className={`px-1 py-0.5 border ${
                entity.verification_status === "verified" ? "border-[var(--t-green)] text-[var(--t-green)]" : 
                entity.verification_status === "inconsistent" ? "border-[var(--t-red)] text-[var(--t-red)]" : 
                "border-[var(--t-amber)] text-[var(--t-amber)]"
              }`}>
                {entity.verification_status?.toUpperCase() || "PENDING"}
              </span>
            </div>
            {entity.claim && <div className="text-[var(--t-glow)] mb-1 break-words">Claim: {entity.claim}</div>}
            {entity.fact && <div className="text-white/80 mb-1 break-words">Fact: {entity.fact}</div>}
            {entity.confidence !== undefined && (
              <div className="flex justify-between items-center text-[var(--t-dim)] mt-2 pt-1 border-t border-[var(--t-dim)]/30">
                <span>CONFIDENCE</span>
                <span className={entity.confidence > 0.8 ? "text-[var(--t-green)]" : "text-[var(--t-amber)]"}>
                  {Math.round(entity.confidence * 100)}%
                </span>
              </div>
            )}
            {entity.sources && entity.sources.length > 0 && (
              <div className="text-[8px] text-[var(--t-dim)] mt-1 truncate">
                SRC: {entity.sources.join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
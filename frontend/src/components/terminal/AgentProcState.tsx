"use client";
import React from "react";
import type { PhaseState, Phase } from "@/lib/types";
import { AGENT_ORDER } from "@/config/agents";
import { GhostPanel } from "./TerminalPanel";

export function AgentProcState({ 
  phases, 
  activePhase,
  status
}: { 
  phases: Record<Phase, PhaseState>;
  activePhase: string | undefined;
  status?: string;
}) {
  if (!phases || Object.keys(phases).length === 0) {
    return <GhostPanel message="AGENT_SCHEDULER_INIT" />;
  }

  return (
    <div className="w-full h-full p-2 overflow-y-auto flex flex-col gap-[2px]">
      {AGENT_ORDER.map((agentId) => {
        const pState = phases[agentId as Phase];
        const isComplete = pState?.status === "complete" || status === "complete";
        const isActive = activePhase === agentId && status !== "complete";
        const isError = pState?.status === "error";
        
        let headerColor = "text-[var(--t-dim)] border-[var(--t-border)]";
        let statusText = "STANDBY";
        let barColor = "bg-transparent";

        if (status === "error" && (!isComplete && !isError)) {
          headerColor = "text-[var(--t-dim)] border-[var(--t-red)] border-opacity-50";
          statusText = "ABORTED";
          barColor = "bg-transparent";
        } else if (isActive) {
          headerColor = "text-[var(--t-base)] bg-[var(--t-green)] border-[var(--t-green)]";
          statusText = status === "error" ? "ERR" : "ACTIVE";
          barColor = "bg-[#111]";
          if (status === "error") {
             headerColor = "text-[var(--t-base)] bg-[var(--t-red)] border-[var(--t-red)]";
          }
        } else if (isComplete) {
          headerColor = "text-[var(--t-green)] border-[var(--t-green)]";
          statusText = "DONE";
          barColor = "bg-[#111]";
        } else if (isError) {
          headerColor = "text-[var(--t-base)] bg-[var(--t-red)] border-[var(--t-red)]";
          statusText = "ERR";
          barColor = "bg-[#111]";
        }

        return (
          <div key={agentId} className={`flex flex-col border p-1 ${headerColor} ${barColor} transition-colors duration-300`}>
            <div className="flex justify-between items-center text-[10px] font-bold uppercase">
              <span>{agentId}</span>
              <span className={isActive ? "animate-pulse" : ""}>[{statusText}]</span>
            </div>
            {/* Progress Bar Line */}
            {isActive && (
              <div className="mt-1 w-full bg-[var(--t-base)] h-[2px]">
                 <div className="h-full bg-[var(--t-base)]" style={{ width: `${pState?.pct || 0}%`, transition: 'width 0.3s' }}></div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

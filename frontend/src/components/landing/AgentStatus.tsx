"use client";

import { AGENT_CONFIGS, AGENT_ORDER, type AgentId } from "@/config/agents";

export function AgentStatus() {
  return (
    <div className="flex flex-col h-full">
      <div className="text-[10px] font-mono text-[var(--t-dim)] uppercase tracking-widest border-b border-[var(--t-border)] pb-2 mb-4">
         SYS.AGENT_FLEET_STATUS
      </div>
      <div className="space-y-2 flex-1">
        {AGENT_ORDER.map((agentId) => {
          const agent = AGENT_CONFIGS[agentId as AgentId];
          if (!agent) return null;

          return (
            <div
              key={agentId}
              className="flex items-center justify-between border-l-2 border-[#00FF41] pl-3 py-1 bg-[#111]"
            >
              <div className="flex items-center gap-2.5">
                <div>
                  <div className="text-[11px] font-mono font-bold text-[#00FF41] uppercase tracking-wider">
                    {agent.label}
                  </div>
                  <div className="text-[9px] font-mono text-[var(--t-dim)] leading-tight">
                    {agent.label + " Protocol"}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2 pr-2">
                <span className="text-[9px] font-mono text-[#00FF41] uppercase">ONLINE</span>
                <div className="w-1.5 h-1.5 rounded-full bg-[#00FF41] animate-pulse" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

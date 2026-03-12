"use client";

/* ========================================
   AgentStatus — Agent System Status Panel
   Shows all 5 agents with online/offline
   status indicators. Internal-tool style.
   ======================================== */

import { PanelChrome } from "@/components/layout/PanelChrome";
import { AgentIcon } from "@/components/ui/AgentIcon";
import { AGENT_CONFIGS, AGENT_ORDER, type AgentId } from "@/config/agents";

export function AgentStatus() {
  return (
    <PanelChrome title="Agent Fleet" elevation={2}>
      <div className="space-y-1">
        {AGENT_ORDER.map((agentId) => {
          const agent = AGENT_CONFIGS[agentId as AgentId];
          if (!agent) return null;

          return (
            <div
              key={agentId}
              className="flex items-center justify-between px-3 py-2 rounded hover:bg-[rgba(255,255,255,0.02)] transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <AgentIcon agent={agentId as AgentId} size="sm" state="idle" />
                <div>
                  <span className="text-[12px] font-semibold text-[var(--v-text)]">
                    {agent.label}
                  </span>
                  <span className="block text-[9px] font-mono text-[var(--v-text-tertiary)]">
                    {agent.logPrompt}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[9px] font-mono text-emerald-400 uppercase">
                  READY
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </PanelChrome>
  );
}

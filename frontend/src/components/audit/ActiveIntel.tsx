"use client";

/* ========================================
   ActiveIntel — Center Stage Panel
   Content rotates based on which agent is active.
   Shows agent-specific data views in the War Room center.
   ======================================== */

import { cn } from "@/lib/utils";
import { PanelChrome } from "@/components/layout/PanelChrome";
import { DataFeed } from "@/components/audit/DataFeed";
import { AgentIcon } from "@/components/ui/AgentIcon";
import { AGENT_CONFIGS, type AgentId } from "@/config/agents";
import type { Finding, Phase, LogEntry, Screenshot, PhaseState } from "@/lib/types";
import { useMemo } from "react";

interface ActiveIntelProps {
  currentPhase: Phase | null;
  phases: Record<Phase, PhaseState>;
  findings: Finding[];
  screenshots: Screenshot[];
  logs: LogEntry[];
  status: string;
  trustScore?: number;
  className?: string;
}

export function ActiveIntel({
  currentPhase,
  phases,
  findings,
  screenshots,
  logs,
  status,
  trustScore,
  className,
}: ActiveIntelProps) {
  const activeAgent = (currentPhase && currentPhase !== "init"
    ? currentPhase
    : null) as AgentId | null;

  const config = activeAgent ? AGENT_CONFIGS[activeAgent] : null;

  // Filter findings for active agent context
  const agentFindings = useMemo(() => {
    if (!activeAgent) return findings;
    // Show all findings — the DataFeed handles display
    return findings;
  }, [findings, activeAgent]);

  // Agent-specific status line
  const statusLine = useMemo(() => {
    if (!activeAgent) return "STANDING BY";
    const phase = phases[activeAgent];
    if (!phase) return "STANDING BY";
    if (phase.status === "active") return phase.message || "ANALYZING...";
    if (phase.status === "complete") return "PHASE COMPLETE";
    if (phase.status === "error") return `ERROR: ${phase.error || "Unknown"}`;
    return "WAITING";
  }, [activeAgent, phases]);

  return (
    <PanelChrome
      title={activeAgent ? `${activeAgent.toUpperCase()} INTEL` : "ACTIVE INTEL"}
      icon={
        activeAgent ? (
          <AgentIcon agent={activeAgent} size="sm" state="active" />
        ) : undefined
      }
      accentColor={config?.color.primary}
      elevation={2}
      className={cn("flex flex-col h-full", className)}
      contentClassName="flex-1 flex flex-col min-h-0"
    >
      {/* Agent banner */}
      <div
        className="flex items-center justify-between px-3 py-1.5 border-b"
        style={{
          borderColor: config
            ? `${config.color.primary}20`
            : "rgba(255,255,255,0.04)",
          background: config
            ? `linear-gradient(90deg, ${config.color.primary}08, transparent)`
            : undefined,
        }}
      >
        <div className="flex items-center gap-2">
          {activeAgent && (
            <div
              className="w-1.5 h-1.5 rounded-full"
              style={{
                background: config?.color.primary,
                boxShadow:
                  phases[activeAgent]?.status === "active"
                    ? `0 0 6px ${config?.color.primary}`
                    : undefined,
              }}
            />
          )}
          <span className="text-[10px] font-mono text-[var(--v-text-tertiary)] tracking-wider">
            {activeAgent
              ? `${activeAgent.toUpperCase()} AGENT ACTIVE`
              : status === "complete"
              ? "ANALYSIS COMPLETE"
              : "WAITING FOR AGENT"}
          </span>
        </div>
        <span className="text-[10px] font-mono text-[var(--v-text-tertiary)]">
          {statusLine}
        </span>
      </div>

      {/* Main content area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <DataFeed
          currentPhase={currentPhase}
          findings={agentFindings}
          screenshots={screenshots}
          logs={logs}
          status={status}
          className="h-full"
        />
      </div>

      {/* Bottom status bar */}
      <div className="flex items-center justify-between px-3 py-1 border-t border-[rgba(255,255,255,0.04)] bg-[rgba(0,0,0,0.2)]">
        <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
          {findings.length} findings · {screenshots.length} screenshots
        </span>
        {trustScore !== undefined && (
          <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
            Score: {trustScore}/100
          </span>
        )}
      </div>
    </PanelChrome>
  );
}

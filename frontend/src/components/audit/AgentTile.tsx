"use client";

/* ========================================
   AgentTile — Compact Agent Status Card
   Left sidebar tile: icon-in-container + name
   + mini progress bar + key stat + status badge.
   Replaces the old AgentCard component.
   ======================================== */

import { cn } from "@/lib/utils";
import { AgentIcon, type AgentIconState } from "@/components/ui/AgentIcon";
import { AGENT_CONFIGS, type AgentId } from "@/config/agents";
import type { PhaseStatus } from "@/lib/types";

interface AgentTileProps {
  agent: AgentId;
  status: PhaseStatus;
  /** Primary stat line (e.g., "12 pages", "3 findings") */
  stat?: string;
  /** Phase progress 0-100 */
  progress?: number;
  /** Is this agent currently active? */
  isActive?: boolean;
  className?: string;
  onClick?: () => void;
}

function phaseStatusToIconState(status: PhaseStatus): AgentIconState {
  switch (status) {
    case "active": return "active";
    case "complete": return "complete";
    case "error": return "error";
    default: return "idle";
  }
}

function statusLabel(status: PhaseStatus): string {
  switch (status) {
    case "waiting": return "STANDBY";
    case "active": return "RUNNING";
    case "complete": return "COMPLETE";
    case "error": return "ERROR";
  }
}

function statusColor(status: PhaseStatus): string {
  switch (status) {
    case "waiting": return "rgba(255,255,255,0.25)";
    case "active": return "var(--agent-primary, #06B6D4)";
    case "complete": return "#10B981";
    case "error": return "#EF4444";
  }
}

export function AgentTile({
  agent,
  status,
  stat,
  progress = 0,
  isActive = false,
  className,
  onClick,
}: AgentTileProps) {
  const config = AGENT_CONFIGS[agent];

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full text-left px-2.5 py-2 rounded-lg transition-all duration-200",
        "hover:bg-[rgba(255,255,255,0.03)]",
        isActive
          ? "bg-[var(--agent-bg-subtle)] border border-[var(--agent-border-subtle)]"
          : "bg-transparent border border-transparent",
        className
      )}
      aria-label={`${config.label} agent — ${statusLabel(status)}`}
    >
      <div className="flex items-center gap-2.5">
        {/* Agent icon */}
        <AgentIcon
          agent={agent}
          state={phaseStatusToIconState(status)}
          size="md"
        />

        {/* Text content */}
        <div className="flex-1 min-w-0">
          {/* Name + status */}
          <div className="flex items-center justify-between gap-2">
            <span
              className={cn(
                "text-xs font-medium truncate",
                isActive ? "text-[var(--v-text)]" : "text-[var(--v-text-secondary)]"
              )}
            >
              {config.label}
            </span>
            <span
              className="text-badge shrink-0"
              style={{ color: statusColor(status) }}
            >
              {statusLabel(status)}
            </span>
          </div>

          {/* Progress bar */}
          <div className="mt-1.5 h-1 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-300 ease-out"
              style={{
                width: `${Math.min(100, Math.max(0, progress))}%`,
                backgroundColor:
                  status === "complete"
                    ? "#10B981"
                    : status === "error"
                      ? "#EF4444"
                      : isActive
                        ? config.color.primary
                        : "rgba(255,255,255,0.15)",
              }}
            />
          </div>

          {/* Stat line */}
          {stat && (
            <p className="mt-1 text-[10px] font-mono text-[var(--v-text-tertiary)] truncate">
              {stat}
            </p>
          )}
        </div>
      </div>
    </button>
  );
}

"use client";

/* ========================================
   AgentIcon — Premium Agent Identity Renderer
   Lucide icon inside a colored rounded-square container.
   Supports 4 visual states: idle, active, complete, error.
   ======================================== */

import { cn } from "@/lib/utils";
import { AGENT_CONFIGS, type AgentId } from "@/config/agents";
import {
  Radar,
  ShieldCheck,
  ScanEye,
  Network,
  Scale,
  AlertCircle,
  CheckCircle2,
  type LucideProps,
} from "lucide-react";
import { type ComponentType } from "react";

export type AgentIconState = "idle" | "active" | "complete" | "error";
export type AgentIconSize = "sm" | "md" | "lg" | "xl";

const ICON_MAP: Record<string, ComponentType<LucideProps>> = {
  Radar,
  ShieldCheck,
  ScanEye,
  Network,
  Scale,
};

const SIZE_CONFIG: Record<AgentIconSize, { container: number; icon: number; badge: number }> = {
  sm: { container: 24, icon: 14, badge: 8 },
  md: { container: 32, icon: 16, badge: 10 },
  lg: { container: 40, icon: 20, badge: 12 },
  xl: { container: 52, icon: 28, badge: 14 },
};

interface AgentIconProps {
  agent: AgentId;
  state?: AgentIconState;
  size?: AgentIconSize;
  className?: string;
}

export function AgentIcon({
  agent,
  state = "idle",
  size = "md",
  className,
}: AgentIconProps) {
  const config = AGENT_CONFIGS[agent];
  const sizeConfig = SIZE_CONFIG[size];
  const IconComponent = ICON_MAP[config.icon];

  if (!IconComponent) return null;

  const isActive = state === "active";
  const isComplete = state === "complete";
  const isError = state === "error";

  // Container styles based on state
  const containerBg = isError
    ? "rgba(239,68,68,0.10)"
    : isActive
      ? config.color.bgSubtle.replace("0.10", "0.20")
      : config.color.bgSubtle;

  const containerBorder = isError
    ? "rgba(239,68,68,0.25)"
    : isActive
      ? config.color.borderSubtle.replace("0.20", "0.35")
      : config.color.borderSubtle;

  const iconColor = isError
    ? "#EF4444"
    : state === "idle"
      ? `${config.color.primary}66` // 40% opacity
      : isComplete
        ? `${config.color.primary}99` // 60% opacity
        : config.color.primary; // 100%

  return (
    <div
      className={cn(
        "relative inline-flex items-center justify-center rounded-lg shrink-0",
        "transition-all duration-150 ease-out",
        isActive && "shadow-[var(--agent-icon-glow)]",
        className
      )}
      style={{
        width: sizeConfig.container,
        height: sizeConfig.container,
        backgroundColor: containerBg,
        border: `1px solid ${containerBorder}`,
        ["--agent-icon-glow" as string]: isActive
          ? `0 0 12px ${config.color.primary}33`
          : "none",
      }}
    >
      {/* Main icon — or error fallback */}
      {isError ? (
        <AlertCircle
          style={{ color: "#EF4444" }}
          width={sizeConfig.icon}
          height={sizeConfig.icon}
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <IconComponent
          style={{ color: iconColor }}
          width={sizeConfig.icon}
          height={sizeConfig.icon}
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}

      {/* Completion badge */}
      {isComplete && (
        <div
          className="absolute flex items-center justify-center rounded-full"
          style={{
            width: sizeConfig.badge,
            height: sizeConfig.badge,
            bottom: -2,
            right: -2,
            backgroundColor: "#080A0F",
          }}
        >
          <CheckCircle2
            style={{ color: config.color.primary }}
            width={sizeConfig.badge - 2}
            height={sizeConfig.badge - 2}
            strokeWidth={2}
          />
        </div>
      )}
    </div>
  );
}

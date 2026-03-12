/* ========================================
   Veritas — Agent Configuration
   Centralized agent identity, colors, and icon assignments
   Used by ChromaticProvider, AgentIcon, AgentTile, etc.
   ======================================== */

import type { Phase } from "@/lib/types";

export type AgentId = Exclude<Phase, "init">;

export interface AgentConfig {
  id: AgentId;
  label: string;
  icon: string; // Lucide icon name
  color: {
    primary: string;
    glow: string;
    tint: string;
    border: string;
    text: string;
    bgSubtle: string;
    borderSubtle: string;
  };
  logPrompt: string;
}

export const AGENT_CONFIGS: Record<AgentId, AgentConfig> = {
  scout: {
    id: "scout",
    label: "Scout",
    icon: "Radar",
    color: {
      primary: "#06D6A0",
      glow: "0 0 40px rgba(6,214,160,0.3)",
      tint: "radial-gradient(ellipse at 30% 50%, rgba(6,214,160,0.08), transparent 60%)",
      border: "rgba(6,214,160,0.4)",
      text: "rgba(6,214,160,0.9)",
      bgSubtle: "rgba(6,214,160,0.10)",
      borderSubtle: "rgba(6,214,160,0.20)",
    },
    logPrompt: "scout",
  },
  security: {
    id: "security",
    label: "Security",
    icon: "ShieldCheck",
    color: {
      primary: "#10B981",
      glow: "0 0 40px rgba(16,185,129,0.3)",
      tint: "radial-gradient(ellipse at 70% 30%, rgba(16,185,129,0.08), transparent 60%)",
      border: "rgba(16,185,129,0.4)",
      text: "rgba(16,185,129,0.9)",
      bgSubtle: "rgba(16,185,129,0.10)",
      borderSubtle: "rgba(16,185,129,0.20)",
    },
    logPrompt: "security",
  },
  vision: {
    id: "vision",
    label: "Vision",
    icon: "ScanEye",
    color: {
      primary: "#8B5CF6",
      glow: "0 0 40px rgba(139,92,246,0.3)",
      tint: "radial-gradient(ellipse at 50% 70%, rgba(139,92,246,0.08), transparent 60%)",
      border: "rgba(139,92,246,0.4)",
      text: "rgba(139,92,246,0.9)",
      bgSubtle: "rgba(139,92,246,0.10)",
      borderSubtle: "rgba(139,92,246,0.20)",
    },
    logPrompt: "vision",
  },
  graph: {
    id: "graph",
    label: "Graph",
    icon: "Network",
    color: {
      primary: "#F59E0B",
      glow: "0 0 40px rgba(245,158,11,0.3)",
      tint: "radial-gradient(ellipse at 60% 40%, rgba(245,158,11,0.08), transparent 60%)",
      border: "rgba(245,158,11,0.4)",
      text: "rgba(245,158,11,0.9)",
      bgSubtle: "rgba(245,158,11,0.10)",
      borderSubtle: "rgba(245,158,11,0.20)",
    },
    logPrompt: "graph",
  },
  judge: {
    id: "judge",
    label: "Judge",
    icon: "Scale",
    color: {
      primary: "#EF4444",
      glow: "0 0 40px rgba(239,68,68,0.3)",
      tint: "radial-gradient(ellipse at 50% 50%, rgba(239,68,68,0.08), transparent 60%)",
      border: "rgba(239,68,68,0.4)",
      text: "rgba(239,68,68,0.9)",
      bgSubtle: "rgba(239,68,68,0.10)",
      borderSubtle: "rgba(239,68,68,0.20)",
    },
    logPrompt: "judge",
  },
} as const;

export const AGENT_ORDER: AgentId[] = ["scout", "security", "vision", "graph", "judge"];

/** Verdict classification thresholds and colors */
export const VERDICT_COLORS = {
  safe: { text: "#10B981", bg: "rgba(16,185,129,0.08)", border: "rgba(16,185,129,0.3)" },
  caution: { text: "#F59E0B", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.3)" },
  suspicious: { text: "#EF4444", bg: "rgba(239,68,68,0.08)", border: "rgba(239,68,68,0.3)" },
  dangerous: { text: "#DC2626", bg: "rgba(220,38,38,0.10)", border: "rgba(220,38,38,0.35)" },
} as const;

export type VerdictLevel = keyof typeof VERDICT_COLORS;

export function getVerdictLevel(score: number): VerdictLevel {
  if (score >= 70) return "safe";
  if (score >= 50) return "caution";
  if (score >= 25) return "suspicious";
  return "dangerous";
}

export function getVerdictLabel(score: number): string {
  const level = getVerdictLevel(score);
  return level.charAt(0).toUpperCase() + level.slice(1);
}

/** Severity configuration for consistent visual rendering */
export const SEVERITY_CONFIG = {
  critical: {
    color: "#EF4444",
    bg: "rgba(239,68,68,0.12)",
    border: "rgba(239,68,68,0.3)",
    icon: "ShieldAlert" as const,
    label: "CRITICAL",
    stripeWidth: 3,
  },
  high: {
    color: "#F59E0B",
    bg: "rgba(245,158,11,0.08)",
    border: "rgba(245,158,11,0.25)",
    icon: "AlertTriangle" as const,
    label: "HIGH",
    stripeWidth: 3,
  },
  medium: {
    color: "#3B82F6",
    bg: "rgba(59,130,246,0.06)",
    border: "rgba(59,130,246,0.2)",
    icon: "Info" as const,
    label: "MEDIUM",
    stripeWidth: 2,
  },
  low: {
    color: "#6B7280",
    bg: "rgba(107,114,128,0.06)",
    border: "rgba(107,114,128,0.15)",
    icon: "Minus" as const,
    label: "LOW",
    stripeWidth: 1,
  },
  pass: {
    color: "#10B981",
    bg: "rgba(16,185,129,0.06)",
    border: "rgba(16,185,129,0.2)",
    icon: "CheckCircle2" as const,
    label: "PASS",
    stripeWidth: 2,
  },
} as const;

export type SeverityLevel = keyof typeof SEVERITY_CONFIG;

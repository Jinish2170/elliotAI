"use client";

/* ========================================
   RecommendationsPanel — Action Items
   Structured recommendation list with
   priority indicators. PanelChrome wrapper.
   ======================================== */

import { PanelChrome } from "@/components/layout/PanelChrome";
import { AlertCircle, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface RecommendationsPanelProps {
  recommendations: string[];
  className?: string;
}

const PRIORITY = [
  { icon: AlertCircle, color: "text-red-400", borderColor: "border-red-500/15", bg: "bg-red-500/[0.03]", label: "HIGH" },
  { icon: AlertCircle, color: "text-red-400", borderColor: "border-red-500/15", bg: "bg-red-500/[0.03]", label: "HIGH" },
  { icon: AlertTriangle, color: "text-amber-400", borderColor: "border-amber-500/15", bg: "bg-amber-500/[0.03]", label: "MEDIUM" },
  { icon: AlertTriangle, color: "text-amber-400", borderColor: "border-amber-500/15", bg: "bg-amber-500/[0.03]", label: "MEDIUM" },
  { icon: Info, color: "text-blue-400", borderColor: "border-blue-500/15", bg: "bg-blue-500/[0.03]", label: "LOW" },
];

export function RecommendationsPanel({ recommendations, className }: RecommendationsPanelProps) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <PanelChrome
      title="Recommendations"
      count={recommendations.length}
      elevation={2}
      className={className}
    >
      <div className="space-y-1.5">
        {recommendations.map((rec, i) => {
          const pri = PRIORITY[Math.min(i, PRIORITY.length - 1)];
          const Icon = pri.icon;

          return (
            <div
              key={i}
              className={cn(
                "flex items-start gap-3 px-3 py-2.5 rounded border",
                pri.borderColor,
                pri.bg
              )}
            >
              <div className="flex items-center gap-2 shrink-0 pt-0.5">
                <Icon className={cn("w-3.5 h-3.5", pri.color)} />
                <span className={cn("text-[9px] font-mono font-bold tracking-wider", pri.color)}>
                  {pri.label}
                </span>
              </div>
              <p className="text-[13px] text-[var(--v-text-secondary)] leading-relaxed">
                {rec}
              </p>
            </div>
          );
        })}
      </div>
    </PanelChrome>
  );
}

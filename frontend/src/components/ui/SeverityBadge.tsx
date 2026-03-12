"use client";

/* ========================================
   SeverityBadge — Consistent Severity Rendering
   Color + icon + label badge used everywhere severity appears.
   ======================================== */

import { cn } from "@/lib/utils";
import { SEVERITY_CONFIG, type SeverityLevel } from "@/config/agents";
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  Minus,
  CheckCircle2,
  type LucideProps,
} from "lucide-react";
import { type ComponentType } from "react";

const ICON_MAP: Record<string, ComponentType<LucideProps>> = {
  ShieldAlert,
  AlertTriangle,
  Info,
  Minus,
  CheckCircle2,
};

type BadgeVariant = "solid" | "outlined" | "minimal";
type BadgeSize = "sm" | "md";

interface SeverityBadgeProps {
  severity: SeverityLevel;
  variant?: BadgeVariant;
  size?: BadgeSize;
  className?: string;
  /** Show just icon, no label text */
  iconOnly?: boolean;
}

export function SeverityBadge({
  severity,
  variant = "solid",
  size = "sm",
  className,
  iconOnly = false,
}: SeverityBadgeProps) {
  const config = SEVERITY_CONFIG[severity];
  const IconComponent = ICON_MAP[config.icon];

  const isSm = size === "sm";
  const iconSize = isSm ? 10 : 12;

  const baseClasses = cn(
    "inline-flex items-center gap-1 font-mono shrink-0 select-none",
    isSm ? "text-[9px] tracking-[0.08em] px-1.5 py-0.5 rounded" : "text-[10px] tracking-[0.06em] px-2 py-0.5 rounded",
  );

  const variantStyles = (() => {
    switch (variant) {
      case "solid":
        return {
          backgroundColor:
            severity === "critical" || severity === "high"
              ? config.color
              : config.bg,
          color:
            severity === "critical"
              ? "#FFFFFF"
              : severity === "high"
                ? "#000000"
                : config.color,
          border: "none",
        };
      case "outlined":
        return {
          backgroundColor: "transparent",
          color: config.color,
          border: `1px solid ${config.border}`,
        };
      case "minimal":
        return {
          backgroundColor: config.bg,
          color: config.color,
          border: "none",
        };
    }
  })();

  return (
    <span className={cn(baseClasses, className)} style={variantStyles}>
      {IconComponent && (
        <IconComponent
          width={iconSize}
          height={iconSize}
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ color: variant === "solid" && (severity === "critical" || severity === "high") ? "currentColor" : config.color }}
        />
      )}
      {!iconOnly && <span className="font-semibold">{config.label}</span>}
    </span>
  );
}

/* ========================================
   SeverityStripe — Left border stripe for finding rows
   ======================================== */

interface SeverityStripeProps {
  severity: SeverityLevel;
  className?: string;
}

export function SeverityStripe({ severity, className }: SeverityStripeProps) {
  const config = SEVERITY_CONFIG[severity];

  return (
    <div
      className={cn("shrink-0 rounded-full self-stretch", className)}
      style={{
        width: config.stripeWidth,
        backgroundColor: config.color,
      }}
    />
  );
}

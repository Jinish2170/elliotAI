import { cn } from "@/lib/utils";
import { RISK_COLORS, RISK_LABELS } from "@/lib/types";

interface RiskBadgeProps {
  riskLevel: string;
  className?: string;
}

export function RiskBadge({ riskLevel, className }: RiskBadgeProps) {
  const color = RISK_COLORS[riskLevel] || "#9CA3AF";
  const label = RISK_LABELS[riskLevel] || riskLevel;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border",
        className
      )}
      style={{
        color,
        backgroundColor: `${color}15`,
        borderColor: `${color}30`,
      }}
    >
      <span
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  );
}

import { cn } from "@/lib/utils";

const SEVERITY_CONFIG = {
  low: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/20", label: "Low" },
  medium: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/20", label: "Medium" },
  high: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/20", label: "High" },
  critical: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/20", label: "Critical" },
};

interface SeverityBadgeProps {
  severity: "low" | "medium" | "high" | "critical";
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const cfg = SEVERITY_CONFIG[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border",
        cfg.bg,
        cfg.text,
        cfg.border,
        className
      )}
    >
      {cfg.label}
    </span>
  );
}

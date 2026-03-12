"use client";

/* ========================================
   ExecSummary — Executive Summary Section
   Trust score gauge + risk classification +
   narrative in institutional style.
   ======================================== */

import { cn } from "@/lib/utils";
import { PanelChrome } from "@/components/layout/PanelChrome";
import { getVerdictLevel, getVerdictLabel, VERDICT_COLORS } from "@/config/agents";
import { TrustGauge } from "@/components/data-display/TrustGauge";
import { ShieldAlert, ShieldCheck, AlertTriangle, Shield } from "lucide-react";

interface ExecSummaryProps {
  score: number;
  riskLevel: string;
  narrative: string;
  url: string;
  siteType?: string;
  findingsCount: number;
  screenshotsCount: number;
  elapsedSeconds?: number;
  className?: string;
}

const RISK_ICONS: Record<string, React.ReactNode> = {
  dangerous: <ShieldAlert className="w-5 h-5" />,
  suspicious: <AlertTriangle className="w-5 h-5" />,
  caution: <Shield className="w-5 h-5" />,
  safe: <ShieldCheck className="w-5 h-5" />,
};

export function ExecSummary({
  score,
  riskLevel,
  narrative,
  url,
  siteType,
  findingsCount,
  screenshotsCount,
  elapsedSeconds,
  className,
}: ExecSummaryProps) {
  const level = getVerdictLevel(score);
  const label = getVerdictLabel(score);
  const colors = VERDICT_COLORS[level];

  return (
    <PanelChrome title="Executive Summary" elevation={2} className={className}>
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Score + Classification */}
        <div className="flex flex-col items-center gap-3 lg:w-[200px] shrink-0">
          <TrustGauge score={score} size={160} animate={true} />
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border"
            style={{
              borderColor: colors.border,
              background: colors.bg,
              color: colors.text,
            }}
          >
            {RISK_ICONS[level] || <Shield className="w-5 h-5" />}
            <span className="text-[11px] font-mono font-bold uppercase tracking-wider">
              {label}
            </span>
          </div>
          <span className="text-[10px] font-mono text-[var(--v-text-tertiary)] uppercase">
            {riskLevel}
          </span>
        </div>

        {/* Detail */}
        <div className="flex-1 min-w-0">
          {/* Target */}
          <div className="mb-4 pb-3 border-b border-[rgba(255,255,255,0.04)]">
            <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--v-text-tertiary)]">
              Target URL
            </span>
            <p className="text-[14px] font-mono text-[var(--v-text)] mt-0.5 break-all">
              {url}
            </p>
            {siteType && (
              <span className="text-[10px] font-mono text-[var(--v-text-tertiary)] mt-1 inline-block">
                Classified as: {siteType}
              </span>
            )}
          </div>

          {/* Narrative */}
          <p className="text-[13px] text-[var(--v-text-secondary)] leading-relaxed mb-4">
            {narrative}
          </p>

          {/* Quick stats */}
          <div className="flex flex-wrap gap-4">
            <QuickStat label="FINDINGS" value={String(findingsCount)} />
            <QuickStat label="SCREENSHOTS" value={String(screenshotsCount)} />
            {elapsedSeconds != null && (
              <QuickStat
                label="DURATION"
                value={`${Math.floor(elapsedSeconds / 60)}m ${elapsedSeconds % 60}s`}
              />
            )}
          </div>
        </div>
      </div>
    </PanelChrome>
  );
}

function QuickStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-1.5">
      <span className="text-[18px] font-mono font-bold text-[var(--v-text)] tabular-nums">
        {value}
      </span>
      <span className="text-[9px] uppercase tracking-wider text-[var(--v-text-tertiary)]">
        {label}
      </span>
    </div>
  );
}

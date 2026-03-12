"use client";

/* ========================================
   MetadataGrid — Audit Metadata Section
   Compact grid of audit facts in PanelChrome.
   ======================================== */

import { PanelChrome } from "@/components/layout/PanelChrome";
import type { AuditResult } from "@/lib/types";
import { AlertTriangle, AlertCircle } from "lucide-react";

interface MetadataGridProps {
  result: AuditResult;
  auditId: string;
  className?: string;
}

export function MetadataGrid({ result, auditId, className }: MetadataGridProps) {
  const tierLabel = (result.audit_tier || "standard_audit").replace(/_/g, " ");
  const rows = [
    { label: "Audit ID", value: auditId },
    { label: "Tier", value: tierLabel },
    {
      label: "Duration",
      value: `${Math.floor(result.elapsed_seconds / 60)}m ${result.elapsed_seconds % 60}s`,
    },
    { label: "Pages", value: String(result.pages_scanned) },
    { label: "Screenshots", value: String(result.screenshots_count) },
    {
      label: "Site Type",
      value: `${result.site_type} (${Math.round(result.site_type_confidence * 100)}%)`,
    },
    { label: "Findings", value: String(result.findings.length) },
    { label: "Verdict", value: result.verdict_mode },
  ];

  return (
    <PanelChrome title="Audit Metadata" elevation={2} className={className}>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {rows.map((row) => (
          <div key={row.label}>
            <span className="text-[9px] uppercase tracking-[0.15em] text-[var(--v-text-tertiary)] block mb-0.5">
              {row.label}
            </span>
            <span className="text-[13px] font-mono text-[var(--v-text)]">
              {row.value}
            </span>
          </div>
        ))}
      </div>

      {/* Errors */}
      {result.errors && result.errors.length > 0 && (
        <div className="mt-4 pt-3 border-t border-[rgba(255,255,255,0.04)]">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-3.5 h-3.5 text-red-400" />
            <h4 className="text-[10px] uppercase tracking-[0.15em] font-bold text-red-400">
              Errors
            </h4>
          </div>
          <div className="space-y-1">
            {result.errors.map((err, i) => (
              <p
                key={i}
                className="text-[11px] font-mono text-[var(--v-text-secondary)] px-2 py-1 rounded bg-red-500/[0.04] border border-red-500/10"
              >
                {err}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Overrides */}
      {result.overrides && result.overrides.length > 0 && (
        <div className="mt-4 pt-3 border-t border-[rgba(255,255,255,0.04)]">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <h4 className="text-[10px] uppercase tracking-[0.15em] font-bold text-amber-400">
              Score Overrides
            </h4>
          </div>
          <div className="space-y-1">
            {result.overrides.map((ov, i) => (
              <p
                key={i}
                className="text-[11px] text-[var(--v-text-secondary)] px-2 py-1 rounded bg-amber-500/[0.04] border border-amber-500/10"
              >
                {ov}
              </p>
            ))}
          </div>
        </div>
      )}
    </PanelChrome>
  );
}

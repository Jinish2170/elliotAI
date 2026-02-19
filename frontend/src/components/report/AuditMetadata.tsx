"use client";

import type { AuditResult } from "@/lib/types";
import { motion } from "framer-motion";

interface AuditMetadataProps {
  result: AuditResult;
  auditId: string;
}

export function AuditMetadata({ result, auditId }: AuditMetadataProps) {
  const tierLabel = (result.audit_tier || "standard_audit").replace(/_/g, " ");
  const rows = [
    { label: "Audit ID", value: auditId },
    { label: "Tier", value: tierLabel },
    { label: "Duration", value: `${Math.floor(result.elapsed_seconds / 60)}m ${result.elapsed_seconds % 60}s` },
    { label: "Pages Analyzed", value: String(result.pages_scanned) },
    { label: "Screenshots", value: String(result.screenshots_count) },
    { label: "Site Type", value: `${result.site_type} (${Math.round(result.site_type_confidence * 100)}%)` },
    { label: "Findings", value: String(result.findings.length) },
    { label: "Verdict Mode", value: result.verdict_mode },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.6 }}
      className="glass-card rounded-2xl p-8 mb-6"
    >
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold mb-6">
        Audit Metadata
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {rows.map((row) => (
          <div key={row.label}>
            <p className="text-[10px] uppercase tracking-wider text-[var(--v-text-tertiary)] mb-0.5">
              {row.label}
            </p>
            <p className="text-sm text-[var(--v-text)] font-mono">{row.value}</p>
          </div>
        ))}
      </div>

      {/* Errors */}
      {result.errors && result.errors.length > 0 && (
        <div className="mt-6 pt-4 border-t border-white/5">
          <h3 className="text-xs font-semibold text-red-400 mb-2">Errors During Audit</h3>
          <div className="space-y-1">
            {result.errors.map((err, i) => (
              <p key={i} className="text-xs text-[var(--v-text-secondary)] font-mono">
                {err}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Overrides */}
      {result.overrides && result.overrides.length > 0 && (
        <div className="mt-4 pt-4 border-t border-white/5">
          <h3 className="text-xs font-semibold text-amber-400 mb-2">Score Overrides Applied</h3>
          <div className="space-y-1">
            {result.overrides.map((ov, i) => (
              <p key={i} className="text-xs text-[var(--v-text-secondary)]">
                ⚠️ {ov}
              </p>
            ))}
          </div>
        </div>
      )}
    </motion.section>
  );
}

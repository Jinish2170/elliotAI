"use client";

import { motion } from "framer-motion";

interface SecurityPanelProps {
  securityResults: Record<string, unknown>;
  mode: "simple" | "expert";
}

export function SecurityPanel({ securityResults, mode }: SecurityPanelProps) {
  // Parse security results
  const headers: { name: string; present: boolean; value?: string }[] = [];
  const phishingChecks: { source: string; flagged: boolean }[] = [];
  const formIssues: string[] = [];

  // Extract header info if available
  if (securityResults) {
    const hr = securityResults as Record<string, unknown>;

    // Try to extract headers
    if (hr.headers && typeof hr.headers === "object") {
      const h = hr.headers as Record<string, string | boolean>;
      const headerNames = [
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "Content-Security-Policy",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
      ];
      for (const name of headerNames) {
        const key = name.toLowerCase().replace(/-/g, "_");
        headers.push({
          name,
          present: !!h[key] || !!h[name],
          value: typeof h[key] === "string" ? h[key] as string : undefined,
        });
      }
    }

    // If no structured data, show a general status
    if (headers.length === 0) {
      // Fallback: iterate over what we have
      Object.entries(hr).forEach(([key, value]) => {
        if (key !== "headers" && key !== "phishing" && key !== "forms") {
          headers.push({
            name: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
            present: value !== null && value !== false,
            value: typeof value === "string" ? value : undefined,
          });
        }
      });
    }
  }

  const presentCount = headers.filter((h) => h.present).length;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.4 }}
      className="glass-card rounded-2xl p-8 mb-6"
    >
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold mb-6">
        Security Audit
      </h2>

      {/* Headers */}
      {headers.length > 0 && (
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-[var(--v-text-secondary)] mb-3">
            HTTP Security Headers ({presentCount}/{headers.length})
          </h3>
          <div className="space-y-2">
            {headers.map((h, i) => (
              <motion.div
                key={h.name}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.08 }}
                className="flex items-center justify-between py-1.5"
              >
                <div className="flex items-center gap-2">
                  <span className={h.present ? "text-emerald-400" : "text-red-400"}>
                    {h.present ? "✅" : "❌"}
                  </span>
                  <span className={`text-sm ${mode === "expert" ? "font-mono" : ""} text-[var(--v-text)]`}>
                    {h.name}
                  </span>
                </div>
                {mode === "expert" && h.value && (
                  <span className="text-xs text-[var(--v-text-tertiary)] font-mono truncate max-w-[200px]">
                    {h.value}
                  </span>
                )}
                {!h.present && (
                  <span className="text-[10px] text-red-400 font-medium">MISSING</span>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Phishing checks */}
      {phishingChecks.length > 0 && (
        <div className="mb-6 pt-4 border-t border-white/5">
          <h3 className="text-xs font-semibold text-[var(--v-text-secondary)] mb-3">
            Phishing Database Check
          </h3>
          <div className="space-y-2">
            {phishingChecks.map((check) => (
              <div key={check.source} className="flex items-center gap-2 text-sm">
                <span className={check.flagged ? "text-red-400" : "text-emerald-400"}>
                  {check.flagged ? "🔴" : "✅"}
                </span>
                <span className="text-[var(--v-text)]">
                  {check.flagged ? "Found in" : "Not found in"} {check.source}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Form issues */}
      {formIssues.length > 0 && (
        <div className="pt-4 border-t border-white/5">
          <h3 className="text-xs font-semibold text-[var(--v-text-secondary)] mb-3">
            Form Security
          </h3>
          <div className="space-y-2">
            {formIssues.map((issue, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span className="text-amber-400 mt-0.5">⚠️</span>
                <span className="text-[var(--v-text-secondary)]">{issue}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {headers.length === 0 && phishingChecks.length === 0 && formIssues.length === 0 && (
        <p className="text-sm text-[var(--v-text-tertiary)] text-center py-4">
          Security data not available
        </p>
      )}
    </motion.section>
  );
}

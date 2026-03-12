"use client";

/* ========================================
   SecurityMatrix — Pass/Fail Grid
   Replaces card-based SecurityPanel with
   structured grid layout.
   ======================================== */

import { cn } from "@/lib/utils";
import { PanelChrome } from "@/components/layout/PanelChrome";
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Lock, Globe, FileWarning } from "lucide-react";

interface SecurityMatrixProps {
  securityResults: Record<string, unknown>;
  className?: string;
}

interface HeaderCheck {
  name: string;
  present: boolean;
  value?: string;
}

interface PhishingCheck {
  source: string;
  flagged: boolean;
}

function parseSecurityResults(sr: Record<string, unknown>) {
  const headers: HeaderCheck[] = [];
  const phishingChecks: PhishingCheck[] = [];
  const formIssues: string[] = [];

  // Structured security headers
  const securityHeaders = sr.security_headers as Record<string, unknown> | undefined;
  const headerChecks = Array.isArray(securityHeaders?.checks)
    ? (securityHeaders.checks as Array<Record<string, unknown>>)
    : [];
  for (const check of headerChecks) {
    headers.push({
      name: String(check.header || "Unknown"),
      present: Boolean(check.present),
      value: typeof check.value === "string" ? check.value : undefined,
    });
  }

  // Phishing
  const phishing = sr.phishing as Record<string, unknown> | undefined;
  if (phishing) {
    const sources = Array.isArray(phishing.sources) ? phishing.sources : [];
    if (sources.length > 0) {
      for (const source of sources) {
        phishingChecks.push({ source: String(source), flagged: true });
      }
    } else {
      phishingChecks.push({
        source: "Heuristic Analysis",
        flagged: Boolean(phishing.is_phishing),
      });
    }
  }

  // Form validation
  const formValidation = sr.form_validation as Record<string, unknown> | undefined;
  if (formValidation) {
    const criticalCount = Number(formValidation.critical_count || 0);
    if (criticalCount > 0) {
      formIssues.push(`${criticalCount} critical form vulnerability(s)`);
    }
  }

  // Fallback header extraction
  if (headers.length === 0) {
    const knownHeaders = [
      "Strict-Transport-Security",
      "X-Content-Type-Options",
      "Content-Security-Policy",
      "X-Frame-Options",
      "Referrer-Policy",
      "Permissions-Policy",
    ];
    if (sr.headers && typeof sr.headers === "object") {
      const h = sr.headers as Record<string, string | boolean>;
      for (const name of knownHeaders) {
        const key = name.toLowerCase().replace(/-/g, "_");
        headers.push({
          name,
          present: !!h[key] || !!h[name],
          value: typeof h[key] === "string" ? (h[key] as string) : undefined,
        });
      }
    }
    // Fallback: iterate
    if (headers.length === 0) {
      Object.entries(sr).forEach(([key, value]) => {
        if (!["headers", "phishing", "forms", "security_headers", "form_validation"].includes(key)) {
          headers.push({
            name: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
            present: value !== null && value !== false,
            value: typeof value === "string" ? value : undefined,
          });
        }
      });
    }
  }

  return { headers, phishingChecks, formIssues };
}

export function SecurityMatrix({ securityResults, className }: SecurityMatrixProps) {
  const { headers, phishingChecks, formIssues } = parseSecurityResults(securityResults || {});
  const presentCount = headers.filter((h) => h.present).length;
  const totalChecks = headers.length + phishingChecks.length + (formIssues.length > 0 ? 1 : 0);
  const passCount = presentCount + phishingChecks.filter((p) => !p.flagged).length + (formIssues.length === 0 ? 1 : 0);

  return (
    <PanelChrome
      title="Security Posture"
      elevation={2}
      className={className}
      titleActions={
        <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
          {passCount}/{totalChecks} CHECKS PASSED
        </span>
      }
    >
      {/* HTTP Security Headers Grid */}
      {headers.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Lock className="w-3.5 h-3.5 text-[var(--v-text-tertiary)]" />
            <h3 className="text-[10px] uppercase tracking-[0.15em] font-semibold text-[var(--v-text-secondary)]">
              HTTP Headers ({presentCount}/{headers.length})
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
            {headers.map((h) => (
              <div
                key={h.name}
                className={cn(
                  "flex items-center justify-between px-3 py-2 rounded",
                  "border transition-colors",
                  h.present
                    ? "border-emerald-500/10 bg-emerald-500/[0.03]"
                    : "border-red-500/10 bg-red-500/[0.03]"
                )}
              >
                <div className="flex items-center gap-2 min-w-0">
                  {h.present ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="w-3 h-3 text-red-400 shrink-0" />
                  )}
                  <span className="text-[12px] font-mono text-[var(--v-text)] truncate">
                    {h.name}
                  </span>
                </div>
                {!h.present && (
                  <span className="text-[9px] font-mono font-bold text-red-400 ml-2 shrink-0">MISSING</span>
                )}
                {h.present && h.value && (
                  <span className="text-[9px] font-mono text-[var(--v-text-tertiary)] truncate max-w-[120px] ml-2">
                    {h.value}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Phishing */}
      {phishingChecks.length > 0 && (
        <div className="mb-4 pt-3 border-t border-[rgba(255,255,255,0.04)]">
          <div className="flex items-center gap-2 mb-3">
            <Globe className="w-3.5 h-3.5 text-[var(--v-text-tertiary)]" />
            <h3 className="text-[10px] uppercase tracking-[0.15em] font-semibold text-[var(--v-text-secondary)]">
              Phishing Database
            </h3>
          </div>
          <div className="space-y-1">
            {phishingChecks.map((check) => (
              <div
                key={check.source}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded border",
                  check.flagged
                    ? "border-red-500/10 bg-red-500/[0.03]"
                    : "border-emerald-500/10 bg-emerald-500/[0.03]"
                )}
              >
                {check.flagged ? (
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                ) : (
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                )}
                <span className="text-[12px] text-[var(--v-text)]">
                  {check.flagged ? "Flagged in" : "Clear from"} {check.source}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Form Issues */}
      {formIssues.length > 0 && (
        <div className="pt-3 border-t border-[rgba(255,255,255,0.04)]">
          <div className="flex items-center gap-2 mb-3">
            <FileWarning className="w-3.5 h-3.5 text-amber-400" />
            <h3 className="text-[10px] uppercase tracking-[0.15em] font-semibold text-amber-400">
              Form Security
            </h3>
          </div>
          {formIssues.map((issue, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 rounded border border-amber-500/10 bg-amber-500/[0.03]">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span className="text-[12px] text-[var(--v-text-secondary)]">{issue}</span>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {headers.length === 0 && phishingChecks.length === 0 && formIssues.length === 0 && (
        <p className="text-[12px] text-[var(--v-text-tertiary)] text-center py-6">
          Security data not available
        </p>
      )}
    </PanelChrome>
  );
}

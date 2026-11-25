"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { SecurityResultItem, TechniqueMatch, CVSSMeta } from "@/lib/types";

/* Replaces the always-similar CVSS radar: every security check that ran,
   in plain English, with its evidence and the fix. Arrives ~30 s in. */

const CHECKS: Record<string, [string, string]> = {
  security_headers: ["Security headers", "browser protections against clickjacking and script injection"],
  csp: ["Content Security Policy", "limits which scripts the page may run"],
  cookies: ["Cookie safety", "Secure / HttpOnly / SameSite flags on cookies"],
  prompt_injection: ["Hidden AI instructions", "text that tries to manipulate AI agents reading the page"],
  social_engineering: ["Scam & pressure language", "phishing phrases, fake urgency, impersonation"],
  gdpr: ["Privacy basics (GDPR)", "privacy policy, consent before tracking"],
  pci_dss: ["Payment-page safety (PCI DSS)", "card forms served securely"],
  darknet_analysis: ["Dark-web exposure", ".onion links, marketplace and leak references"],
};

type Finding = { evidence?: string; description?: string; title?: string; severity?: string; recommendation?: string };

export function SecurityChecksPanel({
  results, mitre, cvssScore, cvssMeta, status,
}: {
  results: SecurityResultItem[];
  mitre?: TechniqueMatch[];
  cvssScore?: number | null;
  cvssMeta?: CVSSMeta | null;
  status?: string;
}) {
  const modules = (results || []).filter(
    (r) => r.result && typeof r.result === "object" && "findings" in r.result
  );
  if (!modules.length) {
    return <GhostPanel message={status === "complete" ? "NO SECURITY CHECKS RAN" : "SECURITY CHECKS RUN AFTER SCOUT · STEP 2 OF 5"} />;
  }
  const withIssues = modules.filter((m) => ((m.result.findings as Finding[]) || []).length > 0);
  const passed = modules.length - withIssues.length;

  return (
    <div className="w-full h-full overflow-y-auto p-3 font-mono text-[11px] text-[var(--t-text)]">
      {mitre && mitre.length > 0 && (
        <div className="mb-2 border border-[var(--t-red)] bg-[var(--t-red)]/10 p-2">
          <div className="text-[var(--t-red)] font-bold">Known attacker techniques matched (MITRE ATT&CK)</div>
          {mitre.slice(0, 4).map((t, i) => (
            <div key={i} className="text-[10px]">
              {t.technique_id} · {t.technique_name}
            </div>
          ))}
        </div>
      )}

      <div className="mb-2">
        <span className="font-bold">{passed} of {modules.length} checks passed</span>
        {typeof cvssScore === "number" && cvssScore > 0 && cvssMeta?.vector && (
          <span className="text-[10px] text-[var(--t-dim)]">
            {" "}· industry severity (CVSS 3.1) {cvssScore.toFixed(1)}{" "}
            <a href={cvssMeta.calculatorUrl} target="_blank" rel="noopener noreferrer" className="underline text-[var(--t-amber)]">
              verify
            </a>
          </span>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        {[...withIssues, ...modules.filter((m) => !withIssues.includes(m))].map((m) => {
          const [label, what] = CHECKS[m.module] || [m.module.replace(/_/g, " "), ""];
          const findings = (m.result.findings as Finding[]) || [];
          const ok = findings.length === 0;
          return (
            <div key={m.module} className="border-l-2 pl-2" style={{ borderColor: ok ? "var(--t-green)" : "var(--t-amber)" }}>
              <div className="flex justify-between gap-2">
                <span>
                  <span className={ok ? "text-[var(--t-green)]" : "text-[var(--t-amber)]"}>{ok ? "✓" : "!"}</span>{" "}
                  {label}
                </span>
                <span className="text-[10px] text-[var(--t-dim)] whitespace-nowrap">
                  {ok ? "passed" : `${findings.length} issue${findings.length > 1 ? "s" : ""}`}
                </span>
              </div>
              {ok ? (
                what && <div className="text-[10px] text-[var(--t-dim)]">{what}</div>
              ) : (
                findings.slice(0, 3).map((f, i) => (
                  <div key={i} className="text-[10px] leading-snug">
                    <span className="text-[var(--t-text)] opacity-90">{f.evidence || f.description || f.title}</span>
                    {f.recommendation && <span className="text-[var(--t-dim)]"> → {f.recommendation}</span>}
                  </div>
                ))
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

"use client";

/* ========================================
   FindingsPanel — Report Findings Section
   Filterable dark pattern / finding list
   using FindingRow components.
   ======================================== */

import { cn } from "@/lib/utils";
import { PanelChrome } from "@/components/layout/PanelChrome";
import { FindingRow } from "@/components/audit/FindingRow";
import type { SeverityLevel } from "@/config/agents";
import type { Finding } from "@/lib/types";
import { useState, useMemo } from "react";

/** Convert snake_case to Title Case */
function formatCategory(raw: string | undefined): string {
  if (!raw) return "";
  return raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Derive a meaningful finding title, falling back to category when pattern_type is a pass reference. */
function formatFindingTitle(f: Finding): string {
  const pt = f.pattern_type || "";
  if (/^pass_?\d+$/i.test(pt) || !pt || pt === "unknown") {
    const cat = f.category || "";
    if (cat && !/^pass_?\d+$/i.test(cat) && cat !== "unknown") {
      return formatCategory(cat);
    }
    const desc = f.plain_english || f.description || "";
    if (desc) {
      const firstSentence = desc.split(/[.!?\n]/)[0].trim();
      return firstSentence.length > 80 ? firstSentence.slice(0, 77) + "..." : firstSentence || "Finding";
    }
    return "Finding";
  }
  return formatCategory(pt);
}

/** Strip markdown bold/italic/heading markers */
function stripMarkdown(text: string | undefined): string {
  if (!text) return "";
  return text
    .replace(/#{1,6}\s*/g, "")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/__(.+?)__/g, "$1")
    .replace(/_(.+?)_/g, "$1")
    .replace(/`(.+?)`/g, "$1")
    .replace(/\n{2,}/g, " ")
    .trim();
}

interface FindingsPanelProps {
  findings: Finding[];
  mode?: "simple" | "expert";
  className?: string;
}

export function FindingsPanel({ findings: rawFindings, mode = "expert", className }: FindingsPanelProps) {
  const findings = rawFindings ?? [];
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  // Categories with counts
  const categories = useMemo(() => {
    const map: Record<string, number> = {};
    for (const f of findings) {
      const cat = f.category || "unknown";
      map[cat] = (map[cat] || 0) + 1;
    }
    return Object.entries(map)
      .sort(([, a], [, b]) => b - a)
      .map(([id, count]) => ({ id, count }));
  }, [findings]);

  const filtered = activeCategory
    ? findings.filter((f) => (f.category || "unknown") === activeCategory)
    : findings;

  // Severity ordering
  const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, pass: 4 };
  const sorted = [...filtered].sort(
    (a, b) => (severityOrder[a.severity] ?? 5) - (severityOrder[b.severity] ?? 5)
  );

  const criticalCount = findings.filter((f) => f.severity === "critical" || f.severity === "high").length;

  return (
    <PanelChrome
      title="Findings"
      count={findings.length}
      elevation={2}
      className={className}
      titleActions={
        criticalCount > 0 ? (
          <span className="text-[9px] font-mono text-red-400">
            {criticalCount} CRITICAL/HIGH
          </span>
        ) : undefined
      }
    >
      {/* Category filters */}
      {categories.length > 1 && (
        <div className="flex flex-wrap gap-1 mb-4">
          <button
            onClick={() => setActiveCategory(null)}
            className={cn(
              "px-2.5 py-1 rounded text-[10px] font-mono border transition-colors",
              !activeCategory
                ? "border-[var(--agent-border,rgba(255,255,255,0.2))] text-[var(--agent-text,var(--v-text))] bg-[var(--agent-tint,rgba(255,255,255,0.05))]"
                : "border-[rgba(255,255,255,0.06)] text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
            )}
          >
            ALL ({findings.length})
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() =>
                setActiveCategory(cat.id === activeCategory ? null : cat.id)
              }
              className={cn(
                "px-2.5 py-1 rounded text-[10px] font-mono border transition-colors",
                activeCategory === cat.id
                  ? "border-[var(--agent-border,rgba(255,255,255,0.2))] text-[var(--agent-text,var(--v-text))] bg-[var(--agent-tint,rgba(255,255,255,0.05))]"
                  : "border-[rgba(255,255,255,0.06)] text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
              )}
            >
              {cat.id.replace(/_/g, " ").toUpperCase()} ({cat.count})
            </button>
          ))}
        </div>
      )}

      {/* Findings list */}
      <div className="space-y-1">
        {sorted.length === 0 ? (
          <p className="text-[12px] text-[var(--v-text-tertiary)] text-center py-6">
            No findings in this category
          </p>
        ) : (
          sorted.map((finding, i) => {
            const title = formatFindingTitle(finding);
            const desc = stripMarkdown(
              mode === "simple" && finding.plain_english
                ? finding.plain_english
                : finding.description
            );

            return (
              <FindingRow
                key={finding.id || i}
                severity={finding.severity as SeverityLevel}
                title={title}
                description={desc}
                agent={formatCategory(finding.category)}
                checkType={formatCategory(finding.pattern_type)}
                index={i}
              />
            );
          })
        )}
      </div>
    </PanelChrome>
  );
}

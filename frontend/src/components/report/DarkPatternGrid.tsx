"use client";

import { SeverityBadge } from "@/components/data-display/SeverityBadge";
import { DARK_PATTERN_CATEGORIES } from "@/lib/education";
import type { Finding } from "@/lib/types";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

interface DarkPatternGridProps {
  findings: Finding[];
  mode: "simple" | "expert";
}

export function DarkPatternGrid({ findings, mode }: DarkPatternGridProps) {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  // Group findings by category
  const grouped: Record<string, Finding[]> = {};
  for (const f of findings) {
    const cat = f.category || "unknown";
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(f);
  }

  const categories = DARK_PATTERN_CATEGORIES.map((cat) => ({
    ...cat,
    count: grouped[cat.id]?.length || 0,
    findings: grouped[cat.id] || [],
  }));

  const selected = activeCategory
    ? categories.find((c) => c.id === activeCategory)
    : null;
  const displayFindings = selected ? selected.findings : findings;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="glass-card rounded-2xl p-8 mb-6"
    >
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold mb-6">
        Dark Patterns Found ({findings.length})
      </h2>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setActiveCategory(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
            !activeCategory
              ? "border-cyan-500/40 text-cyan-400 bg-cyan-500/10"
              : "border-white/10 text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
          }`}
        >
          All ({findings.length})
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id === activeCategory ? null : cat.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              activeCategory === cat.id
                ? "border-cyan-500/40 text-cyan-400 bg-cyan-500/10"
                : "border-white/10 text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
            }`}
          >
            {cat.icon} {cat.name} ({cat.count})
          </button>
        ))}
      </div>

      {/* Findings */}
      <div className="space-y-3">
        <AnimatePresence mode="wait">
          {displayFindings.length === 0 ? (
            <p className="text-sm text-[var(--v-text-tertiary)] text-center py-6">
              No dark patterns detected in this category.
            </p>
          ) : (
            displayFindings.map((finding, i) => (
              <FindingDetailCard key={finding.id || i} finding={finding} mode={mode} delay={i * 0.05} />
            ))
          )}
        </AnimatePresence>
      </div>
    </motion.section>
  );
}

function FindingDetailCard({
  finding,
  mode,
  delay,
}: {
  finding: Finding;
  mode: "simple" | "expert";
  delay: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const rawPatternType =
    finding.pattern_type || ((finding as unknown as { sub_type?: string }).sub_type ?? "unknown_pattern");
  const patternTitle = rawPatternType
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
  const categoryLabel = (finding.category || "unknown").replace(/_/g, " ");
  const descriptionText =
    (mode === "simple" && finding.plain_english
      ? finding.plain_english
      : finding.description) || "No details available.";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="glass-card rounded-xl p-4 cursor-pointer hover:border-white/20 transition-colors"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-[var(--v-text)] mb-1">
            {patternTitle}
          </h4>
          <p className="text-xs text-[var(--v-text-secondary)]">
            {descriptionText}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <SeverityBadge severity={finding.severity} />
          <span className="text-[10px] text-[var(--v-text-tertiary)] font-mono">
            {Math.round(finding.confidence * 100)}%
          </span>
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden mt-3 pt-3 border-t border-white/5"
          >
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-[var(--v-text-tertiary)]">Category:</span>{" "}
                <span className="text-[var(--v-text-secondary)]">
                  {categoryLabel}
                </span>
              </div>
              <div>
                <span className="text-[var(--v-text-tertiary)]">Confidence:</span>{" "}
                <span className="text-[var(--v-text-secondary)]">
                  {Math.round(finding.confidence * 100)}%
                </span>
              </div>
            </div>
            {mode === "expert" && finding.plain_english && (
              <div className="mt-2 bg-white/5 rounded-lg p-2 text-xs text-[var(--v-text-secondary)]">
                <span className="font-medium text-[var(--v-text-tertiary)]">Plain English: </span>
                {finding.plain_english}
              </div>
            )}
            {mode === "simple" && finding.description !== finding.plain_english && (
              <div className="mt-2 bg-white/5 rounded-lg p-2 text-xs text-[var(--v-text-secondary)] font-mono">
                <span className="font-medium text-[var(--v-text-tertiary)]">Technical: </span>
                {finding.description}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

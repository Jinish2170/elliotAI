"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Screenshot, Finding } from "@/lib/types";
import { SeverityBadge } from "@/components/data-display/SeverityBadge";
import { StatCounter } from "@/components/data-display/StatCounter";
import type { AuditStats } from "@/lib/types";

interface EvidencePanelProps {
  screenshots: Screenshot[];
  findings: Finding[];
  stats: AuditStats;
}

export function EvidencePanel({ screenshots, findings, stats }: EvidencePanelProps) {
  const [activeTab, setActiveTab] = useState<"screenshots" | "findings" | "stats">("stats");

  const tabs = [
    { id: "stats" as const, label: "📊 Stats", count: null },
    { id: "screenshots" as const, label: "📸 Captures", count: screenshots.length },
    { id: "findings" as const, label: "🔍 Findings", count: findings.length },
  ];

  return (
    <div className="flex flex-col h-full">
      <h3 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold px-1 mb-3">
        Evidence Panel
      </h3>

      {/* Tabs */}
      <div className="flex rounded-lg bg-white/5 p-0.5 mb-3">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 text-[10px] py-1.5 rounded-md transition-colors relative ${
              activeTab === tab.id
                ? "bg-[var(--v-surface)] text-[var(--v-text)]"
                : "text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
            }`}
          >
            {tab.label}
            {tab.count !== null && tab.count > 0 && (
              <span className="ml-1 text-cyan-400">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin" style={{ maxHeight: "calc(100vh - 260px)" }}>
        <AnimatePresence mode="wait">
          {activeTab === "stats" && (
            <motion.div
              key="stats"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-2 gap-3"
            >
              <div className="glass-card rounded-lg p-3">
                <StatCounter value={stats.pages_scanned} label="Pages" />
              </div>
              <div className="glass-card rounded-lg p-3">
                <StatCounter value={stats.screenshots} label="Screenshots" />
              </div>
              <div className="glass-card rounded-lg p-3">
                <StatCounter value={stats.findings} label="Findings" />
              </div>
              <div className="glass-card rounded-lg p-3">
                <StatCounter value={stats.ai_calls} label="AI Calls" />
              </div>
              <div className="glass-card rounded-lg p-3">
                <StatCounter value={stats.security_checks} label="Sec Checks" />
              </div>
              <div className="glass-card rounded-lg p-3">
                <StatCounter
                  value={stats.elapsed_seconds}
                  label="Elapsed"
                  suffix="s"
                />
              </div>
            </motion.div>
          )}

          {activeTab === "screenshots" && (
            <motion.div
              key="screenshots"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-2"
            >
              {screenshots.length === 0 ? (
                <p className="text-xs text-[var(--v-text-tertiary)] text-center py-8">
                  No screenshots yet
                </p>
              ) : (
                <ScreenshotGallery screenshots={screenshots} />
              )}
            </motion.div>
          )}

          {activeTab === "findings" && (
            <motion.div
              key="findings"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-2"
            >
              {findings.length === 0 ? (
                <p className="text-xs text-[var(--v-text-tertiary)] text-center py-8">
                  No findings yet
                </p>
              ) : (
                findings.map((f, i) => <FindingRow key={f.id || i} finding={f} />)
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

/* ── Screenshot Gallery ── */

function ScreenshotGallery({ screenshots }: { screenshots: Screenshot[] }) {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  return (
    <>
      <div className="grid grid-cols-2 gap-2">
        {screenshots.map((ss, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.9, rotate: Math.random() * 4 - 2 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            transition={{ duration: 0.4, delay: i * 0.05 }}
            className="cursor-pointer rounded-lg overflow-hidden border border-white/10 hover:border-cyan-500/30 transition-colors"
            onClick={() => setSelectedIdx(i)}
          >
            {ss.data ? (
              <img
                src={`data:image/jpeg;base64,${ss.data}`}
                alt={ss.label}
                className="w-full h-20 object-cover"
              />
            ) : (
              <div className="w-full h-20 bg-white/5 flex items-center justify-center text-xs text-[var(--v-text-tertiary)]">
                📸 {ss.label}
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Lightbox */}
      <AnimatePresence>
        {selectedIdx !== null && screenshots[selectedIdx]?.data && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            onClick={() => setSelectedIdx(null)}
          >
            <motion.img
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              src={`data:image/jpeg;base64,${screenshots[selectedIdx].data}`}
              alt={screenshots[selectedIdx].label}
              className="max-w-[90vw] max-h-[85vh] rounded-lg border border-white/10"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

/* ── Finding Row ── */

function FindingRow({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="glass-card rounded-lg p-3 cursor-pointer hover:border-white/20 transition-colors"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-[var(--v-text)] truncate flex-1">
          {finding.pattern_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
        </span>
        <SeverityBadge severity={finding.severity} />
      </div>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <p className="text-[11px] text-[var(--v-text-secondary)] mt-2">{finding.description}</p>
            {finding.plain_english && (
              <p className="text-[10px] text-[var(--v-text-tertiary)] mt-1 italic">{finding.plain_english}</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

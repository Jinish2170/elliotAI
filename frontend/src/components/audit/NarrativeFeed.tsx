"use client";

import { SeverityBadge } from "@/components/data-display/SeverityBadge";
import { GreenFlagCelebration } from "@/components/audit/GreenFlagCelebration";
import { DARK_PATTERN_FACTS, PHASE_TERMS } from "@/lib/education";
import type { Finding, GreenFlag, LogEntry, Phase, Screenshot } from "@/lib/types";
import { PHASE_META } from "@/lib/types";
import { getPersonalityMessage } from "@/config/agent_personalities";
import { AnimatePresence, motion } from "framer-motion";
import confetti from "canvas-confetti";
import { useEffect, useMemo, useRef, useState } from "react";

interface NarrativeFeedProps {
  currentPhase: Phase | null;
  findings: Finding[];
  screenshots: Screenshot[];
  logs: LogEntry[];
  status: string;
  trustScore?: number;
  greenFlags?: GreenFlag[];
}

type FeedEntry =
  | { kind: "phase"; phase: Phase; timestamp: number }
  | { kind: "finding"; finding: Finding; timestamp: number }
  | { kind: "screenshot"; screenshot: Screenshot; timestamp: number }
  | { kind: "didyouknow"; factIdx: number; timestamp: number }
  | { kind: "complete"; score: number; timestamp: number }
  | { kind: "personality"; agent: Phase; context: "working" | "complete" | "success" | "error"; params?: Record<string, unknown>; timestamp: number };

export function NarrativeFeed({
  currentPhase,
  findings,
  screenshots,
  logs,
  status,
  trustScore,
  greenFlags = [],
}: NarrativeFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null);
  const [entries, setEntries] = useState<FeedEntry[]>([]);
  const prevPhaseRef = useRef<Phase | null>(null);
  const prevFindingsCount = useRef(0);
  const prevScreensCount = useRef(0);
  const prevLogsCount = useRef(0);
  const shownFacts = useRef(new Set<number>());

  // Build feed entries reactively
  useEffect(() => {
    const newEntries: FeedEntry[] = [];

    // Phase transition
    if (currentPhase && currentPhase !== prevPhaseRef.current && currentPhase !== "init") {
      // Insert a "did you know" card between phases
      if (prevPhaseRef.current && prevPhaseRef.current !== "init") {
        const availableFacts = DARK_PATTERN_FACTS.map((_, i) => i).filter(
          (i) => !shownFacts.current.has(i)
        );
        if (availableFacts.length > 0) {
          const idx = availableFacts[Math.floor(Math.random() * availableFacts.length)];
          shownFacts.current.add(idx);
          newEntries.push({ kind: "didyouknow", factIdx: idx, timestamp: Date.now() - 1 });
        }
      }
      newEntries.push({ kind: "phase", phase: currentPhase, timestamp: Date.now() });
      prevPhaseRef.current = currentPhase;
    }

    // New findings
    if (findings.length > prevFindingsCount.current) {
      for (let i = prevFindingsCount.current; i < findings.length; i++) {
        newEntries.push({ kind: "finding", finding: findings[i], timestamp: Date.now() + i });
      }
      prevFindingsCount.current = findings.length;
    }

    // New screenshots
    if (screenshots.length > prevScreensCount.current) {
      for (let i = prevScreensCount.current; i < screenshots.length; i++) {
        newEntries.push({ kind: "screenshot", screenshot: screenshots[i], timestamp: Date.now() + i + 100 });
      }
      prevScreensCount.current = screenshots.length;
    }

    // Personality events from logs
    if (logs.length > prevLogsCount.current) {
      for (let i = prevLogsCount.current; i < logs.length; i++) {
        const log = logs[i];
        // Check if this is a personality log entry
        if (log.context && log.agent) {
          const phase = log.agent as Phase;
          if (phase && phase !== "init") {
            // Throttle personality events: only show every 30 seconds or on complete
            const shouldShow = log.context === "complete" ||
              (log.context === "working" && Math.random() < 0.3); // Only 30% of working messages
            if (shouldShow) {
              newEntries.push({
                kind: "personality",
                agent: phase,
                context: log.context,
                params: log.params,
                timestamp: Date.now() + i,
              });
            }
          }
        }
      }
      prevLogsCount.current = logs.length;
    }

    if (newEntries.length > 0) {
      setEntries((prev) => [...prev, ...newEntries]);
    }
  }, [currentPhase, findings, screenshots, logs]);

  // Completion entry
  useEffect(() => {
    if (status === "complete" && trustScore !== undefined) {
      setEntries((prev) => [
        ...prev,
        { kind: "complete", score: trustScore, timestamp: Date.now() },
      ]);
    }
  }, [status, trustScore]);

  // Auto-scroll
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [entries]);

  // Phase terms for contextual education
  const phaseTerms = useMemo(() => {
    if (!currentPhase || currentPhase === "init") return [];
    return PHASE_TERMS[currentPhase] || [];
  }, [currentPhase]);

  return (
    <div className="flex flex-col h-full">
      <h3 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold px-1 mb-3">
        Live Narrative
      </h3>

      <div
        ref={feedRef}
        className="flex-1 overflow-y-auto space-y-3 pr-1 scrollbar-thin"
        style={{ maxHeight: "calc(100vh - 220px)" }}
      >
        <AnimatePresence initial={false}>
          {entries.map((entry, idx) => (
            <motion.div
              key={`${entry.kind}-${entry.timestamp}-${idx}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
              {entry.kind === "phase" && <PhaseCard phase={entry.phase} />}
              {entry.kind === "finding" && <FindingAlertCard finding={entry.finding} />}
              {entry.kind === "screenshot" && <ScreenshotCard screenshot={entry.screenshot} />}
              {entry.kind === "didyouknow" && <DidYouKnowCard factIdx={entry.factIdx} />}
              {entry.kind === "personality" && <PersonalityCard agent={entry.agent} context={entry.context} params={entry.params} />}
              {entry.kind === "complete" && <CompletionCard score={entry.score} greenFlags={greenFlags} />}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Idle state */}
        {entries.length === 0 && status !== "complete" && (
          <div className="text-center py-12 text-[var(--v-text-tertiary)]">
            <div className="text-3xl mb-3 animate-pulse">🔍</div>
            <p className="text-sm">Waiting for audit to begin...</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Sub-cards ── */

function PhaseCard({ phase }: { phase: Phase }) {
  const meta = PHASE_META[phase];
  const PIPELINE_PHASES: Phase[] = ["scout", "security", "vision", "graph", "judge"];
  const phaseNum = PIPELINE_PHASES.indexOf(phase) + 1;

  return (
    <div className="glass-card rounded-xl p-4 border-l-2 border-cyan-500/50">
      <div className="text-[10px] uppercase tracking-wider text-[var(--v-text-tertiary)] mb-2">
        Phase {phaseNum} of 5
      </div>
      <div className="flex items-center gap-3">
        <span className="text-2xl">{meta.icon}</span>
        <div>
          <h4 className="text-sm font-semibold text-[var(--v-text)]">{meta.label}</h4>
          <p className="text-xs text-[var(--v-text-secondary)]">{meta.description}</p>
        </div>
      </div>
    </div>
  );
}

function FindingAlertCard({ finding }: { finding: Finding }) {
  const borderColor =
    finding.severity === "critical"
      ? "border-red-500/50"
      : finding.severity === "high"
      ? "border-orange-500/50"
      : "border-amber-500/50";

  return (
    <div className={`glass-card rounded-xl p-4 border-l-2 ${borderColor}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] uppercase tracking-wider text-amber-400 font-semibold">
          ⚠️ Dark Pattern Detected
        </span>
        <SeverityBadge severity={finding.severity} />
      </div>
      <h4 className="text-sm font-semibold text-[var(--v-text)] mb-1">
        {finding.pattern_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
      </h4>
      <p className="text-xs text-[var(--v-text-secondary)] mb-2">{finding.description}</p>
      {finding.plain_english && (
        <div className="bg-white/5 rounded-lg p-2 text-xs text-[var(--v-text-secondary)]">
          <span className="text-[var(--v-text-tertiary)] font-medium">What this means: </span>
          {finding.plain_english}
        </div>
      )}
      <div className="mt-2 text-[10px] text-[var(--v-text-tertiary)]">
        Confidence: {Math.round(finding.confidence * 100)}% · Category:{" "}
        {finding.category.replace(/_/g, " ")}
      </div>
    </div>
  );
}

function ScreenshotCard({ screenshot }: { screenshot: Screenshot }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="glass-card rounded-xl p-4">
      <div className="text-[10px] uppercase tracking-wider text-[var(--v-text-tertiary)] mb-2">
        📸 Screenshot Captured
      </div>
      {screenshot.data ? (
        <>
          <div
            className="cursor-pointer rounded-lg overflow-hidden border border-white/10 hover:border-cyan-500/30 transition-colors"
            onClick={() => setExpanded(!expanded)}
          >
            <img
              src={`data:image/jpeg;base64,${screenshot.data}`}
              alt={screenshot.label}
              className={`w-full object-cover transition-all duration-300 ${
                expanded ? "max-h-[500px]" : "max-h-[120px]"
              }`}
            />
          </div>
          <p className="text-xs text-[var(--v-text-tertiary)] mt-2">{screenshot.label}</p>
        </>
      ) : (
        <p className="text-xs text-[var(--v-text-secondary)]">{screenshot.label}</p>
      )}
    </div>
  );
}

function DidYouKnowCard({ factIdx }: { factIdx: number }) {
  const fact = DARK_PATTERN_FACTS[factIdx];
  if (!fact) return null;

  return (
    <div className="glass-card rounded-xl p-4 border-l-2 border-purple-500/50">
      <div className="text-[10px] uppercase tracking-wider text-purple-400 font-semibold mb-2">
        ✨ Did You Know?
      </div>
      <h4 className="text-sm font-semibold text-[var(--v-text)] mb-1">{fact.title}</h4>
      <p className="text-xs text-[var(--v-text-secondary)] leading-relaxed">{fact.text}</p>
      <p className="text-[10px] text-[var(--v-text-tertiary)] mt-2 italic">Source: {fact.source}</p>
    </div>
  );
}

function CompletionCard({ score, greenFlags = [] }: { score: number; greenFlags?: GreenFlag[] }) {
  const color =
    score >= 90
      ? "text-emerald-400 border-emerald-500/50"
      : score >= 70
      ? "text-cyan-400 border-cyan-500/50"
      : score >= 40
      ? "text-amber-400 border-amber-500/50"
      : "text-red-400 border-red-500/50";

  // Trigger confetti for high trust scores
  useEffect(() => {
    if (score >= 80) {
      setTimeout(() => {
        confetti({
          particleCount: 80,
          spread: 60,
          origin: { y: 0.7 },
          colors: ["#10B981", "#06B6D4", "#8B5CF6"],
          disableForReducedMotion: true,
        });
      }, 300);
    }
  }, [score]);

  return (
    <>
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className={`glass-card rounded-xl p-6 text-center border-l-2 ${color.split(" ")[1]}`}
      >
        <motion.div
          initial={{ rotate: -10 }}
          animate={{ rotate: 0 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="text-4xl mb-2"
        >
          {score >= 80 ? "🎉" : score >= 70 ? "✅" : score >= 40 ? "⚠️" : "🚨"}
        </motion.div>
        <h3 className="text-lg font-bold text-[var(--v-text)] mb-1">
          {score >= 80 ? "Audit Complete - Excellent Trust!" : score >= 70 ? "Audit Complete" : score >= 40 ? "Audit Complete - Caution Advised" : "Audit Complete - Low Trust Detected"}
        </h3>
        <motion.div
          className={`text-4xl font-bold font-mono mb-1 ${color.split(" ")[0]}`}
          animate={score >= 80 ? {
            scale: [1, 1.05, 1],
            textShadow: ["0 0 0px rgba(16, 185, 129, 0)", "0 0 20px rgba(16, 185, 129, 0.5)", "0 0 0px rgba(16, 185, 129, 0)"]
          } : {}}
          transition={{ duration: 2, repeat: score >= 80 ? Infinity : 0 }}
        >
          {score}
        </motion.div>
        <p className="text-xs text-[var(--v-text-tertiary)]">/100 Trust Score</p>
        {score >= 70 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-2 text-xs text-[var(--v-text-secondary)]"
          >
            {score >= 90 ? "✨ Outstanding - This site demonstrates excellent trustworthiness!" : "✓ This site shows positive trust indicators"}
          </motion.div>
        )}
        {score >= 80 && greenFlags.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="mt-2 flex items-center justify-center gap-1 text-[10px] text-emerald-400/90"
          >
            <span>🏅</span>
            <span>{greenFlags.length} positive indicators detected</span>
          </motion.div>
        )}
      </motion.div>

      {/* Green Flag Celebration Banner - shown after CompletionCard */}
      {score >= 80 && greenFlags.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="mt-3"
        >
          <GreenFlagCelebration
            trustScore={score}
            greenFlags={greenFlags}
            onDismiss={() => {/* Can add dismiss handler if needed */}}
          />
        </motion.div>
      )}
    </>
  );
}

/* ── Personality Card Component ── */

function PersonalityCard({ agent, context, params }: { agent: Phase; context: "working" | "complete" | "success" | "error"; params?: Record<string, unknown> }) {
  const meta = PHASE_META[agent];
  if (!meta || agent === "init") return null;

  // Cast params to the expected type for getPersonalityMessage
  const message = getPersonalityMessage(agent, context, params as Record<string, number | string> | undefined);

  return (
    <div className="glass-card rounded-xl p-3 border-l-2 border-cyan-500/30">
      <div className="flex items-center gap-3">
        <span className="text-xl animate-pulse">{meta.icon}</span>
        <div className="flex-1">
          <h4 className="text-xs font-semibold text-[var(--v-text)]">{meta.label}</h4>
          <p className="text-[10px] text-[var(--v-text-secondary)] mt-0.5">{message}</p>
        </div>
      </div>
    </div>
  );
}

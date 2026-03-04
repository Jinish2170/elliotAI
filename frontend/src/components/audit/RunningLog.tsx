"use client";

import type { LogEntry } from "@/lib/types";
import { formatRelativeTime } from "@/lib/types";
import { useAuditStore } from "@/lib/store";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, ChevronUp, Terminal } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

interface RunningLogProps {
  maxEntries?: number; // default 100
  showPersonality?: boolean; // default true
}

export function RunningLog({ maxEntries = 100, showPersonality = true }: RunningLogProps) {
  const [expanded, setExpanded] = useState(false);
  const { logs } = useAuditStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Windowing logic - keep only the last maxEntries
  const windowedLogs = useMemo(() => {
    if (logs.length <= maxEntries) return logs;
    return logs.slice(-maxEntries);
  }, [logs, maxEntries]);

  // Auto-scroll to bottom on new logs
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [windowedLogs, autoScroll]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 40);
  };

  const toggleExpanded = () => {
    setExpanded((prev) => !prev);
  };

  // Color coding for log levels
  const getLevelColor = (level: string) => {
    switch (level) {
      case "error":
        return "text-red-400";
      case "warn":
        return "text-amber-400";
      case "info":
        return "text-cyan-400";
      default:
        return "text-gray-400";
    }
  };

  // Get agent emoji from agent name
  const getAgentEmoji = (agent: string) => {
    const agentLower = agent.toLowerCase();
    if (agentLower.includes("scout") || agentLower.includes("recon")) return "🔎";
    if (agentLower.includes("security")) return "🛡️";
    if (agentLower.includes("vision")) return "👁️";
    if (agentLower.includes("graph") || agentLower.includes("network")) return "🌐";
    if (agentLower.includes("judge")) return "⚖️";
    if (agentLower.includes("init")) return "⚙️";
    return "🤖";
  };

  // Check if entry should be emphasized (success/complete context)
  const isEmphasized = (entry: LogEntry) => {
    return entry.context === "complete" || entry.context === "success";
  };

  const visibleLogs = expanded ? windowedLogs : windowedLogs.slice(-3);

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={toggleExpanded}
        className="w-full flex items-center justify-between px-4 py-2 hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] uppercase tracking-wider text-[var(--v-text-tertiary)] font-semibold">
            Running Log
          </span>
          <span className="text-[10px] text-[var(--v-text-tertiary)]">({windowedLogs.length} entries)</span>
          {logs.length > maxEntries && (
            <span className="text-[9px] text-amber-400/80" title={`Oldest ${logs.length - maxEntries} entries evicted`}>
              (windowed)
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-[var(--v-text-tertiary)]" />
        ) : (
          <ChevronUp className="w-3.5 h-3.5 text-[var(--v-text-tertiary)]" />
        )}
      </button>

      {/* Log content */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className={`font-mono text-[11px] overflow-y-auto transition-all duration-300 ${
          expanded ? "max-h-[300px] px-4 pb-3" : "max-h-[96px] px-4 pb-2"
        }`}
      >
        <AnimatePresence initial={false}>
          {visibleLogs.map((log, i) => (
            <motion.div
              key={`${log.timestamp}-${i}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className={`flex gap-2 py-1 leading-snug ${isEmphasized(log) ? "bg-emerald-500/10 -mx-2 px-2 rounded" : ""}`}
            >
              <span className="text-[var(--v-text-tertiary)] flex-shrink-0 tabular-nums">
                [{formatRelativeTime(log.timestamp)}]
              </span>
              <span className={`flex-shrink-0 ${getLevelColor(log.level)}`}>
                {showPersonality ? `${getAgentEmoji(log.agent)} ${log.agent.split(":")[0].trim()}` : log.agent} →
              </span>
              <span
                className={`text-[var(--v-text-secondary)] break-all ${
                  isEmphasized(log) ? "font-semibold text-emerald-400" : ""
                }`}
              >
                {log.message}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>

        {windowedLogs.length === 0 && (
          <div className="text-[var(--v-text-tertiary)] py-2">Waiting for log entries...</div>
        )}
      </div>
    </div>
  );
}

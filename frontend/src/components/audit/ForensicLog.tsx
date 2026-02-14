"use client";

import type { LogEntry } from "@/lib/types";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, ChevronUp, Terminal } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface ForensicLogProps {
  logs: LogEntry[];
}

const LEVEL_COLORS: Record<string, string> = {
  info: "text-cyan-400",
  warn: "text-amber-400",
  error: "text-red-400",
};

export function ForensicLog({ logs }: ForensicLogProps) {
  const [expanded, setExpanded] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 40);
  };

  const visibleLogs = expanded ? logs : logs.slice(-3);

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2 hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] uppercase tracking-wider text-[var(--v-text-tertiary)] font-semibold">
            Forensic Log
          </span>
          <span className="text-[10px] text-[var(--v-text-tertiary)]">({logs.length} entries)</span>
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
          expanded ? "max-h-[250px] px-4 pb-3" : "max-h-[72px] px-4 pb-2"
        }`}
      >
        <AnimatePresence initial={false}>
          {visibleLogs.map((log, i) => (
            <motion.div
              key={`${log.timestamp}-${i}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className="flex gap-2 py-0.5 leading-snug"
            >
              <span className="text-[var(--v-text-tertiary)] flex-shrink-0 tabular-nums">
                [{log.timestamp}]
              </span>
              <span className={`flex-shrink-0 ${LEVEL_COLORS[log.level] || "text-gray-400"}`}>
                {log.agent} →
              </span>
              <span className="text-[var(--v-text-secondary)] break-all">{log.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>

        {logs.length === 0 && (
          <div className="text-[var(--v-text-tertiary)] py-2">Waiting for log entries...</div>
        )}
      </div>
    </div>
  );
}

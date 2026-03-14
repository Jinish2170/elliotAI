"use client";
import React, { useRef, useEffect } from "react";
import { GhostPanel } from "./TerminalPanel";
import type { LogEntry } from "@/lib/types";

export function SysLogStream({ logs }: { logs: LogEntry[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new logs
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs.length]);

  if (!logs || logs.length === 0) return <GhostPanel message="AWAITING TELEMETRY" />;

  // Optimization: render only latest 200 logs to prevent DOM overload
  const renderLogs = logs.slice(-200);

  return (
    <div ref={containerRef} className="w-full h-full overflow-y-auto p-2 scroll-smooth bg-[var(--t-base)]">
      <div className="flex flex-col">
        {renderLogs.map((log, i) => {
          const levelColor = 
            log.level === "error" ? "text-[var(--t-red)] glow-text-red" : 
            log.level === "warn" ? "text-[var(--t-amber)] glow-text-amber" : 
            "text-[var(--t-text)] opacity-80";
            
          return (
            <div key={i} className={`grid grid-cols-[60px_80px_1fr] gap-3 mb-1 text-[11px] font-mono leading-tight hover:bg-[#111] p-1 rounded-sm transition-colors ${levelColor}`}>
              <span className="text-[var(--t-dim)] opacity-50 whitespace-nowrap select-none">
                {log.timestamp}
              </span>
              <span className="text-[var(--t-dim)] uppercase font-semibold tracking-wider select-none truncate">
                [{log.agent || "SYS"}]
              </span>
              <span className="break-words">
                {log.message}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

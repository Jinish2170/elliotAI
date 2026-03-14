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
            <div key={i} className={`flex gap-2 mb-1 text-[10px] font-mono leading-relaxed ${levelColor} break-words`}>
              <span className="text-[var(--t-dim)] flex-shrink-0 w-16 select-none leading-relaxed">
                {log.timestamp}
              </span>
              <span className="text-[var(--t-dim)] flex-shrink-0 w-16 truncate select-none leading-relaxed uppercase">
                [{log.agent?.substring(0, 7)}]
              </span>
              <span className="flex-1 min-w-0 pr-2 leading-relaxed">
                {log.message}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

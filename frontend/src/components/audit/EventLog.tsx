"use client";

/* ========================================
   EventLog — Bloomberg Terminal Bar
   Full-width structured log: timestamps, agent tags,
   filter, search, copy. Replaces ForensicLog.
   ======================================== */

import { cn } from "@/lib/utils";
import { AGENT_CONFIGS, type AgentId } from "@/config/agents";
import type { LogEntry } from "@/lib/types";
import {
  ChevronDown,
  ClipboardCopy,
  Maximize2,
  Minimize2,
  Search,
  X,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

interface EventLogProps {
  logs: LogEntry[];
  currentAgent?: AgentId | null;
  className?: string;
}

const AGENT_FILTERS = ["all", "scout", "security", "vision", "graph", "judge", "errors"] as const;
type AgentFilter = (typeof AGENT_FILTERS)[number];

const LEVEL_ICONS: Record<string, string> = {
  info: "",
  warn: "▌WRN",
  error: "▌ERR",
};

export function EventLog({ logs, currentAgent, className }: EventLogProps) {
  const [filter, setFilter] = useState<AgentFilter>("all");
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filterOpen, setFilterOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Filter + search
  const filtered = useMemo(() => {
    let result = logs;

    if (filter === "errors") {
      result = result.filter((l) => l.level === "error" || l.level === "warn");
    } else if (filter !== "all") {
      result = result.filter(
        (l) => l.agent?.toLowerCase().includes(filter)
      );
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (l) =>
          l.message?.toLowerCase().includes(q) ||
          l.agent?.toLowerCase().includes(q)
      );
    }

    return result;
  }, [logs, filter, search]);

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [filtered.length, autoScroll]);

  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 40);
  }, []);

  const copyAll = useCallback(() => {
    const text = filtered
      .map((l) => `[${l.timestamp}] [${l.agent || "SYS"}] ${l.message}`)
      .join("\n");
    navigator.clipboard.writeText(text);
  }, [filtered]);

  const agentColor = useCallback((agent: string | undefined): string => {
    if (!agent) return "rgba(255,255,255,0.4)";
    const key = agent.toLowerCase().replace(/_agent$/, "") as AgentId;
    return AGENT_CONFIGS[key]?.color.primary || "rgba(255,255,255,0.4)";
  }, []);

  const promptAgent = currentAgent
    ? currentAgent
    : "sys";

  const promptColor = currentAgent
    ? AGENT_CONFIGS[currentAgent]?.color.primary || "#06B6D4"
    : "#06B6D4";

  return (
    <div
      className={cn(
        "terminal-bg rounded-lg overflow-hidden border border-[rgba(255,255,255,0.06)]",
        expanded ? "fixed inset-4 z-50" : "",
        className
      )}
    >
      {/* Title bar */}
      <div className="flex items-center justify-between h-[var(--panel-title-height)] px-3 bg-[var(--panel-title-bg)] border-b border-[rgba(255,255,255,0.04)]">
        <div className="flex items-center gap-2">
          <div
            className="w-[2px] h-3 rounded-full"
            style={{ background: promptColor }}
          />
          <span className="text-panel-title">EVENT LOG</span>
          <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
            [{filtered.length}]
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Filter dropdown */}
          <div className="relative">
            <button
              onClick={() => setFilterOpen((p) => !p)}
              className="flex items-center gap-1 px-2 py-0.5 text-[9px] font-mono text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] rounded bg-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.08)] transition-colors"
            >
              Filter: {filter.toUpperCase()}
              <ChevronDown className="w-2.5 h-2.5" />
            </button>
            {filterOpen && (
              <div className="absolute top-full right-0 mt-1 z-50 elev-4 rounded-md py-1 min-w-[120px]">
                {AGENT_FILTERS.map((f) => (
                  <button
                    key={f}
                    onClick={() => {
                      setFilter(f);
                      setFilterOpen(false);
                    }}
                    className={cn(
                      "w-full text-left px-3 py-1 text-[10px] font-mono transition-colors",
                      filter === f
                        ? "text-[var(--v-text)] bg-[rgba(255,255,255,0.08)]"
                        : "text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] hover:bg-[rgba(255,255,255,0.04)]"
                    )}
                  >
                    {f.toUpperCase()}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Search */}
          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-[rgba(255,255,255,0.04)]">
            <Search className="w-2.5 h-2.5 text-[var(--v-text-tertiary)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="bg-transparent text-[10px] font-mono text-[var(--v-text-secondary)] placeholder:text-[var(--v-text-tertiary)] w-20 focus:w-32 transition-all outline-none"
            />
            {search && (
              <button onClick={() => setSearch("")} className="text-[var(--v-text-tertiary)]">
                <X className="w-2.5 h-2.5" />
              </button>
            )}
          </div>

          {/* Copy */}
          <button
            onClick={copyAll}
            className="p-1 text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] transition-colors"
            title="Copy all"
          >
            <ClipboardCopy className="w-3 h-3" />
          </button>

          {/* Expand */}
          <button
            onClick={() => setExpanded((p) => !p)}
            className="p-1 text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] transition-colors"
            title={expanded ? "Minimize" : "Expand"}
          >
            {expanded ? (
              <Minimize2 className="w-3 h-3" />
            ) : (
              <Maximize2 className="w-3 h-3" />
            )}
          </button>
        </div>
      </div>

      {/* Log entries */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className={cn(
          "overflow-y-auto overflow-x-hidden px-3 py-1",
          expanded ? "h-[calc(100%-28px)]" : "h-[180px]"
        )}
      >
        {filtered.length === 0 && (
          <div className="text-log text-[var(--v-text-tertiary)] py-4">
            {logs.length === 0 ? "Waiting for log entries..." : "No matching entries"}
          </div>
        )}

        {filtered.map((log, i) => (
          <LogLine
            key={`${log.timestamp}-${i}`}
            log={log}
            agentColor={agentColor(log.agent)}
            isNew={i === filtered.length - 1}
          />
        ))}

        {/* Agent prompt */}
        <div className="flex items-center gap-1 py-0.5 text-log">
          <span style={{ color: promptColor }}>{promptAgent}&gt;</span>
          <span className="inline-block w-1.5 h-3.5 animate-pulse" style={{ background: promptColor }} />
        </div>
      </div>

      {/* "New entries" badge when not auto-scrolling */}
      {!autoScroll && filtered.length > 0 && (
        <button
          onClick={() => {
            setAutoScroll(true);
            if (scrollRef.current) {
              scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
            }
          }}
          className="absolute bottom-2 right-4 px-2 py-0.5 text-[9px] font-mono rounded bg-[var(--agent-primary)] text-black"
        >
          ↓ New entries
        </button>
      )}
    </div>
  );
}

/* ── Single log line ── */

function LogLine({
  log,
  agentColor,
  isNew,
}: {
  log: LogEntry;
  agentColor: string;
  isNew: boolean;
}) {
  const levelIndicator = LEVEL_ICONS[log.level] || "";
  const levelColor =
    log.level === "error"
      ? "#EF4444"
      : log.level === "warn"
      ? "#F59E0B"
      : undefined;

  return (
    <div
      className={cn(
        "flex gap-2 py-[1px] text-log leading-[1.6]",
        isNew && "bg-[rgba(255,255,255,0.02)]"
      )}
    >
      {/* Timestamp */}
      <span className="text-[var(--v-text-tertiary)] shrink-0 tabular-nums w-[90px]">
        [{log.timestamp}]
      </span>

      {/* Agent tag */}
      <span
        className="shrink-0 w-[12ch] text-right"
        style={{ color: agentColor }}
      >
        [{(log.agent || "SYS").toUpperCase()}]
      </span>

      {/* Level indicator */}
      {levelIndicator && (
        <span style={{ color: levelColor }} className="shrink-0">
          {levelIndicator}
        </span>
      )}

      {/* Message */}
      <span className="text-[var(--v-text-secondary)] break-words min-w-0 flex-1">
        {log.message}
      </span>
    </div>
  );
}

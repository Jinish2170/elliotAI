"use client";

/* ========================================
   TerminalBlock — Terminal-style Output
   For WHOIS, DNS, cert chain data.
   Monospace, copyable, expandable.
   ======================================== */

import { cn } from "@/lib/utils";
import { ClipboardCopy, Maximize2, Terminal } from "lucide-react";
import { useCallback, useState } from "react";

interface TerminalBlockProps {
  /** Title shown in the header (e.g., "WHOIS LOOKUP") */
  title: string;
  /** Subtitle (e.g., domain name) */
  subtitle?: string;
  /** Command prompt line (e.g., "$ whois example.com") */
  command?: string;
  /** Terminal content lines */
  content: string | string[];
  /** Key fields to highlight in agent color */
  highlights?: string[];
  /** Accent color override */
  accentColor?: string;
  className?: string;
}

export function TerminalBlock({
  title,
  subtitle,
  command,
  content,
  highlights = [],
  accentColor,
  className,
}: TerminalBlockProps) {
  const [expanded, setExpanded] = useState(false);

  const lines = Array.isArray(content) ? content : content.split("\n");
  const visibleLines = expanded ? lines : lines.slice(0, 15);
  const hasMore = lines.length > 15;

  const copyAll = useCallback(() => {
    const text = lines.join("\n");
    navigator.clipboard.writeText(text);
  }, [lines]);

  const highlightLine = useCallback(
    (line: string): boolean => {
      return highlights.some(
        (h) => line.toLowerCase().includes(h.toLowerCase())
      );
    },
    [highlights]
  );

  return (
    <div
      className={cn(
        "terminal-bg rounded-md overflow-hidden border border-[rgba(255,255,255,0.06)]",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-[var(--panel-title-bg)] border-b border-[rgba(255,255,255,0.04)]">
        <div className="flex items-center gap-2">
          <Terminal className="w-3 h-3 text-[var(--v-text-tertiary)]" />
          <span className="text-panel-title">{title}</span>
          {subtitle && (
            <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
              — {subtitle}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={copyAll}
            className="p-1 text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] transition-colors"
            title="Copy"
          >
            <ClipboardCopy className="w-3 h-3" />
          </button>
          {hasMore && (
            <button
              onClick={() => setExpanded((p) => !p)}
              className="p-1 text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] transition-colors"
              title={expanded ? "Collapse" : "Expand"}
            >
              <Maximize2 className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-3 py-2 overflow-x-auto">
        {command && (
          <div className="text-log mb-1.5">
            <span className="text-[var(--v-safe)]">$</span>{" "}
            <span className="text-[var(--v-text-secondary)]">{command}</span>
          </div>
        )}
        {visibleLines.map((line, i) => (
          <div
            key={i}
            className="text-log"
            style={{
              color: highlightLine(line)
                ? accentColor || "var(--agent-primary)"
                : undefined,
            }}
          >
            {line || "\u00A0"}
          </div>
        ))}
        {hasMore && !expanded && (
          <button
            onClick={() => setExpanded(true)}
            className="text-[10px] font-mono text-[var(--agent-primary,#06B6D4)] hover:underline mt-1"
          >
            ... {lines.length - 15} more lines [EXPAND]
          </button>
        )}
      </div>
    </div>
  );
}

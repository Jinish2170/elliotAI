"use client";

/* ========================================
   JsonTreeViewer — DevTools-style JSON Tree
   Collapsible, syntax-highlighted, searchable.
   Copy per-node. Array counts. Object keys bold.
   ======================================== */

import { cn } from "@/lib/utils";
import { ChevronDown, ChevronRight, ClipboardCopy } from "lucide-react";
import { useCallback, useState } from "react";

interface JsonTreeViewerProps {
  data: unknown;
  /** Root label — shown as the top-level key */
  label?: string;
  /** Maximum initial depth to auto-expand */
  defaultExpandDepth?: number;
  className?: string;
}

export function JsonTreeViewer({
  data,
  label = "root",
  defaultExpandDepth = 1,
  className,
}: JsonTreeViewerProps) {
  return (
    <div
      className={cn(
        "terminal-bg rounded-md border border-[rgba(255,255,255,0.06)] p-3 overflow-auto font-mono text-[11px] leading-[1.7]",
        className
      )}
    >
      <JsonNode
        keyName={label}
        value={data}
        depth={0}
        defaultExpandDepth={defaultExpandDepth}
      />
    </div>
  );
}

/* ── Recursive JSON node ── */

function JsonNode({
  keyName,
  value,
  depth,
  defaultExpandDepth,
  isLast = true,
}: {
  keyName?: string;
  value: unknown;
  depth: number;
  defaultExpandDepth: number;
  isLast?: boolean;
}) {
  const [expanded, setExpanded] = useState(depth < defaultExpandDepth);

  const isObject = value !== null && typeof value === "object" && !Array.isArray(value);
  const isArray = Array.isArray(value);
  const isExpandable = isObject || isArray;

  const copyNode = useCallback(() => {
    navigator.clipboard.writeText(JSON.stringify(value, null, 2));
  }, [value]);

  if (!isExpandable) {
    return (
      <div className="flex items-center gap-1 group pl-4">
        {keyName !== undefined && (
          <>
            <span className="text-[#9CDCFE] font-semibold">{keyName}</span>
            <span className="text-[rgba(255,255,255,0.3)]">:</span>
          </>
        )}
        <ValueRenderer value={value} />
        {!isLast && <span className="text-[rgba(255,255,255,0.3)]">,</span>}
      </div>
    );
  }

  const entries = isArray ? value : Object.entries(value as Record<string, unknown>);
  const count = isArray ? value.length : Object.keys(value as Record<string, unknown>).length;
  const bracket = isArray ? ["[", "]"] : ["{", "}"];

  return (
    <div>
      <div className="flex items-center gap-1 group">
        <button
          onClick={() => setExpanded((p) => !p)}
          className="p-0 text-[rgba(255,255,255,0.4)] hover:text-[rgba(255,255,255,0.8)] transition-colors"
          aria-label={expanded ? "Collapse" : "Expand"}
        >
          {expanded ? (
            <ChevronDown className="w-3 h-3" />
          ) : (
            <ChevronRight className="w-3 h-3" />
          )}
        </button>

        {keyName !== undefined && (
          <>
            <span className="text-[#9CDCFE] font-semibold">{keyName}</span>
            <span className="text-[rgba(255,255,255,0.3)]">:</span>
          </>
        )}

        <span className="text-[rgba(255,255,255,0.5)]">
          {bracket[0]}
        </span>

        {!expanded && (
          <>
            <span className="text-[rgba(255,255,255,0.3)] italic">
              {count} {isArray ? (count === 1 ? "item" : "items") : (count === 1 ? "key" : "keys")}
            </span>
            <span className="text-[rgba(255,255,255,0.5)]">{bracket[1]}</span>
            {!isLast && <span className="text-[rgba(255,255,255,0.3)]">,</span>}
          </>
        )}

        {/* Copy button */}
        <button
          onClick={copyNode}
          className="opacity-0 group-hover:opacity-60 hover:!opacity-100 p-0.5 transition-opacity"
          title="Copy"
        >
          <ClipboardCopy className="w-2.5 h-2.5 text-[var(--v-text-tertiary)]" />
        </button>
      </div>

      {expanded && (
        <div className="ml-4 border-l border-[rgba(255,255,255,0.06)]">
          {isArray
            ? (value as unknown[]).map((item, i) => (
                <JsonNode
                  key={i}
                  keyName={String(i)}
                  value={item}
                  depth={depth + 1}
                  defaultExpandDepth={defaultExpandDepth}
                  isLast={i === (value as unknown[]).length - 1}
                />
              ))
            : Object.entries(value as Record<string, unknown>).map(([k, v], i, arr) => (
                <JsonNode
                  key={k}
                  keyName={k}
                  value={v}
                  depth={depth + 1}
                  defaultExpandDepth={defaultExpandDepth}
                  isLast={i === arr.length - 1}
                />
              ))}
          <div className="flex items-center">
            <span className="text-[rgba(255,255,255,0.5)] pl-0">{bracket[1]}</span>
            {!isLast && <span className="text-[rgba(255,255,255,0.3)]">,</span>}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Value renderer with syntax highlighting ── */

function ValueRenderer({ value }: { value: unknown }) {
  if (value === null) {
    return <span className="text-[#EF4444] italic">null</span>;
  }
  if (value === undefined) {
    return <span className="text-[#6B7280] italic">undefined</span>;
  }
  if (typeof value === "boolean") {
    return (
      <span className="text-[#F59E0B]">{value ? "true" : "false"}</span>
    );
  }
  if (typeof value === "number") {
    return <span className="text-[#06B6D4]">{value}</span>;
  }
  if (typeof value === "string") {
    // Truncate long strings
    const display = value.length > 120 ? value.slice(0, 120) + "…" : value;
    return (
      <span className="text-[#10B981]">
        &quot;{display}&quot;
      </span>
    );
  }
  return <span className="text-[var(--v-text-secondary)]">{String(value)}</span>;
}

"use client";

/* ========================================
   DataTable — Sortable, Filterable Table
   For structured data: DNS records, HTTP headers, 
   cookies, security checks.
   ======================================== */

import { cn } from "@/lib/utils";
import { ArrowDown, ArrowUp, ArrowUpDown, ClipboardCopy, Download } from "lucide-react";
import { useCallback, useMemo, useState } from "react";

interface Column<T> {
  key: string;
  label: string;
  /** Width class (Tailwind) */
  width?: string;
  /** Custom render function */
  render?: (value: unknown, row: T) => React.ReactNode;
  /** Sortable (default true) */
  sortable?: boolean;
}

interface DataTableProps<T extends Record<string, unknown>> {
  columns: Column<T>[];
  data: T[];
  /** Table title */
  title?: string;
  /** Show copy/export buttons */
  showControls?: boolean;
  /** Row click handler */
  onRowClick?: (row: T, index: number) => void;
  /** Empty state message */
  emptyMessage?: string;
  className?: string;
}

type SortDir = "asc" | "desc" | null;

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  title,
  showControls = true,
  onRowClick,
  emptyMessage = "No data",
  className,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);

  const handleSort = useCallback(
    (key: string) => {
      if (sortKey === key) {
        setSortDir((d) => (d === "asc" ? "desc" : d === "desc" ? null : "asc"));
        if (sortDir === "desc") setSortKey(null);
      } else {
        setSortKey(key);
        setSortDir("asc");
      }
    },
    [sortKey, sortDir]
  );

  const sorted = useMemo(() => {
    if (!sortKey || !sortDir) return data;
    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      const cmp =
        typeof aVal === "number" && typeof bVal === "number"
          ? aVal - bVal
          : String(aVal).localeCompare(String(bVal));
      return sortDir === "desc" ? -cmp : cmp;
    });
  }, [data, sortKey, sortDir]);

  const copyAsJson = useCallback(() => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
  }, [data]);

  return (
    <div className={cn("rounded-md overflow-hidden border border-[rgba(255,255,255,0.06)]", className)}>
      {/* Header */}
      {(title || showControls) && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-[var(--panel-title-bg)] border-b border-[rgba(255,255,255,0.04)]">
          {title && (
            <div className="flex items-center gap-2">
              <span className="text-panel-title">{title}</span>
              <span className="text-[9px] font-mono text-[var(--v-text-tertiary)]">
                [{data.length}]
              </span>
            </div>
          )}
          {showControls && (
            <div className="flex items-center gap-1">
              <button
                onClick={copyAsJson}
                className="p-1 text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] transition-colors"
                title="Copy as JSON"
              >
                <ClipboardCopy className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[rgba(255,255,255,0.06)]">
              {columns.map((col) => {
                const isSorted = sortKey === col.key;
                const sortable = col.sortable !== false;
                return (
                  <th
                    key={col.key}
                    className={cn(
                      "text-left px-3 py-1.5 text-data-label",
                      sortable && "cursor-pointer select-none hover:text-[var(--v-text-secondary)]",
                      col.width
                    )}
                    onClick={() => sortable && handleSort(col.key)}
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      {sortable && (
                        <span className="shrink-0">
                          {isSorted && sortDir === "asc" ? (
                            <ArrowUp className="w-2.5 h-2.5" />
                          ) : isSorted && sortDir === "desc" ? (
                            <ArrowDown className="w-2.5 h-2.5" />
                          ) : (
                            <ArrowUpDown className="w-2.5 h-2.5 opacity-30" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="text-center text-[11px] font-mono text-[var(--v-text-tertiary)] py-6"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              sorted.map((row, i) => (
                <tr
                  key={i}
                  className={cn(
                    "border-b border-[rgba(255,255,255,0.03)] transition-colors",
                    "hover:bg-[rgba(255,255,255,0.02)]",
                    onRowClick && "cursor-pointer"
                  )}
                  onClick={() => onRowClick?.(row, i)}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        "px-3 py-1.5 text-[11px] font-mono text-[var(--v-text-secondary)]",
                        col.width
                      )}
                    >
                      {col.render
                        ? col.render(row[col.key], row)
                        : String(row[col.key] ?? "—")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      {data.length > 0 && (
        <div className="px-3 py-1 text-[9px] font-mono text-[var(--v-text-tertiary)] border-t border-[rgba(255,255,255,0.04)]">
          Click column header to sort · {data.length} {data.length === 1 ? "row" : "rows"}
        </div>
      )}
    </div>
  );
}

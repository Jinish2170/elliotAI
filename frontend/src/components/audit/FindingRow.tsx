"use client";

/* ========================================
   FindingRow — Structured Finding Display
   Severity stripe + icon + title + description + expand.
   Replaces chat-like finding messages with Bloomberg-style data rows.
   ======================================== */

import { cn } from "@/lib/utils";
import { SeverityBadge, SeverityStripe } from "@/components/ui/SeverityBadge";
import type { SeverityLevel } from "@/config/agents";
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";
import { useCallback, useState } from "react";

interface FindingRowProps {
  severity: SeverityLevel;
  title: string;
  description?: string;
  /** Source agent */
  agent?: string;
  /** Check type (e.g., "http_headers") */
  checkType?: string;
  /** Affected URL or resource */
  resource?: string;
  /** Extended detail (shown on expand) */
  detail?: string;
  /** Remediation advice */
  remediation?: string;
  /** Evidence link — clicking scrolls to evidence */
  onEvidenceClick?: () => void;
  /** Index for stagger animation */
  index?: number;
  className?: string;
}

export function FindingRow({
  severity,
  title,
  description,
  agent,
  checkType,
  resource,
  detail,
  remediation,
  onEvidenceClick,
  index = 0,
  className,
}: FindingRowProps) {
  const [expanded, setExpanded] = useState(false);
  const hasExpandContent = !!(detail || remediation);

  const toggleExpand = useCallback(() => {
    if (hasExpandContent) setExpanded((prev) => !prev);
  }, [hasExpandContent]);

  const isCritical = severity === "critical";

  return (
    <div
      className={cn(
        "group relative flex gap-0 rounded-md overflow-hidden",
        "transition-all duration-150 ease-out",
        "hover:bg-[rgba(255,255,255,0.02)]",
        isCritical ? "finding-critical" : "border-l-0",
        className
      )}
      style={{
        animationDelay: `${index * 50}ms`,
      }}
      role="row"
    >
      {/* Severity stripe (non-critical — critical uses finding-critical class) */}
      {!isCritical && <SeverityStripe severity={severity} className="ml-0" />}

      {/* Content */}
      <div className="flex-1 min-w-0 px-3 py-2">
        {/* Header row: badge + title + expand toggle */}
        <div className="flex items-start gap-2">
          <SeverityBadge severity={severity} variant="minimal" size="sm" />

          <button
            type="button"
            className="flex-1 min-w-0 text-left"
            onClick={toggleExpand}
            disabled={!hasExpandContent}
            aria-expanded={hasExpandContent ? expanded : undefined}
          >
            <span className="text-[13px] text-[var(--v-text)] leading-snug line-clamp-2">
              {title}
            </span>
          </button>

          {hasExpandContent && (
            <button
              onClick={toggleExpand}
              className="shrink-0 p-0.5 text-[rgba(255,255,255,0.3)] hover:text-[rgba(255,255,255,0.6)] transition-colors"
              aria-label={expanded ? "Collapse details" : "Expand details"}
            >
              {expanded ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
            </button>
          )}
        </div>

        {/* Description */}
        {description && (
          <p className="mt-0.5 text-[12px] text-[var(--v-text-tertiary)] leading-relaxed line-clamp-2">
            {description}
          </p>
        )}

        {/* Source metadata */}
        <div className="mt-1 flex items-center gap-2 text-[10px] font-mono text-[var(--v-text-tertiary)]">
          {agent && <span>Source: {agent}</span>}
          {checkType && (
            <>
              <span className="text-[rgba(255,255,255,0.1)]">·</span>
              <span>Check: {checkType}</span>
            </>
          )}
          {resource && (
            <>
              <span className="text-[rgba(255,255,255,0.1)]">·</span>
              <span className="truncate max-w-[200px]">{resource}</span>
            </>
          )}
        </div>

        {/* Expanded detail */}
        {expanded && hasExpandContent && (
          <div className="mt-2 pt-2 border-t border-[rgba(255,255,255,0.04)] space-y-2">
            {detail && (
              <div>
                <span className="text-data-label block mb-0.5">DETAIL</span>
                <p className="text-[12px] text-[var(--v-text-secondary)] leading-relaxed">
                  {detail}
                </p>
              </div>
            )}
            {remediation && (
              <div>
                <span className="text-data-label block mb-0.5">REMEDIATION</span>
                <p className="text-[12px] text-[var(--v-text-secondary)] leading-relaxed">
                  {remediation}
                </p>
              </div>
            )}
            {onEvidenceClick && (
              <button
                onClick={onEvidenceClick}
                className="inline-flex items-center gap-1 text-[11px] font-mono text-[var(--agent-primary,#06B6D4)] hover:underline"
              >
                <ExternalLink className="w-3 h-3" />
                Evidence →
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

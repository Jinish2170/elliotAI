"use client";

/* ========================================
   MetricTicker — Bloomberg-Style Metric Strip
   Horizontal bar of live-updating monospace numbers.
   Sits below the header bar during an audit.
   Numbers animate/tick during live audit state.
   ======================================== */

import { cn } from "@/lib/utils";
import { useEffect, useRef, type ReactNode } from "react";

export interface TickerMetric {
  label: string;
  value: number | string;
  /** Optional suffix like "s" or "%" */
  suffix?: string;
  /** Show a status indicator instead of a number */
  status?: "pass" | "fail" | "pending";
}

interface MetricTickerProps {
  metrics: TickerMetric[];
  className?: string;
}

export function MetricTicker({ metrics, className }: MetricTickerProps) {
  return (
    <div
      className={cn(
        "w-full h-7 flex items-center gap-0 px-3 overflow-x-auto",
        "border-t border-b border-[rgba(255,255,255,0.04)]",
        "bg-[var(--elev-1)]",
        className
      )}
      role="status"
      aria-label="Audit metrics"
    >
      {metrics.map((metric, i) => (
        <TickerItem key={metric.label} metric={metric} isFirst={i === 0} />
      ))}

      {/* Chromatic underline glow */}
      <div
        className="absolute bottom-0 left-0 right-0 h-px"
        style={{
          background: `linear-gradient(90deg, transparent, var(--agent-primary, transparent) 50%, transparent)`,
          opacity: 0.4,
          transition: "background 400ms cubic-bezier(0.4, 0, 0.2, 1)",
        }}
        aria-hidden="true"
      />
    </div>
  );
}

function TickerItem({ metric, isFirst }: { metric: TickerMetric; isFirst: boolean }) {
  return (
    <div className={cn("flex items-center gap-0 shrink-0", !isFirst && "ml-0")}>
      {!isFirst && (
        <span className="text-[rgba(255,255,255,0.15)] mx-2 text-[10px] select-none" aria-hidden="true">·</span>
      )}
      <span className="text-data-label whitespace-nowrap">
        {metric.label}:
      </span>
      <span className="ml-1.5">
        {metric.status ? (
          <StatusIndicator status={metric.status} />
        ) : (
          <TickingNumber value={metric.value} suffix={metric.suffix} />
        )}
      </span>
    </div>
  );
}

function StatusIndicator({ status }: { status: "pass" | "fail" | "pending" }) {
  const config = {
    pass: { symbol: "✓", color: "#10B981" },
    fail: { symbol: "✗", color: "#EF4444" },
    pending: { symbol: "…", color: "rgba(255,255,255,0.3)" },
  };
  const { symbol, color } = config[status];

  return (
    <span className="text-ticker font-bold" style={{ color }}>
      {symbol}
    </span>
  );
}

/**
 * TickingNumber — animates digit transitions for live-updating metrics.
 * Uses a simple RAF-based counter for smooth number ticking.
 */
function TickingNumber({ value, suffix }: { value: number | string; suffix?: string }) {
  const spanRef = useRef<HTMLSpanElement>(null);
  const currentRef = useRef<number>(typeof value === "number" ? value : 0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (typeof value !== "number" || !spanRef.current) {
      if (spanRef.current) {
        spanRef.current.textContent = `${value}${suffix ?? ""}`;
      }
      return;
    }

    const target = value;
    const start = currentRef.current;
    const diff = target - start;

    if (diff === 0) return;

    // For small diffs (1-3), just set immediately — feels snappier
    if (Math.abs(diff) <= 3) {
      currentRef.current = target;
      if (spanRef.current) {
        spanRef.current.textContent = `${target}${suffix ?? ""}`;
      }
      return;
    }

    // Animate larger jumps over ~100ms per digit
    const duration = Math.min(Math.abs(diff) * 100, 800);
    const startTime = performance.now();

    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Linear interpolation — numbers should feel mechanical, not springy
      const current = Math.round(start + diff * progress);
      currentRef.current = current;

      if (spanRef.current) {
        spanRef.current.textContent = `${current}${suffix ?? ""}`;
      }

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    }

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [value, suffix]);

  return (
    <span
      ref={spanRef}
      className="text-ticker text-[var(--v-text)] tabular-nums"
    >
      {typeof value === "number" ? `${value}${suffix ?? ""}` : value}
    </span>
  );
}

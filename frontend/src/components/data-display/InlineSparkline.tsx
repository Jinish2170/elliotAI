"use client";

/* ========================================
   InlineSparkline — Tiny 60×16px Sparkline
   For embedding in table cells and metric displays.
   Pure SVG, no external chart library.
   ======================================== */

import { cn } from "@/lib/utils";

interface InlineSparklineProps {
  /** Data points (y-values) */
  data: number[];
  /** Width in px */
  width?: number;
  /** Height in px */
  height?: number;
  /** Line color */
  color?: string;
  /** Show area fill */
  fill?: boolean;
  /** Highlight the last point with a dot */
  showDot?: boolean;
  className?: string;
}

export function InlineSparkline({
  data,
  width = 60,
  height = 16,
  color = "var(--agent-primary, #06B6D4)",
  fill = true,
  showDot = true,
  className,
}: InlineSparklineProps) {
  if (data.length < 2) {
    return (
      <div
        className={cn("inline-block", className)}
        style={{ width, height }}
      />
    );
  }

  const padding = 2;
  const innerW = width - padding * 2;
  const innerH = height - padding * 2;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((v, i) => {
    const x = padding + (i / (data.length - 1)) * innerW;
    const y = padding + innerH - ((v - min) / range) * innerH;
    return { x, y };
  });

  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  const areaD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${height} L ${points[0].x.toFixed(1)} ${height} Z`;

  const lastPoint = points[points.length - 1];

  return (
    <svg
      width={width}
      height={height}
      className={cn("inline-block align-middle", className)}
      viewBox={`0 0 ${width} ${height}`}
    >
      {/* Area fill */}
      {fill && (
        <path
          d={areaD}
          fill={color}
          fillOpacity={0.1}
        />
      )}

      {/* Line */}
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth={1}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Last-point dot */}
      {showDot && lastPoint && (
        <circle
          cx={lastPoint.x}
          cy={lastPoint.y}
          r={1.5}
          fill={color}
        />
      )}
    </svg>
  );
}
